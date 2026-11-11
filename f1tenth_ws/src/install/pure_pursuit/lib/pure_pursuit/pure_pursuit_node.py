#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

import numpy as np
from sensor_msgs.msg import LaserScan
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive
# TODO CHECK: include needed ROS msg type headers and libraries
import csv
import math
import os
from ament_index_python.packages import get_package_share_directory
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker
from rclpy.qos import QoSProfile, DurabilityPolicy
from std_msgs.msg import Float32

def load_waypoints(csv_path):
    points = []
    speeds = []
    curvatures = []

    with open(csv_path, newline='', encoding='utf-8') as file:
        for row in csv.reader(file):
            if not row or row[0].strip().startswith('#'):
                continue

            points.append([float(row[0]), float(row[1])])
            speeds.append(float(row[2]))
            curvatures.append(float(row[5]))

    return np.asarray(points), np.asarray(speeds), np.asarray(curvatures)


def nearest_path_segment(points, car_xy):
    best_distance = float('inf')
    best_index = None
    best_projection = None

    for index in range(len(points)):
        start = points[index]
        end = points[(index + 1) % len(points)]
        direction = end - start

        length_sq = np.dot(direction, direction)
        if length_sq < 1e-12:
            continue
        
        fraction = np.clip(
            np.dot(car_xy - start, direction) / length_sq,
            0.0, 1.0
        )
        projection = start + fraction * direction
        distance = np.linalg.norm(car_xy - projection)

        if distance < best_distance:
            best_distance = distance
            best_index = index
            best_projection = projection

    return best_index, best_projection


def circle_segment_intersection(start, end, center, radius):
    direction = end - start
    offset = start - center

    a = np.dot(direction, direction)
    b = 2.0 * np.dot(offset, direction)
    c = np.dot(offset, offset) - radius ** 2

    if a < 1e-12:
        return None

    discriminant = b ** 2 - 4.0 * a * c
    if discriminant < -1e-9:
        return None

    root = math.sqrt(max(discriminant, 0.0))

    for fraction in (
        (-b - root) / (2.0 * a),
        (-b + root) / (2.0 * a),
    ):
        if -1e-9 <= fraction <= 1.0 + 1e-9:
            return start + np.clip(fraction, 0.0, 1.0) * direction

    return None


def select_lookahead_goal(points, car_xy, lookahead):
    index, projection = nearest_path_segment(points, car_xy)

    if index is None:
        return None

    ordered_points = np.vstack((
        projection,
        points[index + 1:],
        points[:index + 1],
        projection,
    ))

    for start, end in zip(ordered_points[:-1], ordered_points[1:]):
        goal = circle_segment_intersection(
            start, end, car_xy, lookahead
        )
        if goal is not None:
            return goal
    remaining = lookahead

    for start, end in zip(ordered_points[:-1], ordered_points[1:]):
        length = np.linalg.norm(end - start)

        if length < 1e-9:
            continue

        if remaining <= length:
            return start + (remaining / length) * (end - start)

        remaining -= length

    return None

def speed_at_car_position(points, speeds, car_xy):
    index, projection = nearest_path_segment(points, car_xy)

    if index is None:
        return 0.0

    next_index = (index + 1) % len(points)
    direction = points[next_index] - points[index]

    fraction = float(np.clip(
        np.dot(projection - points[index], direction)
        / np.dot(direction, direction),
        0.0,
        1.0,
    ))

    return float(
        (1.0 - fraction) * speeds[index]
        + fraction * speeds[next_index]
    )


def smooth_abs_curvature(curvatures, segment_lengths, window_m):
    spacing = float(np.median(segment_lengths[segment_lengths > 1e-9]))
    count = max(1, round(window_m / spacing))
    if count % 2 == 0:
        count += 1
    half = count // 2
    padded = np.pad(np.abs(curvatures), (half, half), mode='wrap')
    return np.convolve(padded, np.ones(count) / count, mode='valid')


def target_lookahead(curvature, curve_m, straight_m, low, high):
    blend = float(np.clip((curvature - low) / (high - low), 0.0, 1.0))
    blend = blend * blend * (3.0 - 2.0 * blend)
    return straight_m + blend * (curve_m - straight_m)


