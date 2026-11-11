#!/usr/bin/env python3
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import numpy as np
import rclpy
from ackermann_msgs.msg import AckermannDriveStamped
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from utils import calc_interpolated_ref_trajectory

import csv
import math
import os
import time
from pathlib import Path
from dataclasses import fields, replace
from ament_index_python.packages import get_package_share_directory
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from scipy.spatial import cKDTree
from geometry_msgs.msg import Point, Vector3Stamped
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from visualization_msgs.msg import Marker, MarkerArray


@dataclass(frozen=True)
class MPPIConfig:
    # Immutable model/cost parameters; tuple-valued diagonal weights.
    NX: int = 4  # length of state vector: x = [p_x, p_y, yaw, v]
    NU: int = 2  # length of input vector: u = [a, delta]
    T: int = 1024  # number of sampled control sequences
    H: int = 20  # horizon length
    DT: float = 0.05  # time step [s]
    INTEGRATOR: str = 'euler' # "euler" or "rk4" (bonus)

    # ---------------------------------------------------
    # TODO: you may need to tune the following parameters
    LAMBDA: float = 0.1  # temperature
    U_STD: tuple = (1.0, 0.05)  # std of the sampled inputs [a, delta]
    Q: tuple = (10.0, 10.0, 0.5, 1.0)  # state error cost [x, y, yaw, v]
    Qf: tuple = (5.0, 5.0, 1.0, 1.0)  # final state error cost [x, y, yaw, v]
    R: tuple = (0.01, 5.0)  # input cost [a, delta]
    Rd: tuple = (0.01, 5.0)  # input difference cost [a, delta]
    # ---------------------------------------------------

    WB: float = 0.33  # Wheelbase [m]
    MIN_STEER: float = -0.4189  # minimum steering angle [rad]
    MAX_STEER: float = 0.4189  # maximum steering angle [rad]
    MIN_ACCEL: float = -4.0 # minimum acceleration [m/ss]
    MAX_ACCEL: float = 4.0 # maximum acceleration [m/ss]
    MIN_SPEED: float = 0.0  # minimum speed [m/s]
    MAX_SPEED: float = 10.0  # maximum speed [m/s]



def dynamics(x, u, cfg):
    """Kinematic bicycle derivatives, supporting leading sample dimensions."""
    x=np.asarray(x,dtype=float);u=np.asarray(u,dtype=float)
    return np.stack((x[...,3]*np.cos(x[...,2]),x[...,3]*np.sin(x[...,2]),
                     x[...,3]*np.tan(u[...,1])/cfg.WB,u[...,0]),axis=-1)



def step_euler(x, u, cfg):
    """
    Forward Euler step: x_{k+1} = x_k + f(x_k, u_k) * DT (README Section II.b.i)
    :return: next state, shape (NX,)
    """
    # TODO: fill in the Euler step
    return x + cfg.DT * dynamics(x, u, cfg)



def step_rk4(x, u, cfg):
    """
    Bonus: Runge-Kutta 4 step (README Section II.b.ii)
    :return: next state, shape (NX,)
    """
    # TODO: fill in the RK4 step
    k1 = dynamics(x, u, cfg)
    k2 = dynamics(x + 0.5 * cfg.DT * k1, u, cfg)
    k3 = dynamics(x + 0.5 * cfg.DT * k2, u, cfg)
    k4 = dynamics(x + cfg.DT * k3, u, cfg)
    return x + cfg.DT * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0



def step(x, u, cfg):
    """
    Discretized dynamics F(x, u): the state after DT, holding u constant
    """
    if cfg.INTEGRATOR == "rk4":
        return step_rk4(x, u, cfg)
    return step_euler(x, u, cfg)



def simulate(x0, U, cfg):
    """One sequence; first prediction point is the current measured state."""
    return rollout(x0,np.asarray(U)[None],cfg)[0]


def rollout(x0, U, cfg):
    """Vectorize across samples; iterate only over the horizon."""
    U=np.asarray(U,dtype=float)
    states=np.empty((U.shape[0],U.shape[1]+1,cfg.NX),dtype=float)
    states[:,0]=x0
    for t in range(U.shape[1]):states[:,t+1]=step(states[:,t],U[:,t],cfg)
    return states


