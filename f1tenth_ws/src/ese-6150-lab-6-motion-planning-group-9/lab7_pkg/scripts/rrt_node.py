#!/usr/bin/env python3
"""
This file contains the class definition for tree nodes and RRT
Before you start, please read: https://arxiv.org/pdf/1105.1186.pdf
"""
import numpy as np
from numpy import linalg as LA
import math
import os
import csv
from std_msgs.msg import Float32
from visualization_msgs.msg import Marker

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PointStamped
from geometry_msgs.msg import Pose
from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Path
from rclpy.qos import QoSProfile, DurabilityPolicy

# TODO: import as you need
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

def smooth_abs_curvature(curvatures, segment_lengths, window_m):
    spacing = float(np.median(segment_lengths[segment_lengths > 1e-9]))
    count = max(1, round(window_m / spacing))
    if count % 2 == 0:
        count += 1
    half = count // 2
    padded = np.pad(np.abs(curvatures), (half, half), mode='wrap')
    return np.convolve(padded, np.ones(count) / count, mode='valid')

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


def target_lookahead(curvature, curve_m, straight_m, low, high):
    blend = float(np.clip((curvature - low) / (high - low), 0.0, 1.0))
    blend = blend * blend * (3.0 - 2.0 * blend)
    return straight_m + blend * (curve_m - straight_m)

# class def for tree nodes
# It's up to you if you want to use this
# (named TreeNode: `Node` is the ROS 2 node class imported above)
class TreeNode(object):
    def __init__(self):
    
        self.x = None
        self.y = None
        self.parent = None
        self.cost = None # only used in RRT*
        self.is_root = False

# class def for RRT
class RRT(Node):
    def __init__(self):
        super().__init__('rrt_node')
        # topics, not saved as attributes
        # TODO: grab topics from param file, you'll need to change the yaml file
        pose_topic = "/pf/pose/odom"   # nav_msgs/Odometry, the ground truth in the simulator
        scan_topic = "/scan"

        # declare your own parameters here (self.declare_parameter) and give
        # them values in launch/levine_launch.py; the tuned values should also
        # be the defaults, in case the autograder has to start the node without it.
        defaults = {
            'scan_min_range_m': 0.05,
            'inflation_radius_m': 0.4,
            'rrt_step_m': 0.5,
            'goal_tolerance_m': 0.3,
            'rrt_goal_distance_m': 3.0,
            
            'rrt_max_iter': 500,
            'goal_sample_rate': 0.2,
            'grid_resolution_m': 0.05,
            'grid_x_min_m': -1.0,
            'grid_y_min_m': -5.0,
            'grid_width_cells': 180,
            'grid_height_cells': 280,
            'car_length_m': 0.58,
            'car_width_m': 0.31,
            'car_body_center_x_m': 0.1651,

            'lookahead_m': 2.8,
            'straight_lookahead_m': 6.0,
            'curve_preview_m': 15.0,
            'curvature_smooth_m': 2.0,
            'curve_kappa_low': 0.01,
            'curve_kappa_high': 0.04,
            'lookahead_shrink_rate_mps': 2.0,
            'lookahead_grow_rate_mps': 5.0,
            'wheelbase_m': 0.3302,
            'max_steering_rad': 0.4189,
            'max_speed_mps': 12.0,
            'speed_scale': 1.0,
        }
        self.params = {}
        for name, default in defaults.items():
            self.declare_parameter(name, default)
            self.params[name] = self.get_parameter(name).value
        self.car_x = None
        self.car_y = None
        self.car_yaw = None
        self.pose_ready = False
        self.cached_path_map = None

        # TODO: load your global path from the package's installed waypoints/ folder:
        #       os.path.join(get_package_share_directory('lab7_pkg'), 'waypoints', <your csv>)
        #       A path like /home/you/... only exists on your laptop.
        waypoint_path = os.path.join(
            get_package_share_directory('lab7_pkg'),
            'waypoints',
            'levine.csv'
        )
        self.waypoints, self.waypoint_speeds, curvatures = load_waypoints(
            waypoint_path
        )
        self.segment_lengths = np.linalg.norm(
            np.roll(self.waypoints, -1, axis=0) - self.waypoints, axis=1
        )
        self.path_curvatures = smooth_abs_curvature(
            curvatures, self.segment_lengths, self.params['curvature_smooth_m']
        )
        self.current_lookahead = float(self.params['lookahead_m'])
        self.last_lookahead_time = None


        self.get_logger().info(
            f"Loaded {len(self.waypoints)} waypoints"
        )

        # TODO: create subscribers
        self.pose_sub_ = self.create_subscription(
            Odometry,
            pose_topic,
            self.pose_callback,
            1)
        self.pose_sub_

        self.scan_sub_ = self.create_subscription(
            LaserScan,
            scan_topic,
            self.scan_callback,
            1)
        self.scan_sub_
        
        # publishers
        # TODO: create a drive message publisher, and other publishers that you might need
        self.drive_pub_ = self.create_publisher(
            AckermannDriveStamped,
            '/drive', 
            1)

        path_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.path_pub = self.create_publisher(
            Path, '/pure_pursuit/path', path_qos
        )
        self.publish_waypoint_path()

        self.goal_pub = self.create_publisher(
            Marker, '/pure_pursuit/goal', 10
        )
        self.lookahead_pub = self.create_publisher(
            Float32, '/pure_pursuit/lookahead_m', 10
        )
        self.lookahead_target_pub = self.create_publisher(
            Float32, '/pure_pursuit/lookahead_target_m', 1
        )
        self.grid_pub_ = self.create_publisher(
            OccupancyGrid, '/rrt/occupancy_grid', 1
        )
        self.obstacle_pub_ = self.create_publisher(Marker, '/rrt/obstacles', 1)
        self.inflation_pub_ = self.create_publisher(Marker, '/rrt/inflation', 1)
        self.last_grid_debug_ns = None
        self.tree_pub_ = self.create_publisher(
            Marker, '/rrt/tree', 1
        )
        self.path_pub_ = self.create_publisher(
            Marker, '/rrt/path', 1
        )

