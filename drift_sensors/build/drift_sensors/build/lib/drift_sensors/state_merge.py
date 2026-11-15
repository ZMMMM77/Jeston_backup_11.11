#!/usr/bin/env python3
"""PF pose + EKF velocity -> /drift/state_odom for drift_policy.

On every /odom_ekf message, look up map->base_link from TF (map->odom from the particle filter,
odom->base_link from the EKF) and publish one Odometry: pose at base_link (rear axle) in the map
frame, twist (vx, vy, r) in the body frame copied from the EKF. Launch drift_policy with
    odom_topic:=/drift/state_odom twist_point:=base_link
Stops publishing when the TF is older than ``tf_timeout_s``, so the policy's odom timeout stops the car.
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from nav_msgs.msg import Odometry
from tf2_ros import Buffer, TransformListener, TransformException


class StateMerge(Node):
    def __init__(self):
        super().__init__('drift_state_merge')
        self.declare_parameter('ekf_topic', '/odom_ekf')
        self.declare_parameter('out_topic', '/drift/state_odom')
        self.declare_parameter('tf_timeout_s', 0.3)
        self.tf_timeout = self.get_parameter('tf_timeout_s').value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.pub = self.create_publisher(Odometry, self.get_parameter('out_topic').value, 10)
        self.create_subscription(Odometry, self.get_parameter('ekf_topic').value, self.on_ekf, 10)
        self.warned = False

    def on_ekf(self, ekf: Odometry):
        try:
            # latest available map->base_link; the EKF TF is current, the PF map->odom lags a bit
            tf = self.tf_buffer.lookup_transform('map', 'base_link', Time())
        except TransformException as e:
            if not self.warned:
                self.get_logger().warn(f'no map->base_link TF yet: {e}')
                self.warned = True
            return
        age = (self.get_clock().now() - Time.from_msg(tf.header.stamp)).nanoseconds * 1e-9
        if age > self.tf_timeout:
            return

        out = Odometry()
        out.header.stamp = ekf.header.stamp
        out.header.frame_id = 'map'
        out.child_frame_id = 'base_link'
        out.pose.pose.position.x = tf.transform.translation.x
        out.pose.pose.position.y = tf.transform.translation.y
        out.pose.pose.orientation = tf.transform.rotation
        out.twist = ekf.twist
        self.pub.publish(out)


def main():
    rclpy.init()
    rclpy.spin(StateMerge())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