def cost(X, U, ref, cfg, previous_steering=None):
    """Original Lab8 stage/terminal, input, slew and speed-violation costs."""
    X,U,ref=(np.asarray(a,dtype=float) for a in (X,U,ref))
    error=X[...,1:,:]-ref[...,1:,:]
    error[...,2]=np.arctan2(np.sin(error[...,2]),np.cos(error[...,2]))
    weights=np.broadcast_to(np.asarray(cfg.Q),error.shape).copy()
    weights[...,-1,:]=cfg.Qf
    result=np.sum(weights*error**2,axis=-1)+np.sum(np.asarray(cfg.R)*U**2,axis=-1)
    result[...,1:]+=np.sum(np.asarray(cfg.Rd)*np.diff(U,axis=-2)**2,axis=-1)
    if previous_steering is not None:result[...,0]+=cfg.Rd[1]*(U[...,0,1]-previous_steering)**2
    # Predictions may accelerate from rest. MIN_SPEED remains the CSV/output floor.
    # Keep the existing heavy penalty for reverse motion and overspeed.
    violation=np.maximum(X[...,1:,3]-cfg.MAX_SPEED,0.)+np.maximum(-X[...,1:,3],0.)
    return result+1000.*violation**2



def mppi_step(key, U, x0, ref, cfg, previous_steering=None, obstacle_cost=None):
    """Score each complete rollout and use one weight for its whole input sequence."""
    rng=np.random.default_rng(key)
    samples=np.asarray(U)[None]+rng.standard_normal((cfg.T,cfg.H,cfg.NU))*np.asarray(cfg.U_STD)
    samples=np.clip(samples,[cfg.MIN_ACCEL,cfg.MIN_STEER],[cfg.MAX_ACCEL,cfg.MAX_STEER])
    trajectories=rollout(x0,samples,cfg)
    costs=cost(trajectories,samples,ref,cfg,previous_steering)
    if obstacle_cost is not None:costs += obstacle_cost(trajectories[:,1:,:3])
    # One scalar total cost per sampled trajectory, including its terminal cost.
    totals=np.sum(costs,axis=1)
    normalized=(totals-totals.min())/(np.ptp(totals)+1e-6)
    trajectory_weights=np.exp(-normalized/cfg.LAMBDA)
    trajectory_weights/=trajectory_weights.sum()
    mean=np.sum(trajectory_weights[:,None,None]*samples,axis=0)
    # Preserve the existing (samples, horizon) visualization interface.
    # Every column now contains the same trajectory weights.
    weights=np.broadcast_to(trajectory_weights[:,None],(cfg.T,cfg.H))
    return mean,trajectories,weights


def forward_scan_mask(angles, half_angle_deg):
    """Select beams within the configured angle on each side of laser +X."""
    wrapped = np.arctan2(np.sin(angles), np.cos(angles))
    return np.abs(wrapped) <= np.deg2rad(half_angle_deg) + 1e-7


class LidarSoftCost:
    """Only a finite proximity cost from real scan returns; no collision mask,
    no occupancy grid/boundary, no braking test and no command override.
    Four disks conservatively cover the configured car body, as before.
    """
    def __init__(self, scan, laser_pose, rear_pose, max_range, weight, clearance, margin, half_angle_deg=45.0):
        ranges=np.asarray(scan.ranges,dtype=float)
        angles=scan.angle_min+np.arange(len(ranges))*scan.angle_increment
        usable=(np.isfinite(ranges)&(ranges>=scan.range_min))|np.isposinf(ranges)
        if len(ranges)<3 or np.count_nonzero(usable)<3:
            raise ValueError('No usable LiDAR measurements')
        hit=usable&np.isfinite(ranges)&(ranges<scan.range_max)&(ranges<=max_range)
        hit &= forward_scan_mask(angles, half_angle_deg)
        points=np.column_stack((ranges[hit]*np.cos(angles[hit]),ranges[hit]*np.sin(angles[hit])))
        c,t=np.cos(laser_pose[2]),np.sin(laser_pose[2])
        points=points@np.array([[c,t],[-t,c]])+laser_pose[:2]
        d=points-rear_pose[:2];c,t=np.cos(rear_pose[2]),np.sin(rear_pose[2])
        bx=c*d[:,0]+t*d[:,1]-.1651;by=-t*d[:,0]+c*d[:,1]
        points=points[(np.abs(bx)>.575/2)|(np.abs(by)>.305/2)]
        self.tree=cKDTree(points) if len(points) else None
        self.centers=.1651-.575/2+(np.arange(4)+.5)*.575/4
        self.radius=math.hypot(.575/8,.305/2)+margin
        self.weight=weight;self.buffer=clearance

    def __call__(self, poses):
        if self.tree is None:return np.zeros(poses.shape[:-1])
        x=poses[...,0,None]+np.cos(poses[...,2,None])*self.centers
        y=poses[...,1,None]+np.sin(poses[...,2,None])*self.centers
        query=np.stack((x,y),axis=-1)
        distances=self.tree.query(query.reshape(-1,2),workers=1)[0].reshape(x.shape)
        gap=distances.min(axis=-1)-self.radius
        return self.weight*np.maximum(1.-gap/self.buffer,0.)**2


