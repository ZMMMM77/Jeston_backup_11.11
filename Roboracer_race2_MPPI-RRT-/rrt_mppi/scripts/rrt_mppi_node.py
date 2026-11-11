#!/usr/bin/env python3
"""Pure MPPI ROS adapter, current-state prediction and essential visualization."""
import csv,json,math,time,sys,os
from pathlib import Path as FilePath
from dataclasses import dataclass,fields,replace
from collections import deque
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data,QoSProfile,DurabilityPolicy
from ament_index_python.packages import get_package_share_directory
from ackermann_msgs.msg import AckermannDriveStamped
from nav_msgs.msg import Odometry,OccupancyGrid,Path
from geometry_msgs.msg import PoseStamped,Point,Vector3Stamped
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from visualization_msgs.msg import Marker,MarkerArray
from tf2_ros import Buffer,TransformListener,TransformException
from planning_common import (Config, arc, arc_clear, collides, csv_local_reference, path_clear, scan_grid, sweep_segment_clear, wrap)
from mppi import (MPPI, MPPIConfig, advance, braking_clear, cost, dynamics, evaluate, mppi_step, reference_from_path, reference_steering, rollout, rollout_validity, simulate, stationary_recovery_controls, step, step_euler, step_rk4)

class MPPIVisualization:
    """Publish the global CSV path and the two current MPPI trajectories."""

    def __init__(self, node, waypoints):
        self.display_pub = node.create_publisher(MarkerArray, '/rrt_mppi/display', 1)
        self.actual_pub = node.create_publisher(MarkerArray, '/mppi/actual_motion', 1)
        self.motion_history = deque(maxlen=16)
        self.predict = simulate
        self.node = node
        self.mode_pub = node.create_publisher(String, '/rrt_mppi/mode', QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.waypoints = waypoints
        path_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.path_pub = node.create_publisher(Marker, '/mppi/global_path', path_qos)
        self.reference_pub = node.create_publisher(MarkerArray, '/mppi/reference_trajectory', 1)
        self.prediction_pub = node.create_publisher(MarkerArray, '/mppi/predicted_trajectory', 1)
        self.telemetry_pubs = {name: node.create_publisher(Vector3Stamped, f'/mppi/telemetry/{name}', 10) for name in ('speed', 'acceleration', 'steering_estimate')}
        self.previous_sample = None
        self.filtered_acceleration = None
        self.publish_waypoint_path()
        self.path_timer = node.create_timer(1.0, self.publish_waypoint_path)


    def emit(self, publisher, message):
        """Keep existing topics and provide one display with explicit colors."""
        publisher.publish(message)
        out = message if isinstance(message, MarkerArray) else MarkerArray(markers=[message])
        self.display_pub.publish(out)



    def publish_actual_motion(self, state, stamp):
        """Red dot and direction from measured map-position displacement.

        Neither predicted motion, steering commands nor body yaw sets this arrow.
        A short measurement window suppresses localization noise near standstill.
        """
        xy = np.asarray(state[:2], dtype=float)
        if self.motion_history:
            dt = stamp - self.motion_history[-1][0]
            jump = np.linalg.norm(xy - self.motion_history[-1][1])
            if dt <= 0 or dt > .6 or jump > max(.5, 2*self.node.config.MAX_SPEED*dt+.15):
                self.motion_history.clear()
        self.motion_history.append((stamp, xy.copy()))
        now = self.node.get_clock().now().to_msg()
        color = (0.9,0.05,0.08,1.0)
        dot = self.make_marker('actual_position',0,Marker.SPHERE,color,now)
        dot.pose.position.x=float(xy[0]);dot.pose.position.y=float(xy[1]);dot.pose.position.z=.16
        dot.scale.x=dot.scale.y=dot.scale.z=.09
        trail = self.make_marker('actual_trail',0,Marker.LINE_STRIP,(0.,0.,0.,0.),now)
        trail.action=Marker.DELETE  # Clear old red history lines.
        arrow = self.make_marker('actual_direction',0,Marker.ARROW,color,now)
        arrow.action=Marker.DELETE
        earlier = [sample for sample in self.motion_history if .18 <= stamp-sample[0] <= .5]
        if earlier:
            at, origin = earlier[-1]
            delta=xy-origin;distance=float(np.linalg.norm(delta));speed=distance/(stamp-at)
            if distance>.025 and speed>.08 and float(state[3])>.05:
                tip=xy+delta/distance*float(np.clip(.25+.2*speed,.3,.8))
                arrow.action=Marker.ADD;arrow.scale.x=.025;arrow.scale.y=.075;arrow.scale.z=.10
                arrow.points=[Point(x=float(q[0]),y=float(q[1]),z=.16) for q in (xy,tip)]
        mode=self.make_marker('control_mode',0,Marker.TEXT_VIEW_FACING,(.15,.25,.4,1.),now)
        mode.pose.position.x=float(xy[0]);mode.pose.position.y=float(xy[1]);mode.pose.position.z=.6
        mode.scale.z=.12;mode.text='MPPI'
        for marker in (dot,trail,arrow,mode):
            marker.header.frame_id=self.node.config.map_frame
            marker.lifetime.nanosec=350_000_000
        self.emit(self.actual_pub,MarkerArray(markers=[dot,trail,arrow,mode]))

    def publish_telemetry(self, odom, ref_path, command, acceleration):
        # Scalar comparisons: vector.x = target, vector.y = feedback, vector.z = x - y.
        # Units: speed m/s, acceleration m/s^2, steering rad. Use odometry sample time.
        stamp = odom.header.stamp
        time = stamp.sec + stamp.nanosec * 1e-9
        twist = odom.twist.twist
        speed = math.hypot(twist.linear.x, twist.linear.y)
        measured_acceleration = float('nan')
        if self.previous_sample is not None:
            previous_time, previous_speed = self.previous_sample
            dt = time - previous_time
            if 1e-4 < dt <= 0.5 and math.isfinite(speed):
                raw = (speed - previous_speed) / dt
                if self.filtered_acceleration is None:
                    self.filtered_acceleration = raw
                else:
                    self.filtered_acceleration += dt / (0.15 + dt) * (
                        raw - self.filtered_acceleration
                    )
                measured_acceleration = self.filtered_acceleration
            else:
                self.filtered_acceleration = None
        self.previous_sample = (time, speed) if math.isfinite(speed) else None

        # Bicycle-model estimate, not measured wheel angle; unreliable with slip.
        # Leave gaps below 0.5 m/s instead of displaying a false zero angle.
        steering = float('nan')
        if speed >= 0.5 and math.isfinite(speed) and math.isfinite(twist.angular.z):
            steering = math.atan(self.node.config.WB * twist.angular.z / speed)
        target_acceleration = (
            float(acceleration[0]) if acceleration is not None else float('nan')
        )
        comparisons = {
            'speed': (float(ref_path[0, 3]), speed),
            'acceleration': (target_acceleration, measured_acceleration),
            'steering_estimate': (float(command.drive.steering_angle), steering),
        }
        for name, (target, feedback) in comparisons.items():
            message = Vector3Stamped()
            message.header.stamp = stamp
            message.vector.x = target
            message.vector.y = feedback
            message.vector.z = target - feedback
            self.telemetry_pubs[name].publish(message)

    def publish_waypoint_path(self):
        self.mode_pub.publish(String(data='MPPI'))
        marker=self.make_marker('global_path',0,Marker.LINE_LIST,(0.22,0.25,0.29,1.0),self.node.get_clock().now().to_msg())
        marker.header.frame_id=self.node.config.map_frame
        marker.scale.x=0.025
        # Dashes are measured in metres, independent of CSV waypoint density.
        route=np.vstack((self.waypoints,self.waypoints[0]));progress=0.0
        for a,b in zip(route[:-1],route[1:]):
            delta=b-a;length=float(np.linalg.norm(delta))
            if length<1e-9:continue
            at=0.0
            while at<length-1e-9:
                phase=(progress+at)%0.65
                span=min(length-at,(0.40-phase) if phase<0.40 else (0.65-phase))
                if span<1e-9:span=min(length-at,1e-8)
                if phase<0.40:
                    for d in (at,at+span):
                        q=a+delta*(d/length)
                        marker.points.append(Point(x=float(q[0]),y=float(q[1]),z=0.015))
                at+=span
            progress+=length
        self.emit(self.path_pub, marker)

    @staticmethod
    def make_marker(namespace, marker_id, marker_type, color, stamp):
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = stamp
        marker.ns = namespace
        marker.id = marker_id
        marker.type = marker_type
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.color.r = float(color[0])
        marker.color.g = float(color[1])
        marker.color.b = float(color[2])
        marker.color.a = float(color[3])
        return marker

    def publish_trajectory(self,publisher,namespace,xs,ys,color,line_width,point_size,height):
        stamp=self.node.get_clock().now().to_msg()
        line=self.make_marker(namespace,0,Marker.LINE_STRIP,color,stamp)
        points=self.make_marker(namespace,1,Marker.SPHERE_LIST,color,stamp)
        endpoint=self.make_marker(namespace,2,Marker.SPHERE,color,stamp)
        line.scale.x=line_width
        points.scale.x=points.scale.y=points.scale.z=point_size
        endpoint.scale.x=endpoint.scale.y=endpoint.scale.z=point_size*2.2
        for marker in (line,points,endpoint):
            marker.header.frame_id=self.node.config.map_frame
            marker.lifetime.nanosec=500_000_000
        if xs is None or ys is None or len(xs)==0 or len(ys)==0:
            for marker in (line,points,endpoint):marker.action=Marker.DELETE
        else:
            line.points=[Point(x=float(x),y=float(y),z=height) for x,y in zip(xs,ys)]
            points.points=list(line.points)
            endpoint.pose.position=line.points[-1]
        self.emit(publisher,MarkerArray(markers=[line,points,endpoint]))

    def publish_reference(self,ref_path):
        self.publish_trajectory(self.reference_pub,'reference_trajectory',ref_path[:,0],ref_path[:,1],(0.0,0.45,0.85,1.0),0.018,0.035,0.07)

    def publish_prediction(self,ox,oy):
        self.publish_trajectory(self.prediction_pub,'predicted_trajectory',ox,oy,(1.0,0.55,0.0,1.0),0.028,0.065,0.10)


def canonical_frame(name):
    """TF2 frame names have no leading slash; topic names are unaffected."""
    return str(name).strip().lstrip('/')


def waypoint_file(path,track,package_share):
    """Resolve CSV names against this package, independent of shell cwd."""
    candidate=FilePath(path) if path else FilePath(f'{track}.csv')
    return candidate if candidate.is_absolute() else FilePath(package_share)/'waypoints'/candidate


def load_waypoints(path):
    rows=[]
    with open(path,newline='',encoding='utf-8-sig') as f:
        for line,row in enumerate(csv.reader(f),1):
            if not row or not row[0].strip() or row[0].lstrip().startswith('#'): continue
            try: values=[float(v) for v in row]
            except ValueError as e: raise ValueError(f'{path}:{line}: nonnumeric waypoint') from e
            if len(values)<3 or not np.isfinite(values).all():
                raise ValueError(f'{path}:{line}: need finite x,y,v (optional s,yaw,kappa,ax)')
            rows.append(values[:3])
    a=np.asarray(rows)
    if a.ndim!=2 or len(a)<3 or np.any(a[:,2]<0): raise ValueError('Invalid waypoint route')
    keep=np.r_[True,np.linalg.norm(np.diff(a[:,:2],axis=0),axis=1)>1e-7]; a=a[keep]
    if len(a)>3 and np.linalg.norm(a[-1,:2]-a[0,:2])<1e-7: a=a[:-1]
    if len(a)<3: raise ValueError('Route needs three distinct points')
    d=np.roll(a[:,:2],-1,axis=0)-a[:,:2]
    return np.column_stack((a[:,:2],np.arctan2(d[:,1],d[:,0]),a[:,2]))


def yaw(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))


