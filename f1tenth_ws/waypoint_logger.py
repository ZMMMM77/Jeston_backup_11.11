#!/usr/bin/env python3
"""
Record waypoints from the particle filter pose while you drive the car by hand,
and write a CSV the pure_pursuit node can load directly.

Keep make_speed_csv.py in the SAME folder as this file (it does the math).

Run on the Jetson (bringup + particle_filter running, initial pose set):
    python3 waypoint_logger.py --out ~/f1tenth_ws/src/<pkg>/waypoints/drift_1_circle.csv --v-max 1.5

Drive ONE clean lap with LB held, slowly and smoothly. Recording stops when you
get back to the start (or press Ctrl+C at any time).

Writes:
  drift_1_circle.csv      node format: # x_m,y_m,vx_mps,s_m,psi_rad,kappa_radpm,ax_mps2
                      (node reads x,y = cols 0,1, speed = col 2, curvature = col 5)
  drift_1_circle_raw.csv  raw recording: # x_m,y_m,yaw_rad,speed_mps
The file name (without .csv) is the node's `track` parameter.
"""
import argparse, math, os, sys

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import make_speed_csv as msc
except ImportError:
    msc = None


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def raw_path(out):
    return (out[:-4] if out.endswith(".csv") else out) + "_raw.csv"


class WaypointLogger(Node):
    def __init__(self, a):
        super().__init__("waypoint_logger")
        self.a = a
        self.pts = []            # (x, y, yaw, speed)
        self.speed = 0.0
        self.travelled = 0.0
        self.done = False
        self.create_subscription(Odometry, a.pose_topic, self.on_pose, 10)
        self.create_subscription(Odometry, a.odom_topic, self.on_odom, 10)
        self.get_logger().info(
            f"Recording {a.pose_topic} every {a.spacing:.2f} m  "
            f"(auto-stop after {a.min_lap:.0f} m when back within {a.close_radius:.1f} m of start; Ctrl+C to stop)")

    def on_odom(self, msg):
        self.speed = abs(msg.twist.twist.linear.x)

    def on_pose(self, msg):
        if self.done:
            return
        p = msg.pose.pose
        x, y, yaw = p.position.x, p.position.y, yaw_from_quat(p.orientation)
        if self.pts:
            lx, ly = self.pts[-1][:2]
            step = math.hypot(x - lx, y - ly)
            if step > self.a.max_jump:   # particle filter jumped: ignore this pose
                self.get_logger().warn(f"Ignoring pose jump of {step:.2f} m")
                return
            if step < self.a.spacing:
                return
            self.travelled += step
        self.pts.append((x, y, yaw, self.speed))
        n = len(self.pts)
        if n % 25 == 0:
            self.get_logger().info(f"{n} waypoints, {self.travelled:.1f} m driven")
            self.save_raw()      # periodic save so nothing is lost if something crashes
        if self.a.min_lap > 0 and self.travelled > self.a.min_lap and n > 20:
            sx, sy = self.pts[0][:2]
            if math.hypot(x - sx, y - sy) < self.a.close_radius:
                self.get_logger().info(f"Lap closed: {n} waypoints, {self.travelled:.1f} m.")
                self.done = True

    def save_raw(self):
        if len(self.pts) < 2:
            return None
        path = raw_path(os.path.expanduser(self.a.out))
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            f.write("# x_m,y_m,yaw_rad,speed_mps\n")
            for x, y, yaw, v in self.pts:
                f.write(f"{x:.4f},{y:.4f},{yaw:.4f},{v:.3f}\n")
        return path


def write_node_csv(raw, a):
    """Process the raw lap into the pure_pursuit node format via make_speed_csv."""
    out = os.path.expanduser(a.out)
    argv = [raw, out, "--spacing", str(a.out_spacing), "--smooth", str(a.smooth),
            "--v-max", str(a.v_max), "--v-min", str(a.v_min), "--a-lat", str(a.a_lat),
            "--a-acc", str(a.a_acc), "--a-brake", str(a.a_brake)]
    old = sys.argv
    sys.argv = ["make_speed_csv.py"] + argv
    try:
        msc.main()
    finally:
        sys.argv = old
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="~/f1tenth_ws/waypoints/drift_1_circle.csv",
                    help="node-ready CSV; its name without .csv is the node's track parameter")
    ap.add_argument("--pose-topic", default="/pf/pose/odom")
    ap.add_argument("--odom-topic", default="/odom")
    ap.add_argument("--spacing", type=float, default=0.05, help="m between recorded points")
    ap.add_argument("--min-lap", type=float, default=15.0,
                    help="m to drive before auto-stop can trigger (0 = never auto-stop)")
    ap.add_argument("--close-radius", type=float, default=0.5)
    ap.add_argument("--max-jump", type=float, default=1.0)
    # passed to make_speed_csv
    ap.add_argument("--out-spacing", type=float, default=0.10)
    ap.add_argument("--smooth", type=float, default=0.8)
    ap.add_argument("--v-max", type=float, default=1.5)
    ap.add_argument("--v-min", type=float, default=0.8)
    ap.add_argument("--a-lat", type=float, default=1.5)
    ap.add_argument("--a-acc", type=float, default=1.0)
    ap.add_argument("--a-brake", type=float, default=1.5)
    a, ros_args = ap.parse_known_args()

    if msc is None:
        print("[WARN] make_speed_csv.py not found next to this script: only the raw file will be written.")

    rclpy.init(args=[sys.argv[0]] + ros_args)
    node = WaypointLogger(a)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass

    raw = node.save_raw()
    if not raw:
        print("\nNo waypoints recorded: is the pose publishing? (ros2 topic hz /pf/pose/odom)")
    else:
        print(f"\nRaw lap: {len(node.pts)} points, {node.travelled:.1f} m -> {raw}")
        if msc is not None and len(node.pts) >= 12:
            write_node_csv(raw, a)
        elif msc is not None:
            print("Too few points for a node CSV (need 12+). Drive a longer lap.")
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()