def resolve_waypoint_path(value, track, package_share):
    name=value or ('Spielberg.csv' if track=='spielberg' else f'{track}.csv')
    path=Path(name).expanduser()
    return path if path.is_absolute() else Path(package_share)/'waypoints'/path



def state_from_odom(message, map_frame, offset_x, offset_y):
    if message.header.frame_id.lstrip('/')!=map_frame.lstrip('/'):
        raise ValueError('Odometry must be expressed in the route map frame')
    p=message.pose.pose;q=p.orientation
    yaw=math.atan2(2.*(q.w*q.z+q.x*q.y),1.-2.*(q.y*q.y+q.z*q.z))
    velocity=message.twist.twist.linear
    state=np.array([p.position.x+math.cos(yaw)*offset_x-math.sin(yaw)*offset_y,
                    p.position.y+math.sin(yaw)*offset_x+math.cos(yaw)*offset_y,
                    yaw,math.hypot(velocity.x,velocity.y)])
    if not np.isfinite(state).all():raise ValueError('Nonfinite odometry')
    return state



class MPPI(Node):
    """
    Implement Kinematic MPPI on the car
    This is just a template, you are free to implement your own node!
    """
    def __init__(self):
        super().__init__('mppi_node')
        # launch/levine_launch.py sets track:=levine, launch/spielberg_launch.py track:=spielberg
        self.declare_parameter('track', 'race')
        track = self.get_parameter('track').value

        #       use MPPI as a tracker (similar to pure pursuit)
        #       os.path.join(get_package_share_directory('mppi'), 'waypoints', <your csv>)
        #       (ament_index_python.packages). A path like /home/you/... only exists on your laptop.
        self.declare_parameter('waypoints_path', '')
        csv_path = self.get_parameter('waypoints_path').value
        csv_path=resolve_waypoint_path(csv_path,track,get_package_share_directory('mppi'))
        rows = []
        with open(csv_path, newline='', encoding='utf-8') as file:
            for row in csv.reader(file):
                if not row or not row[0].strip() or row[0].lstrip().startswith('#'):
                    continue
                rows.append([float(row[0]), float(row[1]),
                             float(row[4]), float(row[2])])
        self.waypoints = np.asarray(rows, dtype=float)
        if (self.waypoints.ndim != 2 or len(self.waypoints) < 3
                or not np.all(np.isfinite(self.waypoints))):
            raise ValueError('Waypoints need at least three finite [x, y, yaw, v] rows')
        if np.any(np.linalg.norm(np.diff(self.waypoints[:, :2], axis=0), axis=1) < 1e-8):
            raise ValueError('Consecutive waypoint positions must be distinct')
        for name,default in [('odom_topic','/pf/pose/odom' if track=='race' else '/ego_racecar/odom'),('drive_topic','/drive'),
                             ('map_frame','map'),('pose_to_rear_axle_x_m',-0.27),
                             ('pose_to_rear_axle_y_m',0.0),('odom_timeout_s',0.25)]:
            self.declare_parameter(name,default)
        self.map_frame=self.get_parameter('map_frame').value.lstrip('/')
        self.pose_x=float(self.get_parameter('pose_to_rear_axle_x_m').value)
        self.pose_y=float(self.get_parameter('pose_to_rear_axle_y_m').value)
        self.odom_timeout=float(self.get_parameter('odom_timeout_s').value)
        if (not self.map_frame or not np.isfinite([self.pose_x,self.pose_y,self.odom_timeout]).all()
                or self.odom_timeout<=0):
            raise ValueError('Invalid real-car frame, offset or timeout')
        self.drive_pub=self.create_publisher(AckermannDriveStamped,self.get_parameter('drive_topic').value,10)
        self.pose_sub=self.create_subscription(Odometry,self.get_parameter('odom_topic').value,
                                               self.odom_callback,qos_profile_sensor_data)
        self.last_odom_received=None
        self.pose_history=deque(maxlen=100)
        self.scan_msg=None;self.scan_received=None;self.soft_cache=None
        for name,default in [('obstacle_avoidance',True),('scan_topic','/scan'),
                ('scan_timeout_s',.25),('obstacle_range_m',2.0),('obstacle_half_angle_deg',45.0),
                ('obstacle_weight',100.0),
                ('obstacle_clearance_m',.01),('footprint_margin_m',0.03)]:
            self.declare_parameter(name,default)
        self.use_lidar=bool(self.get_parameter('obstacle_avoidance').value)
        self.scan_timeout=float(self.get_parameter('scan_timeout_s').value)
        self.obstacle_range=float(self.get_parameter('obstacle_range_m').value)
        self.obstacle_half_angle=float(self.get_parameter('obstacle_half_angle_deg').value)
        if not np.isfinite(self.obstacle_half_angle) or not 0 < self.obstacle_half_angle <= 180:
            raise ValueError('obstacle_half_angle_deg must be in (0, 180]')
        self.obstacle_weight=float(self.get_parameter('obstacle_weight').value)
        self.obstacle_clearance=float(self.get_parameter('obstacle_clearance_m').value)
        self.footprint_margin=float(self.get_parameter('footprint_margin_m').value)
        if (not np.isfinite([self.scan_timeout,self.obstacle_range,self.obstacle_weight,
                            self.obstacle_clearance,self.footprint_margin]).all()
                or min(self.scan_timeout,self.obstacle_range,self.obstacle_clearance)<=0
                or min(self.obstacle_weight,self.footprint_margin)<0):
            raise ValueError('Invalid LiDAR soft cost parameters')
        if self.use_lidar:
            self.scan_sub=self.create_subscription(LaserScan,self.get_parameter('scan_topic').value,
                self.scan_callback,qos_profile_sensor_data)
        self.declare_parameter('visualize', True)
        self.visualize = self.get_parameter('visualize').value
        self.declare_parameter('visualize_samples', False)
        self.visualize_samples = self.get_parameter('visualize_samples').value
        self.get_logger().info(f'Loaded {len(rows)} waypoints from {csv_path}')

        self.config = MPPIConfig()
        overrides = {}
        for field in fields(self.config):
            if field.name in ('NX', 'NU'):
                continue
            default = getattr(self.config, field.name)
            self.declare_parameter(field.name, list(default) if isinstance(default, tuple) else default)
            value = self.get_parameter(field.name).value
            overrides[field.name] = tuple(value) if isinstance(default, tuple) else value
        self.config = replace(self.config, **overrides)
        cfg = self.config
        if (cfg.H < 1 or cfg.T < 2 or not np.isfinite(cfg.DT) or cfg.DT <= 0
                or not np.isfinite(cfg.LAMBDA) or cfg.LAMBDA <= 0
                or not np.isfinite(cfg.WB) or cfg.WB <= 0
                or cfg.INTEGRATOR not in ('euler', 'rk4')):
            raise ValueError('Invalid MPPI horizon, sampling, dynamics or integrator parameters')
        for name, size in (('Q', 4), ('Qf', 4), ('R', 2), ('Rd', 2), ('U_STD', 2)):
            value = np.asarray(getattr(cfg, name))
            if value.shape != (size,) or not np.all(np.isfinite(value)) or np.any(value < 0):
                raise ValueError(f'{name} must contain {size} finite nonnegative values')
        for lower, upper in ((cfg.MIN_ACCEL, cfg.MAX_ACCEL),
                             (cfg.MIN_STEER, cfg.MAX_STEER),
                             (cfg.MIN_SPEED, cfg.MAX_SPEED)):
            if not np.isfinite([lower, upper]).all() or lower >= upper:
                raise ValueError('Invalid MPPI limits')
        # Print the resolved cost weights once on startup.
        for name in ("Q", "Qf", "R", "Rd"):
            self.get_logger().info(f"{name!r}: {list(getattr(cfg, name))},")
        self.waypoints[:, 3] = np.clip(self.waypoints[:, 3], cfg.MIN_SPEED, cfg.MAX_SPEED)
        self.U = np.zeros((self.config.H, self.config.NU))  # mean control sequence
        self.key = np.random.default_rng(0)
        self.last_steering = 0.0
        self.latest_odom = None

        # Exercise the NumPy kernel before starting the timer.
        mppi_step(self.key, self.U, np.zeros(self.config.NX),
                  np.zeros((self.config.H + 1, self.config.NX)), self.config,
                  np.asarray(self.last_steering))

        self.visualization = (MPPIVisualization(self, self.waypoints[:, :2])
                              if self.visualize else None)
        self.control_timer = self.create_timer(self.config.DT, self.control_callback)

    def odom_callback(self, odom_msg):
        self.latest_odom=odom_msg
        self.last_odom_received=time.monotonic()
        try:
            state=state_from_odom(odom_msg,self.map_frame,self.pose_x,self.pose_y)
            stamp=odom_msg.header.stamp.sec+odom_msg.header.stamp.nanosec*1e-9
            if self.pose_history and stamp<self.pose_history[-1][0]:self.pose_history.clear()
            self.pose_history.append((stamp,state[:3]))
        except ValueError:pass

    def scan_callback(self,msg):
        self.scan_msg=msg;self.scan_received=time.monotonic()

    def scan_soft_cost(self):
        msg=self.scan_msg
        if msg is None or self.scan_received is None:raise ValueError('Waiting for LiDAR')
        stamp=msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9
        age=self.get_clock().now().nanoseconds*1e-9-stamp
        if not -.05<=age<=self.scan_timeout or time.monotonic()-self.scan_received>self.scan_timeout:
            raise ValueError('LiDAR data expired')
        if msg.header.frame_id.lstrip('/')!='laser':
            raise ValueError('This real-car profile expects scan frame laser')
        if self.soft_cache is not None and self.soft_cache[0] is msg:return self.soft_cache[1]
        history=list(self.pose_history)
        if not history:raise ValueError('Waiting for localization')
        times=np.array([v[0] for v in history]);k=int(np.searchsorted(times,stamp))
        nearest=min(max(k,0),len(history)-1)
        if k>0 and abs(times[k-1]-stamp)<abs(times[nearest]-stamp):nearest=k-1
        if abs(times[nearest]-stamp)>.08:raise ValueError('LiDAR/localization timestamps differ')
        rear=history[nearest][1].copy()
        if 0<k<len(history) and times[k]>times[k-1]:
            f=(stamp-times[k-1])/(times[k]-times[k-1]);a,b=history[k-1][1],history[k][1]
            rear=a+f*(b-a);rear[2]=a[2]+f*math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
        # PF pose origin is the laser; undo the optional rear-axle shift.
        c,t=np.cos(rear[2]),np.sin(rear[2])
        laser=rear.copy();laser[0]-=c*self.pose_x-t*self.pose_y;laser[1]-=t*self.pose_x+c*self.pose_y
        result=LidarSoftCost(msg,laser,rear,self.obstacle_range,self.obstacle_weight,
                             self.obstacle_clearance,self.footprint_margin,self.obstacle_half_angle)
        self.soft_cache=(msg,result)
        return result

    def destroy_node(self):
        self.control_timer.cancel()
        if self.visualization is not None:
            self.visualization.samples_worker.shutdown(wait=True,cancel_futures=True)
        return super().destroy_node()

    def publish_stop(self):
        command=AckermannDriveStamped();command.header.stamp=self.get_clock().now().to_msg()
        self.drive_pub.publish(command)
        self.U=np.zeros_like(self.U);self.last_steering=0.
        if self.visualization is not None:
            self.visualization.publish_reference(np.empty((0,4)))
            self.visualization.publish_prediction([],[])

    def control_callback(self):
        began=time.monotonic()
        odom_msg=self.latest_odom
        if self.last_odom_received is None or began-self.last_odom_received>self.odom_timeout:
            self.publish_stop();return
        if odom_msg is None:return
        self.latest_odom=None
        stamp=odom_msg.header.stamp.sec+odom_msg.header.stamp.nanosec*1e-9
        age=self.get_clock().now().nanoseconds*1e-9-stamp
        if not -.05<=age<=self.odom_timeout:
            self.publish_stop();return
        try:x0=state_from_odom(odom_msg,self.map_frame,self.pose_x,self.pose_y)
        except ValueError as error:
            self.get_logger().error(str(error));self.publish_stop();return
        speed=x0[3]
        obstacle_cost=None
        if self.use_lidar:
            try:obstacle_cost=self.scan_soft_cost()
            except ValueError as error:
                self.get_logger().warning(str(error),throttle_duration_sec=2.)
                self.publish_stop();return

        #       with the current vehicle state.
        #       ref_x, ref_y, ref_yaw, ref_v are columns of self.waypoints
        ref = self.calc_ref_trajectory(x0, *self.waypoints.T)
        if self.visualization is not None:
            self.visualization.publish_reference(ref)

        #       step, so shift self.U one step forward (drop the first input
        #       and repeat the last one)
        warm_start = np.concatenate((self.U[1:], self.U[-1:]), axis=0)

        # a new random key at every step, so MPPI draws new samples
        subkey = self.key
        self.U, trajectories, weights = mppi_step(
            subkey, warm_start, np.asarray(x0), np.asarray(ref), self.config,
            np.asarray(self.last_steering),obstacle_cost)
        effective_samples=1.0/float(np.sum(weights[:,0]**2))
        self.get_logger().info(
            f'MPPI effective samples: {effective_samples:.1f}/{self.config.T} '
            f'({100.0*effective_samples/self.config.T:.1f}%)', throttle_duration_sec=1.0)


        action = np.asarray(self.U[0])
        command = AckermannDriveStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        if np.all(np.isfinite(action)):
            next_speed = np.clip(speed + action[0] * self.config.DT,
                                 self.config.MIN_SPEED, self.config.MAX_SPEED)
            command.drive.speed = float(next_speed)
            command.drive.acceleration = float(action[0])
            command.drive.steering_angle = float(action[1])
        else:
            self.U = np.zeros_like(self.U)
            self.get_logger().error('MPPI produced a nonfinite action; stopping')
        self.drive_pub.publish(command)
        self.last_steering = float(command.drive.steering_angle)

        if self.visualization is not None:
            nominal = np.asarray(self.visualization.predict(
                np.asarray(x0), self.U, self.config))
            self.visualization.publish_prediction(nominal[:, 0], nominal[:, 1])
            self.visualization.publish_telemetry(
                odom_msg, ref, command, self.U[:, 0])
            if self.visualize_samples:
                self.visualization.queue_samples(trajectories, weights)

    def calc_ref_trajectory(self, x0, cx, cy, cyaw, cv):
        """
        Calculate interpolated reference trajectory for H steps: [x, y, yaw, v]

        :param x0: current state [p_x, p_y, yaw, v]
        :param cx: Course X-Position
        :param cy: Course y-Position
        :param cyaw: Course Heading
        :param cv: speed profile
        :return: reference trajectory ref (H+1 x NX)
        """
        return calc_interpolated_ref_trajectory(
            x0[0], x0[1],
            cx, cy, cyaw, cv,
            self.config.DT,
            self.config.H
        )