def seconds(stamp):
    return stamp.sec+stamp.nanosec*1e-9


def realcar_config():
    """Fixed NVIDIA interfaces and installation geometry, outside tuning launch."""
    return replace(Config(), **{'track': 'race', 'waypoints_path': 'race.csv', 'map_frame': 'map', 'odom_topic': '/pf/pose/odom', 'odom_pose_frame': 'laser', 'pose_to_rear_axle_x_m': -0.27, 'pose_to_rear_axle_y_m': 0.0, 'scan_topic': '/scan', 'scan_min_valid_range_m': 0.05, 'drive_topic': '/drive', 'grid_size_m': 12.0, 'collision_step_m': 0.04, 'INTEGRATOR': 'euler', 'max_control_latency_s': 0.15, 'scan_timeout_s': 0.25, 'odom_timeout_s': 0.2, 'scan_pose_tolerance_s': 0.08, 'clear_confirmations': 3})


class MPPINode(Node):

    def __init__(self, realcar=False):
        super().__init__('mppi_node')
        defaults = realcar_config() if realcar else Config()
        overrides = {}
        for f in fields(defaults):
            v = getattr(defaults, f.name)
            self.declare_parameter(f.name, list(v) if isinstance(v, tuple) else v)
            value = self.get_parameter(f.name).value
            overrides[f.name] = tuple(value) if isinstance(v, tuple) else value
        overrides['map_frame'] = canonical_frame(overrides['map_frame'])
        overrides['odom_pose_frame'] = canonical_frame(overrides['odom_pose_frame'])
        if not overrides['map_frame']:
            raise ValueError('map_frame must not be empty')
        self.cfg = replace(defaults, **overrides).validate()
        c = self.cfg
        path = waypoint_file(c.waypoints_path, c.track, get_package_share_directory('rrt_mppi'))
        self.waypoints = load_waypoints(path)
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self)
        self.latest_odom = None
        self.visualization = None
        self.config = c
        self.state = None
        self.odom_received = 0.0
        self.odom_stamp = None
        self.history = deque(maxlen=300)
        self.pending_scans = deque(maxlen=12)
        self.grid = None
        self.origin = None
        self.grid_received = 0.0
        self.grid_stamp = None
        self.path = None
        self.path_time = 0.0
        self.controller = MPPI(c)
        self.confirmed = 0
        self.last_confirm_stamp = None
        self.last_status = 'initializing'
        self.last_steer = 0.0
        self.last_route_index = None
        size = max(40, int(math.ceil(c.grid_size_m / c.grid_resolution_m)))
        warm_grid = np.zeros((size, size), np.int8)
        origin = np.array([-c.grid_size_m / 2] * 2)
        warm_path = np.column_stack((np.linspace(0, 2, 80), np.zeros(80), np.zeros(80)))
        self.controller.solve(np.zeros(4), warm_path, 0.5, warm_grid, origin)
        self.controller.reset()
        path_clear(warm_path, warm_grid, origin, c.grid_resolution_m, c.geometry())
        scan_grid(np.full(8, 5.0), -math.pi, math.pi / 4, 0.05, 5.0, np.zeros(3), np.zeros(3), origin, size, c.grid_resolution_m, c.geometry())
        self.drive = self.create_publisher(AckermannDriveStamped, '/rrt_mppi/drive_candidate', 1)
        self.status = self.create_publisher(String, '/rrt_mppi/status', 1)
        self.grid_pub = self.create_publisher(OccupancyGrid, '/rrt_mppi/local_grid', 1)
        self.path_pubs = {name: self.create_publisher(Path, f'/rrt_mppi/{name}', 1) for name in ('reference', 'prediction')}
        self.body_pub = self.create_publisher(Marker, '/rrt_mppi/footprint', 1)
        self.global_pub = self.create_publisher(Path, '/rrt_mppi/global_path', QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.create_subscription(Odometry, c.odom_topic, self.odom, qos_profile_sensor_data)
        self.create_subscription(LaserScan, c.scan_topic, self.scan, qos_profile_sensor_data)
        self.visualization = MPPIVisualization(self, self.waypoints[:, :2]) if c.visualize else None
        self.create_timer(1 / c.control_rate_hz, self.tick)
        self.publish_path(self.global_pub, np.vstack((self.waypoints, self.waypoints[:1])))
        self.get_logger().info(f'Loaded {len(self.waypoints)} points: {path}; {json.dumps(overrides)}')

    def transform_pose(self, pose, frame, stamp):
        target = canonical_frame(self.cfg.map_frame)
        source = canonical_frame(frame)
        if not source:
            raise TransformException('Odometry.header.frame_id is empty')
        if source == target:
            return pose
        t = self.tf.lookup_transform(target, source, Time.from_msg(stamp)).transform
        a = yaw(t.rotation)
        ca, sa = (math.cos(a), math.sin(a))
        return np.array([t.translation.x + ca * pose[0] - sa * pose[1], t.translation.y + sa * pose[0] + ca * pose[1], wrap(pose[2] + a)])

    def odom(self, msg):
        p = msg.pose.pose
        state = np.array([p.position.x, p.position.y, yaw(p.orientation)])
        try:
            state = self.transform_pose(state, msg.header.frame_id, msg.header.stamp)
        except TransformException:
            return
        a = state[2]
        c = self.cfg
        state[0] += math.cos(a) * c.pose_to_rear_axle_x_m - math.sin(a) * c.pose_to_rear_axle_y_m
        state[1] += math.sin(a) * c.pose_to_rear_axle_x_m + math.cos(a) * c.pose_to_rear_axle_y_m
        speed = math.hypot(msg.twist.twist.linear.x, msg.twist.twist.linear.y)
        state = np.r_[state, speed]
        stamp = seconds(msg.header.stamp)
        if not np.isfinite(state).all():
            return
        if self.odom_stamp is not None and stamp < self.odom_stamp:
            self.history.clear()
            self.pending_scans.clear()
            self.grid_stamp = None
            self.grid = None
            self.path = None
            self.confirmed = 0
            self.controller.reset()
            self.last_route_index = None
        self.latest_odom = msg
        self.state = state
        self.odom_stamp = stamp
        self.odom_received = time.monotonic()
        self.history.append((stamp, state.copy()))
        if c.visualize and self.visualization is not None:
            self.visualization.publish_actual_motion(state, stamp)

    def scan(self, msg):
        self.pending_scans.append((msg, time.monotonic()))

    def build_grid(self):
        if not self.pending_scans or not self.history:
            return
        c = self.cfg
        now = time.monotonic()
        chosen = None
        for msg, received in reversed(self.pending_scans):
            stamp = seconds(msg.header.stamp)
            if self.grid_stamp is not None and stamp <= self.grid_stamp or now - received >= c.scan_timeout_s:
                continue
            times = np.array([item[0] for item in self.history])
            index = int(np.searchsorted(times, stamp))
            if index == 0:
                if times[0] - stamp > c.scan_pose_tolerance_s:
                    continue
                rear = self.history[0][1][:3].copy()
            elif index >= len(times):
                if stamp - times[-1] > c.scan_pose_tolerance_s:
                    continue
                rear = self.history[-1][1][:3].copy()
            else:
                ta, sa = self.history[index - 1]
                tb, sb = self.history[index]
                f = (stamp - ta) / max(tb - ta, 1e-09)
                rear = sa[:3] + f * (sb[:3] - sa[:3])
                rear[2] = sa[2] + f * wrap(sb[2] - sa[2])
            try:
                pose_frame = canonical_frame(c.odom_pose_frame or getattr(getattr(self, 'latest_odom', None), 'child_frame_id', ''))
                scan_frame = canonical_frame(msg.header.frame_id)
                if not scan_frame:
                    continue
                if pose_frame and pose_frame != canonical_frame(c.map_frame):
                    if pose_frame == scan_frame:
                        tx = ty = rotation = 0.0
                    else:
                        t = self.tf.lookup_transform(pose_frame, scan_frame, Time()).transform
                        tx, ty, rotation = (t.translation.x, t.translation.y, yaw(t.rotation))
                    dx = tx - c.pose_to_rear_axle_x_m
                    dy = ty - c.pose_to_rear_axle_y_m
                    ca, sa = (math.cos(rear[2]), math.sin(rear[2]))
                    laser = np.array([rear[0] + ca * dx - sa * dy, rear[1] + sa * dx + ca * dy, wrap(rear[2] + rotation)])
                else:
                    t = self.tf.lookup_transform(canonical_frame(c.map_frame), scan_frame, Time.from_msg(msg.header.stamp)).transform
                    laser = np.array([t.translation.x, t.translation.y, yaw(t.rotation)])
            except TransformException:
                continue
            chosen = (msg, received, stamp, rear, laser)
            break
        if chosen is None:
            return
        msg, received, stamp, rear, laser = chosen
        n = int(math.ceil(c.grid_size_m / c.grid_resolution_m))
        origin = np.floor((rear[:2] - n * c.grid_resolution_m / 2) / c.grid_resolution_m) * c.grid_resolution_m
        self.grid = scan_grid(np.asarray(msg.ranges, dtype=float), float(msg.angle_min), float(msg.angle_increment), max(float(msg.range_min), c.scan_min_valid_range_m), float(msg.range_max), laser, rear, origin, n, c.grid_resolution_m, c.geometry())
        self.origin = origin
        self.grid_received = received
        self.grid_stamp = stamp
        self.pending_scans = deque(((scan, arrival) for scan, arrival in self.pending_scans if seconds(scan.header.stamp) > stamp and now - arrival < c.scan_timeout_s), maxlen=12)
        if c.visualize:
            out = OccupancyGrid()
            out.header.frame_id = c.map_frame
            out.header.stamp = msg.header.stamp
            out.info.resolution = c.grid_resolution_m
            out.info.width = n
            out.info.height = n
            out.info.origin.position.x = float(origin[0])
            out.info.origin.position.y = float(origin[1])
            out.info.origin.orientation.w = 1.0
            out.data = self.grid.ravel().tolist()
            self.grid_pub.publish(out)

    def route_reference(self):
        w = self.waypoints
        n = len(w)
        indices = np.arange(n) if self.last_route_index is None else (self.last_route_index + np.arange(-10, min(n, 100))) % n
        i = int(indices[np.argmin(np.linalg.norm(w[indices, :2] - self.state[:2], axis=1))])
        if np.linalg.norm(w[i, :2] - self.state[:2]) > 3:
            i = int(np.argmin(np.linalg.norm(w[:, :2] - self.state[:2], axis=1)))
        self.last_route_index = i
        ref = csv_local_reference(w, i, self.cfg.reference_distance_m)
        return (ref, min(self.cfg.MAX_SPEED, float(w[i, 3]) * self.cfg.speed_scale))

    def fresh(self):
        now = time.monotonic()
        ros = self.get_clock().now().nanoseconds * 1e-09
        c = self.cfg
        return self.state is not None and self.grid is not None and (now - self.odom_received < c.odom_timeout_s) and (now - self.grid_received < c.scan_timeout_s) and (-0.05 <= ros - self.odom_stamp < c.odom_timeout_s) and (-0.05 <= ros - self.grid_stamp < c.scan_timeout_s)

    def stop(self, reason):
        self.confirmed = 0
        self.last_confirm_stamp = None
        self.controller.reset()
        out = AckermannDriveStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.drive.steering_angle = float(self.last_steer)
        out.drive.acceleration = -self.cfg.BRAKE_DECEL
        self.drive.publish(out)
        self.report(reason, self.diagnostics())
        if self.visualization is not None:
            self.visualization.publish_prediction([], [])
            self.visualization.publish_reference(np.empty((0, 4)))
        if self.cfg.visualize:
            self.publish_path(self.path_pubs['prediction'], np.empty((0, 3)))

    def diagnostics(self):
        now = time.monotonic()
        ros = self.get_clock().now().nanoseconds * 1e-09
        return {'odom_receive_age_ms': (now - self.odom_received) * 1000, 'scan_receive_age_ms': (now - self.grid_received) * 1000, 'odom_stamp_age_ms': None if self.odom_stamp is None else (ros - self.odom_stamp) * 1000, 'scan_stamp_age_ms': None if self.grid_stamp is None else (ros - self.grid_stamp) * 1000, 'reference_points': 0 if self.path is None else len(self.path)}

    def report(self, reason, extra):
        self.last_status = reason
        self.status.publish(String(data=json.dumps({'mode': 'MPPI', 'state': reason, **extra})))

    def tick(self):
        try:
            self.control()
        except Exception as e:
            self.stop('exception')
            self.get_logger().error(f'{type(e).__name__}: {e}')

    def control(self):
        began = time.monotonic()
        c = self.cfg
        self.build_grid()
        if not self.fresh():
            self.stop('stale_sensor_or_missing_tf')
            return
        state = self.state.copy()
        reference, speed = self.route_reference()
        self.path = reference[:, :3].copy()
        self.path_time = began
        if len(self.path) < 2:
            self.stop('no_csv_reference')
            return
        if c.visualize:
            self.publish_body(state)
        if self.grid_stamp != self.last_confirm_stamp:
            self.confirmed += 1
            self.last_confirm_stamp = self.grid_stamp
        if self.confirmed < c.clear_confirmations:
            count, stamp = (self.confirmed, self.last_confirm_stamp)
            self.stop('confirming_clear')
            self.confirmed = count
            self.last_confirm_stamp = stamp
            return
        action, ref, prediction, stats = self.controller.solve(state, self.path, speed, self.grid, self.origin)
        elapsed = time.monotonic() - began
        if action is None:
            self.stop('no_safe_rollout')
            return
        if elapsed > c.max_control_latency_s or not self.fresh():
            self.stop('control_deadline_or_stale')
            return
        command = AckermannDriveStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        command.drive.speed = float(np.clip(state[3] + action[0] * c.DT, 0, c.MAX_SPEED))
        command.drive.acceleration = float(action[0])
        command.drive.steering_angle = float(action[1])
        self.drive.publish(command)
        self.last_steer = float(action[1])
        self.controller.previous = action.copy()
        status = 'holding_safe_stop' if command.drive.speed < 0.05 and state[3] < 0.05 else 'tracking'
        self.report(status, {'control_ms': elapsed * 1000, **self.diagnostics(), **stats})
        if self.visualization is not None:
            self.visualization.publish_reference(ref)
            self.visualization.publish_prediction(prediction[:, 0], prediction[:, 1])
            self.visualization.publish_telemetry(self.latest_odom, ref, command, self.controller.U[:, 0])
        if c.visualize:
            for name, data in (('reference', ref), ('prediction', prediction)):
                self.publish_path(self.path_pubs[name], data)
            self.publish_body(state)

    def publish_path(self, publisher, data):
        msg = Path()
        msg.header.frame_id = self.cfg.map_frame
        msg.header.stamp = self.get_clock().now().to_msg()
        for row in data:
            p = PoseStamped()
            p.header = msg.header
            p.pose.position.x = float(row[0])
            p.pose.position.y = float(row[1])
            p.pose.orientation.z = math.sin(float(row[2]) / 2)
            p.pose.orientation.w = math.cos(float(row[2]) / 2)
            msg.poses.append(p)
        publisher.publish(msg)

    def publish_body(self, state):
        c = self.cfg
        m = Marker()
        m.header.frame_id = c.map_frame
        m.header.stamp = self.get_clock().now().to_msg()
        m.type = Marker.LINE_STRIP
        m.ns = 'inflated_body'
        m.pose.position.x = float(state[0] + c.car_body_center_x_m * math.cos(state[2]))
        m.pose.position.y = float(state[1] + c.car_body_center_x_m * math.sin(state[2]))
        m.pose.position.z = 0.09
        m.pose.orientation.z = math.sin(state[2] / 2)
        m.pose.orientation.w = math.cos(state[2] / 2)
        hl = c.car_length_m / 2 + c.footprint_margin_m
        hw = c.car_width_m / 2 + c.footprint_margin_m
        m.points = [Point(x=float(x), y=float(y), z=0.0) for x, y in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw), (-hl, -hw))]
        m.scale.x = 0.014
        m.color.r = 0.15
        m.color.g = 0.22
        m.color.b = 0.28
        m.color.a = 0.9
        m.lifetime.nanosec = 500000000
        self.body_pub.publish(m)
        if self.visualization is not None:
            self.visualization.display_pub.publish(MarkerArray(markers=[m]))

    def destroy_node(self):
        return super().destroy_node()