class PurePursuit(Node):
    """ 
    Implement Pure Pursuit on the car
    This is just a template, you are free to implement your own node!
    """
    def __init__(self):
        super().__init__('pure_pursuit_node')
        # launch/levine_launch.py sets track:=levine, launch/spielberg_launch.py track:=spielberg
        self.declare_parameter('track', 'spielberg')
        track = self.get_parameter('track').value

        defaults = {
            'lookahead_m': 2.5,             
            'straight_lookahead_m': 7.0,
            'curve_preview_m': 15.0,
            'curvature_smooth_m': 2.0,
            'curve_kappa_low': 0.01,
            'curve_kappa_high': 0.04,
            'lookahead_shrink_rate_mps': 2.0,
            'lookahead_grow_rate_mps': 5.0,
            'wheelbase_m': 0.3302,          
            'max_steering_rad': 0.4189,      
            'max_speed_mps': 10.0,            
            'speed_scale': 1.0,         
            'pose_topic': '/ego_racecar/odom',
            'drive_topic': '/drive',
        }

        self.params = {}
        for name, default in defaults.items():
            self.declare_parameter(name, default)
            self.params[name] = self.get_parameter(name).value


        # TODO: load the waypoints of `track` from the package's installed waypoints/ folder:
        #       os.path.join(get_package_share_directory('pure_pursuit'), 'waypoints', <your csv>)
        #       (ament_index_python.packages). A path like /home/you/... only exists on your laptop.
        csv_path = os.path.join(
            get_package_share_directory('pure_pursuit'),
            'waypoints',
            f'{track}.csv',
        )
        self.waypoints, self.waypoint_speeds, curvatures = load_waypoints(csv_path)
        self.segment_lengths = np.linalg.norm(
            np.roll(self.waypoints, -1, axis=0) - self.waypoints, axis=1
        )
        self.path_curvatures = smooth_abs_curvature(
            curvatures, self.segment_lengths, self.params['curvature_smooth_m']
        )
        self.current_lookahead = float(self.params['lookahead_m'])
        self.last_lookahead_time = None

        
        # TODO: create ROS subscribers and publishers
        self.drive_pub = self.create_publisher(
            AckermannDriveStamped,
            self.params['drive_topic'],
            10,
        )
        self.pose_sub = self.create_subscription(
            Odometry,
            self.params['pose_topic'],
            self.pose_callback,
            10,
        )
        path_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.path_pub = self.create_publisher(
            Path, '/pure_pursuit/path', path_qos
        )
        self.goal_pub = self.create_publisher(
            Marker, '/pure_pursuit/goal', 10
        )
        self.lookahead_pub = self.create_publisher(
        Float32, '/pure_pursuit/lookahead_m', 10
        )
        self.lookahead_target_pub = self.create_publisher(
        Float32, '/pure_pursuit/lookahead_target_m', 1
        )

        self.publish_waypoint_path()
        

    def update_lookahead(self, car_xy):
        index = int(np.argmin(np.sum((self.waypoints - car_xy) ** 2, axis=1)))
        distance = 0.0
        bend = 0.0
        for offset in range(len(self.waypoints)):
            next_index = (index + offset) % len(self.waypoints)
            bend = max(bend, float(self.path_curvatures[next_index]))
            distance += float(self.segment_lengths[next_index])
            if distance >= self.params['curve_preview_m']:
                break

        target = target_lookahead(
            bend,
            self.params['lookahead_m'],
            self.params['straight_lookahead_m'],
            self.params['curve_kappa_low'],
            self.params['curve_kappa_high'],
        )
        now = self.get_clock().now()
        dt = 0.0 if self.last_lookahead_time is None else max(
            0.0, min((now - self.last_lookahead_time).nanoseconds * 1e-9, 0.2)
        )
        self.last_lookahead_time = now
        rate = (
            self.params['lookahead_shrink_rate_mps']
            if target < self.current_lookahead
            else self.params['lookahead_grow_rate_mps']
        )
        self.current_lookahead += float(np.clip(
            target - self.current_lookahead, -rate * dt, rate * dt
        ))

        self.lookahead_target_pub.publish(Float32(data=float(target)))
        self.lookahead_pub.publish(
            Float32(data=float(self.current_lookahead))
        )
        return self.current_lookahead

    def pose_callback(self, pose_msg):
        pass
        # TODO: find the current waypoint to track using methods mentioned in lecture
        pose = pose_msg.pose.pose
        car_xy = np.array([pose.position.x, pose.position.y])

        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y ** 2 + q.z ** 2),
        )

        goal = select_lookahead_goal(
            self.waypoints,
            car_xy,
            self.update_lookahead(car_xy),
        )

        command = AckermannDriveStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        if goal is None:
            self.drive_pub.publish(command)
            return

        # TODO: transform goal point to vehicle frame of reference
        dx, dy = goal - car_xy
        local_x = math.cos(yaw) * dx + math.sin(yaw) * dy
        local_y = -math.sin(yaw) * dx + math.cos(yaw) * dy

        # TODO: calculate curvature/steering angle
        distance_sq = local_x ** 2 + local_y ** 2
        if distance_sq < 1e-9:
            self.drive_pub.publish(command)
            return

        curvature = 2.0 * local_y / distance_sq
        steering = math.atan(
            self.params['wheelbase_m'] * curvature
        )
        steering = float(np.clip(
            steering,
            -self.params['max_steering_rad'],
            self.params['max_steering_rad'],
        ))

        reference_speed = speed_at_car_position(
            self.waypoints,
            self.waypoint_speeds,
            car_xy,
        )

        speed = float(np.clip(
            self.params['speed_scale'] * reference_speed,
            0.0,
            self.params['max_speed_mps'],
        ))

        # TODO: publish drive message, don't forget to limit the steering angle.
        command.drive.steering_angle = steering
        command.drive.speed = speed
        self.drive_pub.publish(command)

        self.publish_goal_marker(goal, command.header.stamp)

    def publish_waypoint_path(self):
        path = Path()
        path.header.frame_id = 'map'
        path.header.stamp = self.get_clock().now().to_msg()

        for x, y in np.vstack((self.waypoints, self.waypoints[0])):
            stamped = PoseStamped()
            stamped.header = path.header
            stamped.pose.position.x = float(x)
            stamped.pose.position.y = float(y)
            stamped.pose.orientation.w = 1.0
            path.poses.append(stamped)

        self.path_pub.publish(path)

    def publish_goal_marker(self, goal, stamp):
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = stamp
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        marker.pose.position.x = float(goal[0])
        marker.pose.position.y = float(goal[1])
        marker.pose.orientation.w = 1.0

        marker.scale.x = marker.scale.y = marker.scale.z = 0.28
        marker.color.g = 1.0
        marker.color.a = 1.0

        self.goal_pub.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    print("PurePursuit Initialized")
    pure_pursuit_node = PurePursuit()
    rclpy.spin(pure_pursuit_node)

    pure_pursuit_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