class MPPIVisualization:
    """Publish the global CSV path and the two current MPPI trajectories."""

    def __init__(self, node, waypoints):
        self.predict = simulate
        self.node = node
        self.waypoints = waypoints
        path_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.path_pub = node.create_publisher(
            Marker, '/mppi/global_path', path_qos
        )
        self.reference_pub = node.create_publisher(
            MarkerArray, '/mppi/reference_trajectory', 1
        )
        self.prediction_pub = node.create_publisher(
            MarkerArray, '/mppi/predicted_trajectory', 1
        )
        self.telemetry_pubs = {
            name: node.create_publisher(Vector3Stamped, f'/mppi/telemetry/{name}', 10)
            for name in ('speed', 'acceleration', 'steering_estimate')
        }
        self.sample_pub = (node.create_publisher(
            MarkerArray, '/mppi/sampled_rollouts', 1)
            if node.visualize_samples else None)
        node.declare_parameter('visualize_sample_count', 0)
        node.declare_parameter('visualize_samples_hz', 1.0)
        self.sample_count = int(node.get_parameter('visualize_sample_count').value)
        self.samples_hz = float(node.get_parameter('visualize_samples_hz').value)
        if self.sample_count < 0 or not np.isfinite(self.samples_hz) or not 0 < self.samples_hz <= 10:
            raise ValueError('Invalid sampled trajectory display count/rate')
        self.samples_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='mppi_viz')
        self.samples_pending = None
        self.last_samples_ns = None
        self.previous_sample = None
        self.filtered_acceleration = None
        self.publish_waypoint_path()
        self.path_timer = node.create_timer(1.0, self.publish_waypoint_path)
        self.scan_range_pub = node.create_publisher(
            Marker, '/mppi/obstacle_scan_range', path_qos)
        self.scan_range_timer = node.create_timer(0.2, self.publish_scan_range)




    def publish_scan_range(self):
        """Display scan coverage only; never modify obstacle costs or commands."""
        node = self.node
        marker = self.make_marker('obstacle_scan_range', 0, Marker.LINE_STRIP,
                                  (0.4, 0.4, 0.4, 1.0), node.get_clock().now().to_msg())
        marker.header.frame_id = node.map_frame
        marker.scale.x = 0.025
        marker.lifetime.nanosec = 600_000_000
        marker.action = Marker.DELETE
        scan = node.scan_msg
        if node.use_lidar and scan is not None and node.scan_received is not None:
            stamp = scan.header.stamp.sec + scan.header.stamp.nanosec * 1e-9
            age = node.get_clock().now().nanoseconds * 1e-9 - stamp
            history = list(node.pose_history)
            fresh = (-0.05 <= age <= node.scan_timeout and
                     time.monotonic() - node.scan_received <= node.scan_timeout)
            if fresh and history and scan.header.frame_id.lstrip('/') == 'laser':
                times = np.array([entry[0] for entry in history])
                k = int(np.searchsorted(times, stamp))
                nearest = min(k, len(history) - 1)
                if k > 0 and abs(times[k-1]-stamp) < abs(times[nearest]-stamp):
                    nearest = k-1
                if abs(times[nearest]-stamp) <= 0.08 and len(scan.ranges) > 1:
                    pose = history[nearest][1].copy()
                    if 0 < k < len(history) and times[k] > times[k-1]:
                        f = (stamp-times[k-1])/(times[k]-times[k-1])
                        a, b = history[k-1][1], history[k][1]
                        pose = a + f*(b-a)
                        pose[2] = a[2] + f*math.atan2(math.sin(b[2]-a[2]), math.cos(b[2]-a[2]))
                    c, s = math.cos(pose[2]), math.sin(pose[2])
                    origin = pose[:2] - [c*node.pose_x-s*node.pose_y, s*node.pose_x+c*node.pose_y]
                    radius = min(node.obstacle_range, scan.range_max)
                    beam_angles = scan.angle_min + np.arange(len(scan.ranges))*scan.angle_increment
                    selected = beam_angles[forward_scan_mask(beam_angles, node.obstacle_half_angle)]
                    selected = np.arctan2(np.sin(selected), np.cos(selected))
                    if np.isfinite(radius) and radius > 0 and len(selected) > 1:
                        start, end = float(selected.min()), float(selected.max())
                        full_circle = end-start >= 2*math.pi-math.radians(1)
                        angles = np.linspace(start, end, 121)
                        xy = radius*np.column_stack((np.cos(angles), np.sin(angles)))
                        xy = xy @ np.array([[c, s], [-s, c]]) + origin
                        if not full_circle:
                            xy = np.vstack((origin, xy, origin))
                        marker.points = [Point(x=float(x), y=float(y), z=0.08) for x, y in xy]
                        marker.action = Marker.ADD
        self.scan_range_pub.publish(marker)

    def queue_samples(self, trajectories, weights):
        if self.samples_pending is not None and not self.samples_pending.done():
            return  # Drop a display frame; never queue old visualization jobs.
        if self.samples_pending is not None and self.samples_pending.exception() is not None:
            self.node.get_logger().warning('Sample visualization failed: ' + str(self.samples_pending.exception()))
        self.samples_pending = self.samples_worker.submit(self.publish_samples,trajectories,weights)

    def publish_samples(self, trajectories, weights):
        now = self.node.get_clock().now().nanoseconds
        if (self.sample_pub is None or (self.last_samples_ns is not None
                and now - self.last_samples_ns < int(1e9/self.samples_hz))):
            return
        self.last_samples_ns = now
        count = self.node.config.T if self.sample_count == 0 else min(self.sample_count,self.node.config.T)
        indices = np.linspace(0,self.node.config.T-1,count,dtype=int)
        paths = np.asarray(trajectories[indices])
        scores = np.asarray(weights[indices, 0])
        scores = scores / max(float(scores.max()), 1e-8)
        stamp = self.node.get_clock().now().to_msg()
        markers = MarkerArray()
        for index, (path, score) in enumerate(zip(paths, scores)):
            marker = self.make_marker(
                'sampled_rollouts', index, Marker.LINE_STRIP,
                (float(1-score),float(score),.1,.3), stamp)
            marker.header.frame_id = self.node.map_frame
            marker.scale.x = 0.01
            marker.lifetime.sec = int(2/self.samples_hz)
            marker.lifetime.nanosec = int((2/self.samples_hz % 1)*1e9)
            marker.points = [Point(x=float(p[0]), y=float(p[1]), z=0.03)
                             for p in path]
            markers.markers.append(marker)
        self.sample_pub.publish(markers)

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
        # Keep the closed-loop waypoint order from the Pure Pursuit publisher.
        path = self.make_marker(
            'global_path', 0, Marker.LINE_STRIP,
            (0.43, 0.34, 0.93, 1.0),
            self.node.get_clock().now().to_msg(),
        )
        path.header.frame_id = self.node.map_frame
        path.scale.x = 0.18

        for x, y in np.vstack((self.waypoints, self.waypoints[0])):
            point = Point()
            point.x = float(x)
            point.y = float(y)
            point.z = 0.02
            path.points.append(point)

        self.path_pub.publish(path)

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

    def publish_trajectory(self, publisher, namespace, xs, ys, color,
                           line_width, point_size, height):
        stamp = self.node.get_clock().now().to_msg()
        line = self.make_marker(
            namespace, 0, Marker.LINE_STRIP, color, stamp
        )
        points = self.make_marker(
            namespace, 1, Marker.SPHERE_LIST, color, stamp
        )
        line.scale.x = line_width
        points.scale.x = point_size
        points.scale.y = point_size
        points.scale.z = point_size

        # Stable namespace/IDs replace the previous horizon instead of trailing it.
        # Expire dynamic markers if updates stop; keep the global path persistent.
        for marker in (line, points):
            marker.header.frame_id = self.node.map_frame
            marker.lifetime.sec = 0
            marker.lifetime.nanosec = 500_000_000

        if xs is None or ys is None or len(xs) == 0 or len(ys) == 0:
            line.action = Marker.DELETE
            points.action = Marker.DELETE
        else:
            for x, y in zip(xs, ys):
                point = Point()
                point.x = float(x)
                point.y = float(y)
                point.z = height
                line.points.append(point)
                points.points.append(point)

        markers = MarkerArray()
        markers.markers = [line, points]
        publisher.publish(markers)

    def publish_reference(self, ref_path):
        self.publish_trajectory(
            self.reference_pub, 'reference_trajectory',
            ref_path[:, 0], ref_path[:, 1],
            (1.0, 0.1, 0.1, 1.0), 0.07, 0.12, 0.04,
        )

    def publish_prediction(self, ox, oy):
        self.publish_trajectory(
            self.prediction_pub, 'predicted_trajectory', ox, oy,
            (0.1, 1.0, 0.2, 1.0), 0.045, 0.085, 0.06,
        )

def main(args=None):
    rclpy.init(args=args)
    print("MPPI Initialized")
    mppi_node = MPPI()
    try:
        rclpy.spin(mppi_node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl-C: stop quietly
    finally:
        mppi_node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