class DriveGuard(Node):
    def __init__(self):
        super().__init__('rrt_mppi_drive_guard')
        for name,value in {'drive_topic':'/drive','timeout_s':0.2,'max_speed':1.5,
                           'max_steer':0.4189,'brake_decel':2.0}.items():
            self.declare_parameter(name,value)
        self.command=None; self.received=0.; self.steer=0.
        self.pub=self.create_publisher(AckermannDriveStamped,self.get_parameter('drive_topic').value,1)
        self.create_subscription(AckermannDriveStamped,'/rrt_mppi/drive_candidate',self.receive,1)
        self.create_timer(.02,self.tick)

    def receive(self,msg):
        values=(msg.drive.speed,msg.drive.steering_angle,msg.drive.acceleration)
        if (not all(math.isfinite(x) for x in values) or msg.drive.speed<0 or
            msg.drive.speed>self.get_parameter('max_speed').value+1e-6 or
            abs(msg.drive.steering_angle)>self.get_parameter('max_steer').value+1e-6):
            self.command=None; return
        self.command=msg; self.received=time.monotonic()

    def tick(self):
        timeout=self.get_parameter('timeout_s').value
        stamp=self.command.header.stamp if self.command else None
        age=(self.get_clock().now().nanoseconds*1e-9-stamp.sec-stamp.nanosec*1e-9) if stamp else math.inf
        if self.command is not None and time.monotonic()-self.received<timeout and -.05<=age<timeout:
            out=self.command; self.steer=out.drive.steering_angle
        else:
            out=AckermannDriveStamped(); out.header.stamp=self.get_clock().now().to_msg()
            out.drive.steering_angle=self.steer
            out.drive.acceleration=-self.get_parameter('brake_decel').value
        self.pub.publish(out)


def main(args=None):
    import sys
    guard_mode='--drive-guard' in sys.argv
    if guard_mode: sys.argv.remove('--drive-guard')
    realcar_mode='--realcar' in sys.argv
    if realcar_mode:sys.argv.remove('--realcar')
    rclpy.init(args=args); node=None
    try:
        node=DriveGuard() if guard_mode else MPPINode(realcar=realcar_mode)
        rclpy.spin(node)
    except (KeyboardInterrupt,rclpy.executors.ExternalShutdownException): pass
    finally:
        if node is not None:
            if not guard_mode and rclpy.ok(): node.stop('shutdown')
            node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__=='__main__':main()
