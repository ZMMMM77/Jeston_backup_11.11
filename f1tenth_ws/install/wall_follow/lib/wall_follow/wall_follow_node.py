#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import numpy as np
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped


class WallFollow(Node):
    """
    Left-wall-following controller.
    """

    def __init__(self):
        super().__init__('wall_follow_node')

        self.lidarscan_topic = '/scan'
        self.drive_topic = '/drive'

        self.scan_subscriber = self.create_subscription(
            LaserScan,
            self.lidarscan_topic,
            self.scan_callback,
            10
        )

        self.drive_publisher = self.create_publisher(
            AckermannDriveStamped,
            self.drive_topic,
            10
        )

        # Start with P-only control on the real car.
        self.kp = 0.35
        self.kd = 0.03
        self.ki = 0.0

        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = None

        # Filtered wall-following error.
        self.filtered_error = None

        # Smaller value means stronger smoothing:
        # 25% new measurement and 75% previous value.
        self.error_filter_alpha = 0.25

        # Desired distance from the left wall in meters.
        self.desired_distance = 0.60

        # Look-ahead distance in meters.
        self.lookahead_distance = 1.0

        # Steering-angle safety limit in radians.
        self.max_steering_angle = 0.35

        # Speed settings in m/s.
        self.straight_speed = 3.0
        self.medium_turn_speed = 1.5
        self.sharp_turn_speed = 1.0

        # Use measurements within +/- 2 degrees.
        self.range_window_degrees = 2.0

        self.angle_min = 0.0
        self.angle_increment = 0.0
        self.range_min = 0.0
        self.range_max = 0.0

        self.received_scan = False
        self.last_log_time_ns = 0

        # Values used for diagnostics.
        self.last_a = None
        self.last_b = None
        self.last_alpha = None
        self.last_future_distance = None
        self.last_raw_error = None

        self.get_logger().info('WallFollow initialized')


    def get_range(self, range_data, angle):
        """
        Return the median valid LiDAR distance near the requested angle.

        Measurements inside a +/- 2-degree window are used.

        Returns:
            Distance in meters, or None if no valid measurement exists.
        """

        if len(range_data) == 0:
            return None

        if self.angle_increment == 0.0:
            return None

        scan_end_angle = (
            self.angle_min
            + self.angle_increment * (len(range_data) - 1)
        )

        minimum_available_angle = min(
            self.angle_min,
            scan_end_angle
        )

        maximum_available_angle = max(
            self.angle_min,
            scan_end_angle
        )

        # Do not silently replace an unavailable angle with an edge beam.
        if (
            angle < minimum_available_angle
            or angle > maximum_available_angle
        ):
            return None

        center_index = int(round(
            (angle - self.angle_min)
            / self.angle_increment
        ))

        window_radians = np.deg2rad(
            self.range_window_degrees
        )

        half_window = max(
            1,
            int(round(
                window_radians
                / abs(self.angle_increment)
            ))
        )

        start_index = max(
            0,
            center_index - half_window
        )

        end_index = min(
            len(range_data),
            center_index + half_window + 1
        )

        samples = np.asarray(
            range_data[start_index:end_index],
            dtype=np.float64
        )

        valid_samples = samples[
            np.isfinite(samples)
            & (samples >= self.range_min)
            & (samples <= self.range_max)
        ]

        if valid_samples.size == 0:
            return None

        return float(np.median(valid_samples))


    def get_error(self, range_data, desired_distance):
        """
        Calculate the predicted distance error from the left wall.

        Returns:
            Filtered distance error, or None if the required LiDAR
            measurements are unavailable.
        """

        theta = np.deg2rad(45.0)

        # 45 degrees toward the left/front.
        a = self.get_range(
            range_data,
            np.deg2rad(45.0)
        )

        # 90 degrees directly toward the left.
        b = self.get_range(
            range_data,
            np.deg2rad(90.0)
        )

        if a is None or b is None:
            return None

        alpha = np.arctan2(
            a * np.cos(theta) - b,
            a * np.sin(theta)
        )

        current_distance = b * np.cos(alpha)

        future_distance = (
            current_distance
            + self.lookahead_distance * np.sin(alpha)
        )

        raw_error = (
            future_distance
            - desired_distance
        )

        if not np.isfinite(raw_error):
            return None

        # Low-pass filter the real LiDAR measurement.
        if self.filtered_error is None:
            self.filtered_error = float(raw_error)
        else:
            self.filtered_error = (
                self.error_filter_alpha * raw_error
                + (1.0 - self.error_filter_alpha)
                * self.filtered_error
            )

        self.last_a = float(a)
        self.last_b = float(b)
        self.last_alpha = float(alpha)
        self.last_future_distance = float(future_distance)
        self.last_raw_error = float(raw_error)

        return float(self.filtered_error)


    def publish_drive(self, steering_angle, speed):
        """
        Publish one Ackermann drive command.
        """

        drive_msg = AckermannDriveStamped()

        drive_msg.header.stamp = (
            self.get_clock().now().to_msg()
        )

        drive_msg.drive.steering_angle = float(
            steering_angle
        )

        # Positive speed means forward.
        # The direction is configured in the vehicle configuration.
        drive_msg.drive.speed = float(speed)

        self.drive_publisher.publish(drive_msg)


    def stop_vehicle(self):
        """
        Request zero speed and centered steering.
        """

        self.publish_drive(
            steering_angle=0.0,
            speed=0.0
        )


    def pid_control(self, error, velocity):
        """
        Calculate and publish the steering command.
        """

        current_time = self.get_clock().now()

        if self.prev_time is None:
            derivative = 0.0
        else:
            dt = (
                current_time - self.prev_time
            ).nanoseconds / 1e9

            if dt > 0.0001:
                self.integral += error * dt

                derivative = (
                    error - self.prev_error
                ) / dt
            else:
                derivative = 0.0

        angle = (
            self.kp * error
            + self.ki * self.integral
            + self.kd * derivative
        )

        angle = float(np.clip(
            angle,
            -self.max_steering_angle,
            self.max_steering_angle
        ))

        absolute_angle = abs(angle)

        if absolute_angle > np.deg2rad(20.0):
            velocity = self.sharp_turn_speed
        elif absolute_angle > np.deg2rad(10.0):
            velocity = self.medium_turn_speed

        self.prev_error = error
        self.prev_time = current_time

        # No speed-direction reversal here.
        # Positive velocity is published directly.
        commanded_speed = velocity

        self.publish_drive(
            steering_angle=angle,
            speed=commanded_speed
        )

        # Print diagnostics approximately once per second.
        current_time_ns = current_time.nanoseconds

        if (
            current_time_ns - self.last_log_time_ns
            >= 1_000_000_000
        ):
            self.get_logger().info(
                'a=%.2f m, b=%.2f m, '
                'future=%.2f m, raw_error=%.3f m, '
                'filtered_error=%.3f m, steering=%.3f rad, '
                'speed=%.2f m/s'
                % (
                    self.last_a,
                    self.last_b,
                    self.last_future_distance,
                    self.last_raw_error,
                    error,
                    angle,
                    commanded_speed
                )
            )

            self.last_log_time_ns = current_time_ns


    def scan_callback(self, msg):
        """
        Process each incoming LiDAR scan.
        """

        self.angle_min = msg.angle_min
        self.angle_increment = msg.angle_increment
        self.range_min = msg.range_min
        self.range_max = msg.range_max

        if not self.received_scan:
            front_distance = self.get_range(
                msg.ranges,
                0.0
            )

            left_distance = self.get_range(
                msg.ranges,
                np.deg2rad(90.0)
            )

            self.get_logger().info(
                f'收到雷达数据：一共有 {len(msg.ranges)} 束激光'
            )

            if front_distance is None:
                self.get_logger().warn(
                    '正前方没有有效雷达数据'
                )
            else:
                self.get_logger().info(
                    f'正前方距离：{front_distance:.2f} 米'
                )

            if left_distance is None:
                self.get_logger().warn(
                    '正左方没有有效雷达数据'
                )
            else:
                self.get_logger().info(
                    f'正左方距离：{left_distance:.2f} 米'
                )

            self.received_scan = True

        error = self.get_error(
            msg.ranges,
            self.desired_distance
        )

        # Stop instead of using an extreme command when either
        # required LiDAR measurement is unavailable.
        if error is None:
            self.get_logger().warn(
                '45°或90°附近没有有效雷达数据，发送停车命令'
            )

            self.prev_time = None
            self.stop_vehicle()
            return

        self.pid_control(
            error,
            self.straight_speed
        )


def main(args=None):
    rclpy.init(args=args)

    wall_follow_node = WallFollow()

    try:
        rclpy.spin(wall_follow_node)
    except KeyboardInterrupt:
        pass
    finally:
        # Send a stop command before shutting down.
        wall_follow_node.stop_vehicle()
        wall_follow_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()