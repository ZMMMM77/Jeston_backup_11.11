"""ROS 2 node: particle-filter pose + IMU -> full odometry for the drift policy (real car).

Run: ros2 launch rl_drifting_input state_estimator_launch.py   (after localize_launch.py)
Copied from the drift repo's src/drift_policy/drift_policy/state_estimator_node.py.

The particle filter publishes only a pose. The drift policy needs vx, vy and the
yaw rate as well. This node fuses both with ``drift_env.estimator`` and publishes
an Odometry whose twist is measured at base_link (the rear axle), so run the
policy node with ``twist_point:=base_link``.

Subscribes  pose_topic  nav_msgs/Odometry or geometry_msgs/PoseStamped (PF, map frame)
            imu_topic   sensor_msgs/Imu
Publishes   out_topic   nav_msgs/Odometry  pose: base_link in map; twist: body frame at base_link
            /drift/est/innovation     PF pose minus prediction [m] (jumps, PF quality)
            /drift/est/pose_age_ms    time since the last PF pose stamp (latency + period)
            /drift/est/speed, /drift/est/vy, /drift/est/beta_rear_deg
            /drift/est/r_gyro, /drift/est/r_pf  yaw rate from the gyro and from PF yaw
                                                (compare them to check the gyro sign and scale)
            std_msgs/Float32 each

Defaults match the course stack:
  * f1tenth/particle_filter estimates the LASER pose (TF map -> laser) and stamps
    /pf/pose/odom with the publish time, so ``pose_offset_x`` = 0.27 m (base_link
    -> laser in f1tenth_system) and ``pose_latency_s`` moves the stamp back to the
    scan. Measure both on your car.
  * the VESC driver publishes /sensors/imu/raw at 50 Hz with the raw VESC units,
    acceleration in g and angular rate in deg/s, stamped on receipt.

Start-up: keep the car still for ``calib_seconds``. The node averages the IMU to
remove the gyro and accelerometer biases, checks the units, then starts publishing.
It stops publishing when PF poses or IMU samples stop, so the policy node's
odom timeout stops the car.
"""
import math

import numpy as np
import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32

from rl_drifting_input import drift_estimator as E

G = 9.80665


def stamp_to_s(stamp):
    return stamp.sec + stamp.nanosec * 1e-9


