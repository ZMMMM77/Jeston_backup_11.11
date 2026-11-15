#!/usr/bin/env python3
"""D435i IMU -> base_link frame for the EKF.

Copied from Roboracer-Final-Project sensors_bringup/src/imu_covariance_override.py, with the
accelerometer rotated as well (the original only rotated the gyro) and its bias removed.

Camera optical frame (x right, y down, z forward) -> car body (x forward, y left, z up):
    body.x = optical.z,  body.y = -optical.x,  body.z = -optical.y
Keep the car still for the first ~1 s: gyro bias and the resting ax, ay (mounting tilt) are
averaged and subtracted. Publishes /imu/data at the camera IMU rate (200 Hz).
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Imu


class D435iImu(Node):
    def __init__(self):
        super().__init__('d435i_imu')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        self.sub = self.create_subscription(Imu, '/camera/camera/imu', self.cb, qos)
        self.pub = self.create_publisher(Imu, '/imu/data', qos)
        self.gyro_var = 0.001
        self.accel_var = 0.05

        self.calibrating = True
        self.cal_samples = []
        self.cal_count = 200
        self.bias = [0.0] * 6        # gx, gy, gz, ax, ay (body frame), az unused
        self.get_logger().info('Calibrating IMU bias - keep car still...')

    def cb(self, msg):
        # rotate optical -> body first, then everything below works in body axes
        g = msg.angular_velocity
        a = msg.linear_acceleration
        gx, gy, gz = g.z, -g.x, -g.y
        ax, ay, az = a.z, -a.x, -a.y

        if self.calibrating:
            self.cal_samples.append((gx, gy, gz, ax, ay))
            if len(self.cal_samples) >= self.cal_count:
                n = float(self.cal_count)
                self.bias = [sum(s[i] for s in self.cal_samples) / n for i in range(5)]
                self.calibrating = False
                self.get_logger().info(
                    'IMU bias: gyro=(%.4f %.4f %.4f) accel xy=(%.3f %.3f)' % tuple(self.bias))
            # Publish during calibration with current (possibly zero) bias so ICP
            # receives IMU data from frame 1 and never gets a null motion guess.

        msg.angular_velocity.x = gx - self.bias[0]
        msg.angular_velocity.y = gy - self.bias[1]
        msg.angular_velocity.z = gz - self.bias[2]
        msg.linear_acceleration.x = ax - self.bias[3]
        msg.linear_acceleration.y = ay - self.bias[4]
        msg.linear_acceleration.z = az

        msg.orientation.x = 0.0
        msg.orientation.y = 0.0
        msg.orientation.z = 0.0
        msg.orientation.w = 1.0
        msg.orientation_covariance[0] = -1.0

        msg.angular_velocity_covariance[0] = self.gyro_var
        msg.angular_velocity_covariance[4] = self.gyro_var
        msg.angular_velocity_covariance[8] = self.gyro_var
        msg.linear_acceleration_covariance[0] = self.accel_var
        msg.linear_acceleration_covariance[4] = self.accel_var
        msg.linear_acceleration_covariance[8] = self.accel_var

        msg.header.frame_id = 'base_link'
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(D435iImu())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