# class attributes
        # TODO: maybe create your occupancy grid here
        self.grid_resolution = self.params['grid_resolution_m']
        self.grid_x_min = self.params['grid_x_min_m']
        self.grid_y_min = self.params['grid_y_min_m']
        self.grid_width = self.params['grid_width_cells']
        self.grid_height = self.params['grid_height_cells']
        self.grid = np.full(
            (self.grid_height, self.grid_width), -1, dtype=np.int8
        )
        self.scan_ready = False

        xs = self.grid_x_min + (
            np.arange(self.grid_width) + 0.5
        ) * self.grid_resolution

        ys = (
            self.grid_y_min
            + (np.arange(self.grid_height) + 0.5)
            * self.grid_resolution
        )[:, None]

        half_cell = self.grid_resolution / 2.0

        self.body_mask = (
            (
                np.abs(xs - self.params['car_body_center_x_m'])
                <= self.params['car_length_m'] / 2.0 - half_cell
            )
            & (
                np.abs(ys)
                <= self.params['car_width_m'] / 2.0 - half_cell
            )
        )

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

    def publish_rrt(self, tree, path, car_xy, yaw, stamp):
        edges = []
        for node in tree:
            if node.parent is not None:
                edges.extend([tree[node.parent], node])

        c, s = math.cos(yaw), math.sin(yaw)

        for publisher, name, kind, nodes, width, color in (
            (
                self.tree_pub_, 'tree', Marker.LINE_LIST,
                edges, 0.025, (0.1, 0.5, 1.0),
            ),
            (
                self.path_pub_, 'path', Marker.LINE_STRIP,
                path, 0.08, (1.0, 0.1, 0.1),
            ),
        ):
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = stamp
            marker.ns = name
            marker.id = 0
            marker.type = kind
            marker.action = (
                Marker.ADD if len(nodes) >= 2 else Marker.DELETE
            )
            marker.pose.orientation.w = 1.0
            marker.scale.x = width
            marker.color.r, marker.color.g, marker.color.b = color
            marker.color.a = 1.0
            marker.lifetime.sec = 1

            for node in nodes:
                point = Point()
                point.x = float(
                    car_xy[0] + c * node.x - s * node.y
                )
                point.y = float(
                    car_xy[1] + s * node.x + c * node.y
                )
                point.z = 0.08
                marker.points.append(point)

            publisher.publish(marker)

    def track_goal(self, goal, car_xy, yaw):
        command = AckermannDriveStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        if goal is None:
            self.drive_pub_.publish(command)
            return

        dx, dy = goal - car_xy
        local_x = math.cos(yaw) * dx + math.sin(yaw) * dy
        local_y = -math.sin(yaw) * dx + math.cos(yaw) * dy

        distance_sq = local_x ** 2 + local_y ** 2
        if distance_sq < 1e-9:
            self.drive_pub_.publish(command)
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

        command.drive.steering_angle = steering
        command.drive.speed = speed
        self.drive_pub_.publish(command)
        self.publish_goal_marker(goal, command.header.stamp)

    def local_to_grid(self, x, y):
        col = math.floor((x - self.grid_x_min) / self.grid_resolution)
        row = math.floor((y - self.grid_y_min) / self.grid_resolution)
        return (row, col) if self.grid_contains(row, col) else None

    def grid_contains(self, rows, cols):
        return (
            (rows >= 0) & (rows < self.grid_height)
            & (cols >= 0) & (cols < self.grid_width)
        )

    def grid_to_local(self, rows, cols):
        return (
            self.grid_x_min + (cols + 0.5) * self.grid_resolution,
            self.grid_y_min + (rows + 0.5) * self.grid_resolution,
        )

    def is_free(self, x, y):
        cell = self.local_to_grid(x, y)
        return cell is not None and self.grid[cell] == 0

    def scan_callback(self, scan_msg):
        """
        LaserScan callback, you should update your occupancy grid here

        Args: 
            scan_msg (LaserScan): incoming message from subscribed topic
        Returns:

        """        

        self.update_grid(scan_msg)
        occupied = self.grid == 100
        self.inflate_grid()
        self.scan_ready = bool(np.any(self.grid == 0))
        self.publish_grid(scan_msg.header.stamp)
        self.publish_grid_debug(occupied, scan_msg.header.stamp)

    def update_grid(self, scan_msg):
        self.grid.fill(-1)
        hits = []

        ray_limit = math.hypot(
            self.grid_width * self.grid_resolution,
            self.grid_height * self.grid_resolution,
        )

        for i, distance in enumerate(scan_msg.ranges):
            if (
                math.isnan(distance) or distance <= 0.0
                or distance < max(
                    scan_msg.range_min, self.params['scan_min_range_m']
                )
            ):
                continue

            angle = scan_msg.angle_min + i * scan_msg.angle_increment
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)

            ray_length = min(distance, scan_msg.range_max, ray_limit)

            steps = np.arange(
                0.0, ray_length, self.grid_resolution / 2.0
            )
            xs = 0.270 + steps * cos_angle
            ys = steps * sin_angle

            cols = np.floor(
                (xs - self.grid_x_min) / self.grid_resolution
            ).astype(int)
            rows = np.floor(
                (ys - self.grid_y_min) / self.grid_resolution
            ).astype(int)

            inside = self.grid_contains(rows, cols)
            self.grid[rows[inside], cols[inside]] = 0

            if math.isfinite(distance) and distance < scan_msg.range_max:
                cell = self.local_to_grid(
                    0.270 + distance * cos_angle,
                    distance * sin_angle,
                )
                if cell is not None:
                    hits.append(cell)

        for row, col in hits:
            self.grid[row, col] = 100

        self.grid[(self.grid == -1) & self.body_mask] = 0

    def inflate_grid(self):
        radius = math.ceil(
            self.params['inflation_radius_m'] / self.grid_resolution
        )
        occupied_rows, occupied_cols = np.nonzero(self.grid == 100)

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy > radius * radius:
                    continue

                rows = occupied_rows + dy
                cols = occupied_cols + dx

                inside = self.grid_contains(rows, cols)
                self.grid[rows[inside], cols[inside]] = 100

    def publish_grid_debug(self, occupied, stamp):
        if not (self.obstacle_pub_.get_subscription_count()
                or self.inflation_pub_.get_subscription_count()):
            return
        stamp_ns = stamp.sec * 1000000000 + stamp.nanosec
        if (self.last_grid_debug_ns is not None
                and 0 <= stamp_ns - self.last_grid_debug_ns < 200000000):
            return
        self.last_grid_debug_ns = stamp_ns
        for publisher, name, mask, color in (
            (self.obstacle_pub_, 'obstacles', occupied, (1.0, 0.1, 0.1, 0.9)),
            (self.inflation_pub_, 'inflation',
             (self.grid == 100) & ~occupied, (1.0, 0.55, 0.0, 0.45)),
        ):
            rows, cols = np.nonzero(mask)
            marker = Marker()
            marker.header.frame_id = 'base_link'
            marker.header.stamp = stamp
            marker.ns = name
            marker.id = 0
            marker.type = Marker.CUBE_LIST
            marker.action = Marker.ADD if len(rows) else Marker.DELETE
            marker.pose.orientation.w = 1.0
            marker.scale.x = self.grid_resolution
            marker.scale.y = self.grid_resolution
            marker.scale.z = 0.02
            marker.color.r, marker.color.g, marker.color.b, marker.color.a = color
            marker.lifetime.sec = 1
            xs, ys = self.grid_to_local(rows, cols)
            for x, y in zip(xs, ys):
                point = Point()
                point.x = float(x)
                point.y = float(y)
                point.z = 0.06
                marker.points.append(point)
            publisher.publish(marker)

    def publish_grid(self, stamp):
        grid_msg = OccupancyGrid()
        grid_msg.header.stamp = stamp
        grid_msg.header.frame_id = 'base_link'
        grid_msg.info.resolution = self.grid_resolution
        grid_msg.info.width = self.grid_width
        grid_msg.info.height = self.grid_height
        grid_msg.info.origin.position.x = self.grid_x_min
        grid_msg.info.origin.position.y = self.grid_y_min
        grid_msg.info.origin.orientation.w = 1.0
        grid_msg.data = self.grid.ravel().tolist()

        self.grid_pub_.publish(grid_msg)

    def pose_callback(self, pose_msg):
        """
        The pose callback: the simulator's ground truth pose (nav_msgs/Odometry)
        Here is where the main RRT loop happens. On the car, subscribe to the
        particle filter's pose instead.

        Args: 
            pose_msg (Odometry): incoming message from subscribed topic
        Returns:

        """
        pose = pose_msg.pose.pose
        car_xy = np.array([pose.position.x, pose.position.y])

        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y ** 2 + q.z ** 2),
        )

        self.car_x, self.car_y = car_xy
        self.car_yaw = yaw
        self.pose_ready = True

        lookahead = self.update_lookahead(car_xy)

        c, s = math.cos(yaw), math.sin(yaw)
        rotation = np.array([[c, s], [-s, c]])
        tree = []
        path = self.reuse_path(car_xy, rotation)
        tracking_goal = self.select_path_goal(path, lookahead)

        if tracking_goal is None:
            path = []
            reference = select_lookahead_goal(
                self.waypoints, car_xy, self.params['rrt_goal_distance_m']
            )
            if reference is not None and self.scan_ready:
                local_goal = self.select_rrt_goal(rotation @ (reference - car_xy))
                if local_goal is not None:
                    tree, path = self.plan_path(local_goal[0], local_goal[1])
            tracking_goal = self.select_path_goal(path, lookahead)

        self.cached_path_map = (
            car_xy + np.array([(node.x, node.y) for node in path]) @ rotation
            if tracking_goal is not None else None
        )
        self.publish_rrt(tree, path, car_xy, yaw, pose_msg.header.stamp)
        global_goal = (
            None if tracking_goal is None
            else car_xy + rotation.T @ tracking_goal
        )
        self.track_goal(global_goal, car_xy, yaw)

    def reuse_path(self, car_xy, rotation):
        if not self.scan_ready or self.cached_path_map is None:
            return []

        points = (self.cached_path_map - car_xy) @ rotation.T
        if len(points) < 2:
            return []

        starts = points[:-1]
        directions = points[1:] - starts
        lengths_sq = np.sum(directions ** 2, axis=1)
        fractions = np.clip(
            -np.sum(starts * directions, axis=1)
            / np.maximum(lengths_sq, 1e-12), 0.0, 1.0
        )
        projections = starts + fractions[:, None] * directions
        index = int(np.argmin(np.sum(projections ** 2, axis=1)))

        if np.linalg.norm(projections[index]) > self.params['rrt_step_m']:
            return []

        remaining = points[index + 1:]
        while len(remaining) and np.linalg.norm(remaining[0]) < 1e-9:
            remaining = remaining[1:]
        if not len(remaining) or remaining[0, 0] <= 0.0:
            return []

        points = np.vstack((np.zeros(2), remaining))
        distance = np.sum(np.linalg.norm(np.diff(points, axis=0), axis=1))
        if distance <= max(self.params['rrt_step_m'], self.params['goal_tolerance_m']):
            return []

        path = []
        for x, y in points:
            node = TreeNode()
            node.x, node.y = float(x), float(y)
            node.is_root = not path
            node.parent = len(path) - 1 if path else None
            if path and self.check_collision(path[-1], node):
                return []
            path.append(node)

        return path

    def select_rrt_goal(self, reference):
        root = self.local_to_grid(0.0, 0.0)

        if root is None or self.grid[root] != 0:
            return None

        reachable = np.zeros(self.grid.shape, dtype=bool)
        reachable[root] = True
        pending = [root]

        while pending:
            row, col = pending.pop()

            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                r, c = row + dr, col + dc

                if (
                    self.grid_contains(r, c)
                    and not reachable[r, c]
                    and self.grid[r, c] == 0
                ):
                    reachable[r, c] = True
                    pending.append((r, c))

        cell = self.local_to_grid(reference[0], reference[1])

        if cell is not None and reachable[cell] and reference[0] > 0.0:
            return reference

        cells = np.argwhere(reachable)

        points = np.column_stack(
            self.grid_to_local(cells[:, 0], cells[:, 1])
        )

        points = points[points[:, 0] > self.params['rrt_step_m']]

        if len(points) == 0:
            return None

        index = np.argmin(np.sum((points - reference) ** 2, axis=1))
        return points[index]
    
    def select_path_goal(self, path, lookahead):
        if len(path) < 2:
            return None

        candidates = []
        spacing = self.grid_resolution / 2.0
        for start, end in zip(path[:-1], path[1:]):
            start_xy = np.array([start.x, start.y])
            end_xy = np.array([end.x, end.y])
            at_limit = np.linalg.norm(end_xy) >= lookahead
            if at_limit:
                end_xy = circle_segment_intersection(
                    start_xy, end_xy, np.zeros(2), lookahead
                )
                if end_xy is None:
                    break

            count = max(1, math.ceil(np.linalg.norm(end_xy - start_xy) / spacing))
            for fraction in np.linspace(0.0, 1.0, count + 1)[1:]:
                candidate = start_xy + fraction * (end_xy - start_xy)
                if candidate[0] > 0.0:
                    candidates.append(candidate)
            if at_limit:
                break

        for candidate in reversed(candidates):
            if self.tracking_arc_is_free(candidate):
                return candidate
        return None


    def tracking_arc_is_free(self, goal):
        if not self.scan_ready:
            return False

        x, y = goal
        distance_sq = x * x + y * y
        if x <= 0.0 or distance_sq < 1e-9:
            return False

        curvature = 2.0 * y / distance_sq
        steering = math.atan(self.params['wheelbase_m'] * curvature)
        if abs(steering) > self.params['max_steering_rad'] + 1e-9:
            return False

        length = (
            2.0 * math.atan2(y, x) / curvature
            if abs(curvature) > 1e-9 else math.sqrt(distance_sq)
        )
        steps = max(1, math.ceil(length / (self.grid_resolution / 2.0)))
        distances = (np.arange(steps) + 0.5) * length / steps
        if abs(curvature) > 1e-9:
            angles = curvature * distances
            xs = np.sin(angles) / curvature
            ys = 2.0 * np.sin(angles / 2.0) ** 2 / curvature
        else:
            xs = distances
            ys = np.zeros_like(distances)

        cols = np.floor((xs - self.grid_x_min) / self.grid_resolution).astype(int)
        rows = np.floor((ys - self.grid_y_min) / self.grid_resolution).astype(int)
        radius = length / (2.0 * steps)
        half_cell = self.grid_resolution / 2.0
        # Each midpoint disk covers its entire arc interval, including cell corners.
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                rr, cc = rows + dy, cols + dx
                cell_x = self.grid_x_min + (cc + 0.5) * self.grid_resolution
                cell_y = self.grid_y_min + (rr + 0.5) * self.grid_resolution
                gap_x = np.maximum(np.abs(xs - cell_x) - half_cell, 0.0)
                gap_y = np.maximum(np.abs(ys - cell_y) - half_cell, 0.0)
                touched = gap_x ** 2 + gap_y ** 2 <= radius ** 2 + 1e-12
                inside = self.grid_contains(rr, cc)
                if np.any(touched & ~inside):
                    return False
                if np.any(self.grid[rr[touched & inside], cc[touched & inside]] != 0):
                    return False
        return True


    def plan_path(self, goal_x, goal_y):
        if not self.scan_ready:
            return [], []

        root = TreeNode()
        root.x = 0.0
        root.y = 0.0
        root.is_root = True

        tree = [root]

        if not self.is_free(root.x, root.y) or not self.is_free(goal_x, goal_y):
            return tree, []

        for _ in range(self.params['rrt_max_iter']):
            if np.random.random() < self.params['goal_sample_rate']:
                sampled_point = (goal_x, goal_y)
            else:
                sampled_point = self.sample()

            if sampled_point is None:
                break

            nearest_index = self.nearest(tree, sampled_point)
            nearest_node = tree[nearest_index]

            new_node = self.steer(nearest_node, sampled_point)

            if new_node is None or self.check_collision(nearest_node, new_node):
                continue

            new_node.parent = nearest_index
            tree.append(new_node)

            if self.is_goal(new_node, goal_x, goal_y):
                goal_node = TreeNode()
                goal_node.x = goal_x
                goal_node.y = goal_y

                if self.check_collision(new_node, goal_node):
                    continue

                goal_node.parent = len(tree) - 1
                tree.append(goal_node)

                return tree, self.find_path(tree, goal_node)

        return tree, []

    def sample(self):
        """
        This method should randomly sample the free space, and returns a viable point

        Args:
        Returns:
            (x, y) (float float): a tuple representing the sampled point

        """
        free_cells = np.argwhere(self.grid == 0)

        if len(free_cells) == 0:
            return None

        row, col = free_cells[np.random.randint(len(free_cells))]

        return self.grid_to_local(row, col)

    def nearest(self, tree, sampled_point):
        """
        This method should return the nearest node on the tree to the sampled point

        Args:
            tree ([]): the current RRT tree
            sampled_point (tuple of (float, float)): point sampled in free space
        Returns:
            nearest_node (int): index of neareset node on the tree
        """
        distances = [
            (node.x - sampled_point[0]) ** 2
            + (node.y - sampled_point[1]) ** 2
            for node in tree
        ]

        nearest_node = int(np.argmin(distances))
        return nearest_node

    def steer(self, nearest_node, sampled_point):
        """
        This method should return a point in the viable set such that it is closer 
        to the nearest_node than sampled_point is.

        Args:
            nearest_node (Node): nearest node on the tree to the sampled point
            sampled_point (tuple of (float, float)): sampled point
        Returns:
            new_node (Node): new node created from steering
        """
        dx = sampled_point[0] - nearest_node.x
        dy = sampled_point[1] - nearest_node.y
        distance = math.hypot(dx, dy)

        if distance < 1e-9:
            return None

        step = min(self.params['rrt_step_m'], distance)

        new_node = TreeNode()
        new_node.x = nearest_node.x + step * dx / distance
        new_node.y = nearest_node.y + step * dy / distance
        return new_node

    def check_collision(self, nearest_node, new_node):
        """
        This method should return whether the path between nearest and new_node is
        collision free.

        Args:
            nearest (Node): nearest node on the tree
            new_node (Node): new node from steering
        Returns:
            collision (bool): whether the path between the two nodes are in collision
                              with the occupancy grid
        """
        if not self.scan_ready:
            return True
        distance = math.hypot(
            new_node.x - nearest_node.x,
            new_node.y - nearest_node.y,
        )
        steps = max(
            1,
            math.ceil(distance / (self.grid_resolution / 2.0)),
        )
        for fraction in np.linspace(0.0, 1.0, steps + 1):
            x = nearest_node.x + fraction * (
                new_node.x - nearest_node.x
            )
            y = nearest_node.y + fraction * (
                new_node.y - nearest_node.y
            )
            if not self.is_free(x, y):
                return True

        return False

    def is_goal(self, latest_added_node, goal_x, goal_y):
        """
        This method should return whether the latest added node is close enough
        to the goal.

        Args:
            latest_added_node (Node): latest added node on the tree
            goal_x (double): x coordinate of the current goal
            goal_y (double): y coordinate of the current goal
        Returns:
            close_enough (bool): true if node is close enoughg to the goal
        """
        distance = math.hypot(
            latest_added_node.x - goal_x,
            latest_added_node.y - goal_y,
        )
        return distance <= self.params['goal_tolerance_m']

    def find_path(self, tree, latest_added_node):
        """
        This method returns a path as a list of Nodes connecting the starting point to
        the goal once the latest added node is close enough to the goal

        Args:
            tree ([]): current tree as a list of Nodes
            latest_added_node (Node): latest added node in the tree
        Returns:
            path ([]): valid path as a list of Nodes
        """
        path = []
        node = latest_added_node

        while True:
            path.append(node)

            if node.parent is None:
                break

            node = tree[node.parent]

        path.reverse()
        return path

    # The following methods are needed for RRT* and not RRT
    def cost(self, tree, node):
        """
        This method should return the cost of a node

        Args:
            node (Node): the current node the cost is calculated for
        Returns:
            cost (float): the cost value of the node
        """
        return 0

    def line_cost(self, n1, n2):
        """
        This method should return the cost of the straight line between n1 and n2

        Args:
            n1 (Node): node at one end of the straight line
            n2 (Node): node at the other end of the straint line
        Returns:
            cost (float): the cost value of the line
        """
        return 0

    def near(self, tree, node):
        """
        This method should return the neighborhood of nodes around the given node

        Args:
            tree ([]): current tree as a list of Nodes
            node (Node): current node we're finding neighbors for
        Returns:
            neighborhood ([]): neighborhood of nodes as a list of Nodes
        """
        neighborhood = []
        return neighborhood

def main(args=None):
    rclpy.init(args=args)
    print("RRT Initialized")
    rrt_node = RRT()
    rclpy.spin(rrt_node)

    rrt_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