def s_to_stamp(t):
    sec = int(math.floor(t))
    return Time(sec=sec, nanosec=int((t - sec) * 1e9))


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class StateEstimatorNode(Node):
    def __init__(self):
        super().__init__("drift_state_estimator")
        p = self.declare_parameter
        p("pose_topic", "/pf/pose/odom")
        p("pose_type", "odometry")            # "odometry" or "pose_stamped" (e.g. /pf/viz/inferred_pose)
        p("pose_offset_x", 0.27)              # PF frame (laser) ahead of base_link [m]; 0 if PF reports base_link
        p("pose_latency_s", 0.03)             # subtracted from PF stamps (publish time -> scan time)
        p("imu_topic", "/sensors/imu/raw")
        p("use_imu", True)                    # False: PF-only fallback, too noisy for drifting
        p("imu_ax_sign", 1.0)                 # map IMU axes to car axes (x forward, y left, z up)
        p("imu_ay_sign", 1.0)
        p("imu_gz_sign", 1.0)
        p("imu_accel_scale", 9.80665)         # VESC reports g; 1.0 for an IMU in m/s^2
        p("imu_gyro_scale", math.pi / 180.0)  # VESC reports deg/s; 1.0 for an IMU in rad/s
        p("imu_offset_x", 0.0)                # IMU ahead of base_link [m]
        p("calib_seconds", 2.0)               # keep the car still this long after start
        p("out_topic", "/drift/state_odom")
        p("frame_id", "map")
        p("child_frame_id", "base_link")
        p("publish_hz", 100.0)
        p("pose_timeout_s", 0.15)
        p("imu_timeout_s", 0.1)
        p("use_header_stamp", True)           # False: use receive time (if stamps are unreliable)
        # filter tuning (see drift_env/estimator.py)
        p("pos_std", 0.02)
        p("yaw_std_deg", 1.0)
        p("acc_density", 0.05)
        p("acc_bias_walk", 0.05)
        p("gyro_density", 0.005)
        p("gyro_bias_walk", 0.002)
        p("jerk_psd", 100.0)                  # PF-only fallback
        p("gate_m", 0.3)
        p("max_rejects", 5)
        p("max_predict_s", 0.05)

        g = lambda name: self.get_parameter(name).value  # noqa: E731
        self.g = g
        self.use_imu = bool(g("use_imu"))
        self.use_stamp = bool(g("use_header_stamp"))
        common = dict(pos_std=g("pos_std"), yaw_std=math.radians(g("yaw_std_deg")), gate_m=g("gate_m"),
                      max_rejects=int(g("max_rejects")), max_predict_s=g("max_predict_s"))
        if self.use_imu:
            self.est = E.ImuPoseEstimator(acc_density=g("acc_density"), acc_bias_walk=g("acc_bias_walk"),
                                          gyro_density=g("gyro_density"), gyro_bias_walk=g("gyro_bias_walk"),
                                          imu_offset_x=g("imu_offset_x"), **common)
        else:
            self.est = E.PfOnlyEstimator(jerk_psd=g("jerk_psd"), **common)
            self.get_logger().warn("use_imu is false: PF-only velocities are too noisy for drifting")
        self.yaw_check = E.YawRateKF(math.radians(g("yaw_std_deg")))   # r from PF yaw, for comparison

        self.calib = []                       # IMU samples while still
        self.bias = np.zeros(3)               # ax, ay, gz removed from every sample
        self.calibrated = not self.use_imu
        self.t_first_imu = None
        self.last_imu_rx = None
        self.last_pose_rx = None
        self.gyro_check = []                  # (r_gyro, r_pf) pairs while turning
        self.ay_check = []                    # (ay, vx * r) pairs while turning
        self.gyro_ok = False                  # gyro agreed with PF yaw rate at least once
        self.fault = None                     # sensor setup error found while driving
        self.last_ay = 0.0
        self.last_gz = 0.0
        self.publishing = False

        self.pub = self.create_publisher(Odometry, g("out_topic"), 10)
        self.dbg = {k: self.create_publisher(Float32, f"/drift/est/{k}", 10)
                    for k in ("innovation", "pose_age_ms", "speed", "vy", "beta_rear_deg", "r_gyro", "r_pf")}
        if g("pose_type") == "pose_stamped":
            self.create_subscription(PoseStamped, g("pose_topic"), lambda m: self.on_pose(m.header, m.pose), 10)
        else:
            self.create_subscription(Odometry, g("pose_topic"), lambda m: self.on_pose(m.header, m.pose.pose), 10)
        if self.use_imu:
            self.create_subscription(Imu, g("imu_topic"), self.on_imu, qos_profile_sensor_data)
        self.create_timer(1.0 / g("publish_hz"), self.tick)
        self.get_logger().info(
            f"PF {g('pose_topic')} + " + (f"IMU {g('imu_topic')}" if self.use_imu else "no IMU")
            + f" -> {g('out_topic')}" + (f"; keep the car still for {g('calib_seconds'):.1f} s" if self.use_imu else ""))

    # ---------------------------------------------------------------- helpers
    def now_s(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def msg_time(self, header):
        t = stamp_to_s(header.stamp)
        return t if self.use_stamp and t > 0 else self.now_s()

    def f32(self, key, value):
        self.dbg[key].publish(Float32(data=float(value)))

    # --------------------------------------------------------------- callbacks
    def on_imu(self, msg):
        t = self.msg_time(msg.header)
        self.last_imu_rx = self.now_s()
        a, w = msg.linear_acceleration, msg.angular_velocity
        s = self.g("imu_accel_scale")
        raw = np.array([self.g("imu_ax_sign") * a.x * s, self.g("imu_ay_sign") * a.y * s,
                        self.g("imu_gz_sign") * w.z * self.g("imu_gyro_scale")])
        if not self.calibrated:
            self.calib.append((raw, a.z * s))
            if self.t_first_imu is None:
                self.t_first_imu = t
            if t - self.t_first_imu >= self.g("calib_seconds"):
                self.finish_calibration()
            return
        ax, ay, gz = raw - self.bias
        self.last_gz, self.last_ay = gz, ay
        self.est.update_imu(t, ax, ay, gz)

    def finish_calibration(self):
        data = np.array([c[0] for c in self.calib])
        az = np.array([c[1] for c in self.calib])
        self.bias = data.mean(axis=0)
        std = data.std(axis=0)
        norm = float(np.linalg.norm([self.bias[0], self.bias[1], az.mean()]))
        log = self.get_logger()
        log.info(f"IMU calibrated from {len(data)} samples: bias ax {self.bias[0]:+.3f} ay {self.bias[1]:+.3f} "
                 f"m/s^2, gz {self.bias[2]:+.4f} rad/s; |a| at rest {norm:.2f} (expect 9.81)")
        if abs(norm - G) > 1.5:
            hint = (" (it reports g: use imu_accel_scale:=9.80665)" if abs(norm - 1.0) < 0.2 else
                    " (it reports m/s^2: use imu_accel_scale:=1.0)" if abs(norm - G * G) < 15 else "")
            log.error(f"|a| at rest is {norm:.2f}, not 9.81: check imu_accel_scale{hint}")
        if std[2] > 0.05 or max(std[0], std[1]) > 0.5:
            log.warn(f"car moved during IMU calibration (std ax {std[0]:.2f} ay {std[1]:.2f} gz {std[2]:.3f}); "
                     "keep it still, restarting calibration")
            self.calib, self.t_first_imu = [], None
            return
        if abs(self.bias[2]) > 0.05:
            log.warn("large gyro bias: check imu_gyro_scale (deg/s?)")
        self.calibrated = True
        self.calib = []

    def on_pose(self, header, pose):
        if not self.calibrated:
            return
        t = self.msg_time(header) - self.g("pose_latency_s")
        self.last_pose_rx = self.now_s()
        yaw = yaw_from_quat(pose.orientation)
        d = self.g("pose_offset_x")
        x = pose.position.x - d * math.cos(yaw)
        y = pose.position.y - d * math.sin(yaw)
        accepted = self.est.update_pose(t, x, y, yaw)
        self.f32("innovation", self.est.gate.last_innovation)
        if not accepted:
            self.get_logger().warn(f"PF jump rejected: {self.est.gate.last_innovation:.2f} m from prediction",
                                   throttle_duration_sec=1.0)
        self.yaw_check.update(t, yaw)
        if self.use_imu and accepted:
            st = self.est.state_at(t)
            if st.speed > 1.5:             # PF yaw rate is too noisy at low speed
                self.check_gyro(self.last_gz, self.yaw_check.x[1])
                if self.gyro_ok:           # the ay check uses the gyro, so it must be right first
                    self.check_ay(self.last_ay, st.vx * self.last_gz)

    def check_ay(self, ay, centripetal):
        """In a turn the lateral acceleration is about vx * r (left turn: +y)."""
        if abs(centripetal) < 3.0:
            return
        self.ay_check.append((ay, centripetal))
        if len(self.ay_check) < 80:
            return
        a, c = np.array(self.ay_check).T
        self.ay_check = []
        agree = float(np.mean(np.sign(a) == np.sign(c)))
        if agree < 0.2:
            self.set_fault(f"IMU lateral acceleration has the wrong sign ({agree:.0%} agree with vx*r): "
                           "set imu_ay_sign:=-1.0")

    def check_gyro(self, r_gyro, r_pf):
        """Compare the gyro with the yaw rate from PF yaw while the car turns."""
        if abs(r_pf) < 1.0:
            return
        self.gyro_check.append((r_gyro, r_pf))
        if len(self.gyro_check) < 80:
            return
        g, p = np.array(self.gyro_check).T
        self.gyro_check = []
        agree = float(np.mean(np.sign(g) == np.sign(p)))
        ratio = float(np.median(np.abs(g) / np.abs(p)))
        if agree < 0.2:
            self.set_fault(f"gyro yaw rate has the opposite sign to PF yaw ({agree:.0%} agree): "
                           "set imu_gz_sign:=-1.0")
        elif agree < 0.8 or not 0.6 < ratio < 1.6:
            self.get_logger().warn(f"gyro and PF yaw rate disagree: same sign {agree:.0%}, "
                                   f"|gyro|/|PF| {ratio:.2f} (check imu_gyro_scale, PF yaw)")
        else:
            self.gyro_ok = True

    def set_fault(self, why):
        """A sensor setup error: stop publishing for good, so the policy stops the car."""
        if self.fault is None:
            self.fault = why
            self.get_logger().error(f"{why}. Not publishing until restarted.")

    def tick(self):
        if not self.calibrated or not self.est.initialized or self.fault is not None:
            return
        now = self.now_s()
        stale = []
        if now - self.last_pose_rx > self.g("pose_timeout_s"):
            stale.append(f"PF pose ({1000 * (now - self.last_pose_rx):.0f} ms)")
        if self.use_imu and (self.last_imu_rx is None or now - self.last_imu_rx > self.g("imu_timeout_s")):
            stale.append(f"IMU ({1000 * (now - (self.last_imu_rx or now)):.0f} ms)")
        if stale:
            if self.publishing:
                self.get_logger().warn(f"no {' or '.join(stale)}: not publishing")
            self.publishing = False
            return
        if not self.publishing:
            self.get_logger().info("publishing state")
        self.publishing = True

        st = self.est.state_at(now)
        m = Odometry()
        m.header.stamp = s_to_stamp(st.t)
        m.header.frame_id = self.g("frame_id")
        m.child_frame_id = self.g("child_frame_id")
        m.pose.pose.position.x, m.pose.pose.position.y = st.x, st.y
        m.pose.pose.orientation.z = math.sin(st.yaw / 2)
        m.pose.pose.orientation.w = math.cos(st.yaw / 2)
        m.twist.twist.linear.x, m.twist.twist.linear.y = st.vx, st.vy
        m.twist.twist.angular.z = st.r
        cov = [0.0] * 36
        cov[0] = cov[7] = st.vel_std ** 2
        m.twist.covariance = cov
        self.pub.publish(m)

        self.f32("pose_age_ms", 1000.0 * st.age)
        self.f32("speed", st.speed)
        self.f32("vy", st.vy)
        self.f32("beta_rear_deg", math.degrees(st.beta_rear))
        self.f32("r_gyro", self.last_gz)
        if self.yaw_check.t is not None:
            self.f32("r_pf", self.yaw_check.x[1])


def main():
    rclpy.init()
    node = StateEstimatorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception:
        if rclpy.ok():      # a real error; on Ctrl-C the context is already gone
            raise
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.try_shutdown()


if __name__ == "__main__":
    main()
