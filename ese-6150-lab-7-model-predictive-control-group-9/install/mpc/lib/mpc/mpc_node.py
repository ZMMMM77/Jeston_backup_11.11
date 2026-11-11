#!/usr/bin/env python3
import math
from dataclasses import dataclass, field

import csv
import os
from ament_index_python.packages import get_package_share_directory
from nav_msgs.msg import Odometry

import cvxpy
import numpy as np
import rclpy
from ackermann_msgs.msg import AckermannDrive, AckermannDriveStamped
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from scipy.linalg import block_diag
from scipy.sparse import block_diag, csc_matrix, diags
from sensor_msgs.msg import LaserScan
from utils import nearest_point, calc_interpolated_ref_trajectory

# TODO CHECK: include needed ROS msg type headers and libraries
# Keep SciPy's sparse matrix output, including stored zeros used by CVXPY.
_sparse_block_diag = block_diag

def block_diag(mats, format=None, dtype=None):
    return _sparse_block_diag(
        (csc_matrix((0, 0)), *mats), format=format, dtype=dtype
    )


def load_waypoints(csv_path):
    points = []
    speeds = []
    curvatures = []
    yaws = []

    with open(csv_path, newline='', encoding='utf-8') as file:
        for row in csv.reader(file):
            if not row or row[0].strip().startswith('#'):
                continue

            points.append([float(row[0]), float(row[1])])
            speeds.append(float(row[2]))
            curvatures.append(float(row[5]))
            yaws.append(float(row[4]))

    return (
        np.asarray(points),
        np.asarray(speeds),
        np.asarray(curvatures),
        np.asarray(yaws),
    )

@dataclass
class mpc_config:
    NXK: int = 4  # length of kinematic state vector: z = [x, y, v, yaw]
    NU: int = 2  # length of input vector: u = = [steering speed, acceleration]
    TK: int = 8  # finite time horizon length kinematic

    # ---------------------------------------------------
    # TODO: you may need to tune the following matrices
    Rk: list = field(
        default_factory=lambda: np.diag([0.01, 100.0])
    )  # input cost matrix, penalty for inputs - [accel, steering_speed]
    Rdk: list = field(
        default_factory=lambda: np.diag([0.01, 600.0])
    )  # input difference cost matrix, penalty for change of inputs - [accel, steering_speed]
    Qk: list = field(
        default_factory=lambda: np.diag([13.5, 13.5, 5.5, 13.0])
    )  # state error cost matrix, for the the next (T) prediction time steps [x, y, delta, v, yaw, yaw-rate, beta]
    Qfk: list = field(
        default_factory=lambda: np.diag([13.5, 13.5, 5.5, 13.0])
    )  # final state error matrix, penalty  for the final state constraints: [x, y, delta, v, yaw, yaw-rate, beta]
    # ---------------------------------------------------

    N_IND_SEARCH: int = 20  # Search index number
    DTK: float = 0.1  # time step [s] kinematic
    dlk: float = 0.03  # dist step [m] kinematic
    LENGTH: float = 0.58  # Length of the vehicle [m]
    WIDTH: float = 0.31  # Width of the vehicle [m]
    WB: float = 0.33  # Wheelbase [m]
    MIN_STEER: float = -0.4189  # maximum steering angle [rad]
    MAX_STEER: float = 0.4189  # maximum steering angle [rad]
    MAX_DSTEER: float = np.deg2rad(180.0)  # maximum steering speed [rad/s]
    MAX_SPEED: float = 12.0  # maximum speed [m/s]
    MIN_SPEED: float = 0.0  # minimum backward speed [m/s]
    MAX_ACCEL: float = 3.0  # maximum acceleration [m/ss]


@dataclass
class State:
    x: float = 0.0
    y: float = 0.0
    delta: float = 0.0
    v: float = 0.0
    yaw: float = 0.0
    yawrate: float = 0.0
    beta: float = 0.0

class MPC(Node):
    """ 
    Implement Kinematic MPC on the car
    This is just a template, you are free to implement your own node!
    """
    def __init__(self):
        super().__init__('mpc_node')
        # launch/levine_launch.py sets track:=levine, launch/spielberg_launch.py track:=spielberg
        self.declare_parameter('track', 'levine')
        track = self.get_parameter('track').value

        # TODO: create ROS subscribers and publishers
        #       use the MPC as a tracker (similar to pure pursuit)
        # TODO: load the waypoints of `track` from the package's installed waypoints/ folder:
        #       os.path.join(get_package_share_directory('mpc'), 'waypoints', <your csv>)
        #       (ament_index_python.packages). A path like /home/you/... only exists on your laptop.
        csv_path = os.path.join(
            get_package_share_directory('mpc'),
            'waypoints',
            'Spielberg.csv' if track == 'spielberg' else f'{track}.csv',
        )
        (
            self.waypoints,
            self.waypoint_speeds,
            self.waypoint_curvatures,
            self.waypoint_yaws,
        ) = load_waypoints(csv_path)
        self.get_logger().info(
            f"Loaded {len(self.waypoints)} waypoints from {csv_path}"
        )

        self.config = mpc_config()

        # Read the launch speed limit before building the MPC constraints.
        self.declare_parameter('max_speed', self.config.MAX_SPEED)
        max_speed = float(self.get_parameter('max_speed').value)
        if not math.isfinite(max_speed) or max_speed <= self.config.MIN_SPEED:
            raise ValueError('max_speed must be finite and greater than MIN_SPEED')
        self.config.MAX_SPEED = max_speed
        self.waypoint_speeds = np.clip(
            self.waypoint_speeds, self.config.MIN_SPEED, max_speed
        )
        self.get_logger().info(f'Maximum speed: {max_speed} m/s')

        # Read diagonal cost weights supplied by the selected launch file.
        for name in ('Rk', 'Rdk', 'Qk', 'Qfk'):
            default_weights = np.diag(getattr(self.config, name)).tolist()
            self.declare_parameter(name, default_weights)
            weights = np.asarray(self.get_parameter(name).value, dtype=float)
            if (
                weights.shape != (len(default_weights),)
                or not np.all(np.isfinite(weights))
                or np.any(weights < 0.0)
            ):
                raise ValueError(
                    f'{name} must contain {len(default_weights)} finite, nonnegative weights'
                )
            setattr(self.config, name, np.diag(weights))
            self.get_logger().info(f'{name}: {weights.tolist()}')

        self.odelta_v = None
        self.odelta = None
        self.oa = None
        self.init_flag = 0

        # Keep the last published steering command for inter-cycle continuity.
        self.last_steering = 0.0
        self.last_steering_stamp_ns = None

        # initialize MPC problem
        self.mpc_prob_init()
        self.drive_pub = self.create_publisher(
            AckermannDriveStamped,
            '/drive',
            10,
        )

        self.pose_sub = self.create_subscription(
            Odometry,
            '/ego_racecar/odom',
            self.odom_callback,
            10,
        )

        self.visualization = MPCVisualization(self, self.waypoints)

    def odom_callback(self, odom_msg):
        pass
        # TODO: extract pose from ROS msg
        pose = odom_msg.pose.pose
        q = pose.orientation

        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y ** 2 + q.z ** 2),
        )

        velocity = odom_msg.twist.twist.linear
        speed = math.hypot(velocity.x, velocity.y)

        vehicle_state = State(
            x=pose.position.x,
            y=pose.position.y,
            v=speed,
            yaw=yaw,
        )

        # TODO: Calculate the next reference trajectory for the next T steps
        #       with current vehicle pose.
        #       ref_x, ref_y, ref_yaw, ref_v are columns of self.waypoints
        ref_x = self.waypoints[:, 0]
        ref_y = self.waypoints[:, 1]
        ref_yaw = self.waypoint_yaws
        ref_v = self.waypoint_speeds
        ref_path = self.calc_ref_trajectory(vehicle_state, ref_x, ref_y, ref_yaw, ref_v)

        ref_path[3, :] = np.unwrap(ref_path[3, :])

        yaw_offset = 2.0 * math.pi * round(
            (vehicle_state.yaw - ref_path[3, 0]) / (2.0 * math.pi)
        )
        ref_path[3, :] += yaw_offset
        self.visualization.publish_reference(ref_path)
        x0 = [vehicle_state.x, vehicle_state.y, vehicle_state.v, vehicle_state.yaw]

        # TODO: solve the MPC control problem
        (
            self.oa,
            self.odelta_v,
            ox,
            oy,
            oyaw,
            ov,
            state_predict,
        ) = self.linear_mpc_control(ref_path, x0, self.oa, self.odelta_v)
        self.visualization.publish_prediction(ox, oy)

        # TODO: publish drive message.
        command = AckermannDriveStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        if self.oa is None or self.odelta_v is None:
            self.drive_pub.publish(command)
            self.last_steering = float(command.drive.steering_angle)
            self.last_steering_stamp_ns = self.get_clock().now().nanoseconds
            self.visualization.publish_telemetry(
                odom_msg, ref_path, command, self.oa
            )
            self.get_logger().warn("MPC returned no valid solution")
            return
        steer_output = self.odelta_v[0]
        speed_output = vehicle_state.v + self.oa[0] * self.config.DTK
        command.drive.steering_angle = float(np.clip(
            steer_output,
            self.config.MIN_STEER,
            self.config.MAX_STEER,
        ))
        command.drive.speed = float(np.clip(
            speed_output,
            self.config.MIN_SPEED,
            self.config.MAX_SPEED,
        ))
        self.drive_pub.publish(command)
        self.last_steering = float(command.drive.steering_angle)
        self.last_steering_stamp_ns = self.get_clock().now().nanoseconds
        self.visualization.publish_telemetry(
            odom_msg, ref_path, command, self.oa
        )

    def mpc_prob_init(self):
        """
        Create MPC quadratic optimization problem using cvxpy, solver: OSQP
        Will be solved every iteration for control.
        More MPC problem information here: https://osqp.org/docs/examples/mpc.html
        More QP example in CVXPY here: https://www.cvxpy.org/examples/basic/quadratic_program.html
        """
        # Initialize and create vectors for the optimization problem
        # Vehicle State Vector
        self.xk = cvxpy.Variable(
            (self.config.NXK, self.config.TK + 1)
        )
        # Control Input vector
        self.uk = cvxpy.Variable(
            (self.config.NU, self.config.TK)
        )
        objective = 0.0  # Objective value of the optimization problem
        constraints = []  # Create constraints array

        # Initialize reference vectors
        self.x0k = cvxpy.Parameter((self.config.NXK,))
        self.x0k.value = np.zeros((self.config.NXK,))

        # Connect the first predicted steering angle to the last command.
        self.previous_steering_k = cvxpy.Parameter(value=0.0)
        self.first_steering_change_limit_k = cvxpy.Parameter(
            nonneg=True, value=self.config.MAX_DSTEER * self.config.DTK
        )

        # Initialize reference trajectory parameter
        self.ref_traj_k = cvxpy.Parameter((self.config.NXK, self.config.TK + 1))
        self.ref_traj_k.value = np.zeros((self.config.NXK, self.config.TK + 1))

        # Initializes block diagonal form of R = [R, R, ..., R] (NU*T, NU*T)
        R_block = block_diag(tuple([self.config.Rk] * self.config.TK))

        # Initializes block diagonal form of Rd = [Rd, ..., Rd] (NU*(T-1), NU*(T-1))
        Rd_block = block_diag(tuple([self.config.Rdk] * (self.config.TK - 1)))

        # Initializes block diagonal form of Q = [Q, Q, ..., Qf] (NX*T, NX*T)
        Q_block = [self.config.Qk] * (self.config.TK)
        Q_block.append(self.config.Qfk)
        Q_block = block_diag(tuple(Q_block))

        # Formulate and create the finite-horizon optimal control problem (objective function)
        # The FTOCP has the horizon of T timesteps

        # --------------------------------------------------------
        # TODO: fill in the objectives here, you should be using cvxpy.quad_form() somehwhere
        
        # TODO: Objective part 1: Influence of the control inputs: Inputs u multiplied by the penalty R
        objective += cvxpy.quad_form(
            cvxpy.vec(self.uk, order='F'),
            R_block,)
        # TODO: Objective part 2: Deviation of the vehicle from the reference trajectory weighted by Q, including final Timestep T weighted by Qf
        objective += cvxpy.quad_form(
            cvxpy.vec(self.xk - self.ref_traj_k, order='F'),
            Q_block,)
        # TODO: Objective part 3: Difference from one control input to the next control input weighted by Rd
        objective += cvxpy.quad_form(
            cvxpy.vec(self.uk[:, 1:] - self.uk[:, :-1], order='F'),
            Rd_block,)
        # Apply the same steering-change weight across control cycles.
        objective += self.config.Rdk[1, 1] * cvxpy.square(
            self.uk[1, 0] - self.previous_steering_k
        )
        # --------------------------------------------------------

        # Constraints 1: Calculate the future vehicle behavior/states based on the vehicle dynamics model matrices
        # Evaluate vehicle Dynamics for next T timesteps
        A_block = []
        B_block = []
        C_block = []
        # init path to zeros
        path_predict = np.zeros((self.config.NXK, self.config.TK + 1))
        for t in range(self.config.TK):
            A, B, C = self.get_model_matrix(
                path_predict[2, t], path_predict[3, t], 0.0
            )
            A_block.append(A)
            B_block.append(B)
            C_block.extend(C)

        A_block = block_diag(tuple(A_block))
        B_block = block_diag(tuple(B_block))
        C_block = np.array(C_block)

        # [AA] Sparse matrix to CVX parameter for proper stuffing
        # Reference: https://github.com/cvxpy/cvxpy/issues/1159#issuecomment-718925710
        m, n = A_block.shape
        self.Annz_k = cvxpy.Parameter(A_block.nnz)
        data = np.ones(self.Annz_k.size)
        rows = A_block.row * n + A_block.col
        cols = np.arange(self.Annz_k.size)
        Indexer = csc_matrix((data, (rows, cols)), shape=(m * n, self.Annz_k.size))

        # Setting sparse matrix data
        self.Annz_k.value = A_block.data

        # Now we use this sparse version instead of the old A_ block matrix
        self.Ak_ = cvxpy.reshape(Indexer @ self.Annz_k, (m, n), order="C")

        # Same as A
        m, n = B_block.shape
        self.Bnnz_k = cvxpy.Parameter(B_block.nnz)
        data = np.ones(self.Bnnz_k.size)
        rows = B_block.row * n + B_block.col
        cols = np.arange(self.Bnnz_k.size)
        Indexer = csc_matrix((data, (rows, cols)), shape=(m * n, self.Bnnz_k.size))
        self.Bk_ = cvxpy.reshape(Indexer @ self.Bnnz_k, (m, n), order="C")
        self.Bnnz_k.value = B_block.data

        # No need for sparse matrices for C as most values are parameters
        self.Ck_ = cvxpy.Parameter(C_block.shape)
        self.Ck_.value = C_block

        # -------------------------------------------------------------
        # TODO: Constraint part 1:
        #       Add dynamics constraints to the optimization problem
        #       This constraint should be based on a few variables:
        #       self.xk, self.Ak_, self.Bk_, self.uk, and self.Ck_
        constraints += [
            cvxpy.vec(self.xk[:, 1:], order='F')== self.Ak_ @ cvxpy.vec(self.xk[:, :-1], order='F')
            + self.Bk_ @ cvxpy.vec(self.uk, order='F')
            + self.Ck_]
        # TODO: Constraint part 2:
        #       Add constraints on steering, change in steering angle
        #       cannot exceed steering angle speed limit. Should be based on:
        #       self.uk, self.config.MAX_DSTEER, self.config.DTK
        constraints += [
            cvxpy.abs(self.uk[1, 1:] - self.uk[1, :-1])
            <= self.config.MAX_DSTEER * self.config.DTK]
        # Limit the first steering change from the last published command.
        constraints += [
            cvxpy.abs(self.uk[1, 0] - self.previous_steering_k)
            <= self.first_steering_change_limit_k
        ]
        # TODO: Constraint part 3:
        #       Add constraints on upper and lower bounds of states and inputs
        #       and initial state constraint, should be based on:
        #       self.xk, self.x0k, self.config.MAX_SPEED, self.config.MIN_SPEED,
        #       self.uk, self.config.MAX_ACCEL, self.config.MAX_STEER
        constraints += [
            self.xk[:, 0] == self.x0k,
            self.xk[2, :] >= self.config.MIN_SPEED,
            self.xk[2, :] <= self.config.MAX_SPEED,
            cvxpy.abs(self.uk[0, :]) <= self.config.MAX_ACCEL,
            self.uk[1, :] >= self.config.MIN_STEER,
            self.uk[1, :] <= self.config.MAX_STEER,]
        # -------------------------------------------------------------

        # Create the optimization problem in CVXPY and setup the workspace
        # Optimization goal: minimize the objective function
        self.MPC_prob = cvxpy.Problem(cvxpy.Minimize(objective), constraints)

    def calc_ref_trajectory(self, state, cx, cy, cyaw, sp):
        """
        Calculate interpolated reference trajectory for T steps: [x, y, v, yaw]

        Uses proper linear interpolation between waypoints based on velocity
        propagation, rather than snapping to discrete waypoint indices.

        :param state: Current vehicle state
        :param cx: Course X-Position
        :param cy: Course y-Position
        :param cyaw: Course Heading
        :param sp: speed profile
        :return: reference trajectory ref_traj (NXK x TK+1)
        """
        return calc_interpolated_ref_trajectory(
            state.x, state.y,
            cx, cy, sp, cyaw,
            self.config.DTK,
            self.config.TK
        )

    def predict_motion(self, x0, oa, od, xref):
        path_predict = xref * 0.0
        for i, _ in enumerate(x0):
            path_predict[i, 0] = x0[i]

        state = State(x=x0[0], y=x0[1], yaw=x0[3], v=x0[2])
        for (ai, di, i) in zip(oa, od, range(1, self.config.TK + 1)):
            state = self.update_state(state, ai, di)
            path_predict[0, i] = state.x
            path_predict[1, i] = state.y
            path_predict[2, i] = state.v
            path_predict[3, i] = state.yaw

        return path_predict

    def update_state(self, state, a, delta):

        # input check
        if delta >= self.config.MAX_STEER:
            delta = self.config.MAX_STEER
        elif delta <= -self.config.MAX_STEER:
            delta = -self.config.MAX_STEER

        state.x = state.x + state.v * math.cos(state.yaw) * self.config.DTK
        state.y = state.y + state.v * math.sin(state.yaw) * self.config.DTK
        state.yaw = (
            state.yaw + (state.v / self.config.WB) * math.tan(delta) * self.config.DTK
        )
        state.v = state.v + a * self.config.DTK

        if state.v > self.config.MAX_SPEED:
            state.v = self.config.MAX_SPEED
        elif state.v < self.config.MIN_SPEED:
            state.v = self.config.MIN_SPEED

        return state

    def get_model_matrix(self, v, phi, delta):
        """
        Calc linear and discrete time dynamic model-> Explicit discrete time-invariant
        Linear System: Xdot = Ax +Bu + C
        State vector: x=[x, y, v, yaw]
        :param v: speed
        :param phi: heading angle of the vehicle
        :param delta: steering angle: delta_bar
        :return: A, B, C
        """

        # State (or system) matrix A, 4x4
        A = np.zeros((self.config.NXK, self.config.NXK))
        A[0, 0] = 1.0
        A[1, 1] = 1.0
        A[2, 2] = 1.0
        A[3, 3] = 1.0
        A[0, 2] = self.config.DTK * math.cos(phi)
        A[0, 3] = -self.config.DTK * v * math.sin(phi)
        A[1, 2] = self.config.DTK * math.sin(phi)
        A[1, 3] = self.config.DTK * v * math.cos(phi)
        A[3, 2] = self.config.DTK * math.tan(delta) / self.config.WB

        # Input Matrix B; 4x2
        B = np.zeros((self.config.NXK, self.config.NU))
        B[2, 0] = self.config.DTK
        B[3, 1] = self.config.DTK * v / (self.config.WB * math.cos(delta) ** 2)

        C = np.zeros(self.config.NXK)
        C[0] = self.config.DTK * v * math.sin(phi) * phi
        C[1] = -self.config.DTK * v * math.cos(phi) * phi
        C[3] = -self.config.DTK * v * delta / (self.config.WB * math.cos(delta) ** 2)

        return A, B, C

    def mpc_prob_solve(self, ref_traj, path_predict, x0):
        self.x0k.value = x0

        # Use elapsed command time for the inter-cycle steering rate limit.
        now_ns = self.get_clock().now().nanoseconds
        control_dt = self.config.DTK
        if self.last_steering_stamp_ns is not None:
            control_dt = max(
                0.0, (now_ns - self.last_steering_stamp_ns) * 1e-9
            )
        self.previous_steering_k.value = self.last_steering
        self.first_steering_change_limit_k.value = (
            self.config.MAX_DSTEER * control_dt
        )

        A_block = []
        B_block = []
        C_block = []
        for t in range(self.config.TK):
            A, B, C = self.get_model_matrix(
                path_predict[2, t], path_predict[3, t], 0.0
            )
            A_block.append(A)
            B_block.append(B)
            C_block.extend(C)

        A_block = block_diag(tuple(A_block))
        B_block = block_diag(tuple(B_block))
        C_block = np.array(C_block)

        self.Annz_k.value = A_block.data
        self.Bnnz_k.value = B_block.data
        self.Ck_.value = C_block

        self.ref_traj_k.value = ref_traj

        # Solve the optimization problem in CVXPY
        # Solver selections: cvxpy.OSQP; cvxpy.GUROBI
        self.MPC_prob.solve(solver=cvxpy.OSQP, verbose=False, warm_start=True)

        if (
            self.MPC_prob.status == cvxpy.OPTIMAL
            or self.MPC_prob.status == cvxpy.OPTIMAL_INACCURATE
        ):
            ox = np.array(self.xk.value[0, :]).flatten()
            oy = np.array(self.xk.value[1, :]).flatten()
            ov = np.array(self.xk.value[2, :]).flatten()
            oyaw = np.array(self.xk.value[3, :]).flatten()
            oa = np.array(self.uk.value[0, :]).flatten()
            odelta = np.array(self.uk.value[1, :]).flatten()

        else:
            print("Error: Cannot solve mpc..")
            oa, odelta, ox, oy, oyaw, ov = None, None, None, None, None, None

        return oa, odelta, ox, oy, oyaw, ov

    def linear_mpc_control(self, ref_path, x0, oa, od):
        """
        MPC contorl with updating operational point iteraitvely
        :param ref_path: reference trajectory in T steps
        :param x0: initial state vector
        :param oa: acceleration of T steps of last time
        :param od: delta of T steps of last time
        """

        if oa is None or od is None:
            oa = [0.0] * self.config.TK
            od = [0.0] * self.config.TK

        # Call the Motion Prediction function: Predict the vehicle motion for x-steps
        path_predict = self.predict_motion(x0, oa, od, ref_path)
        poa, pod = oa[:], od[:]

        # Run the MPC optimization: Create and solve the optimization problem
        mpc_a, mpc_delta, mpc_x, mpc_y, mpc_yaw, mpc_v = self.mpc_prob_solve(
            ref_path, path_predict, x0
        )

        return mpc_a, mpc_delta, mpc_x, mpc_y, mpc_yaw, mpc_v, path_predict

# ==================== Visualization ====================
# Copy from pure_pursuit.py, but change the topic names to /mpc/...
from geometry_msgs.msg import Point, Vector3Stamped
from rclpy.qos import DurabilityPolicy, QoSProfile
from visualization_msgs.msg import Marker, MarkerArray


class MPCVisualization:
    """Publish the global CSV path and the two current MPC trajectories."""

    def __init__(self, node, waypoints):
        self.node = node
        self.waypoints = waypoints
        path_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.path_pub = node.create_publisher(
            Marker, '/mpc/global_path', path_qos
        )
        self.reference_pub = node.create_publisher(
            MarkerArray, '/mpc/reference_trajectory', 1
        )
        self.prediction_pub = node.create_publisher(
            MarkerArray, '/mpc/predicted_trajectory', 1
        )
        self.telemetry_pubs = {
            name: node.create_publisher(Vector3Stamped, f'/mpc/telemetry/{name}', 10)
            for name in ('speed', 'acceleration', 'steering_estimate')
        }
        self.previous_sample = None
        self.filtered_acceleration = None
        self.publish_waypoint_path()

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
            'speed': (float(ref_path[2, 0]), speed),
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
            ref_path[0, :], ref_path[1, :],
            (1.0, 0.1, 0.1, 1.0), 0.07, 0.12, 0.04,
        )

    def publish_prediction(self, ox, oy):
        # Use the optimized solution, rather than the nominal state_predict rollout.
        self.publish_trajectory(
            self.prediction_pub, 'predicted_trajectory', ox, oy,
            (0.1, 1.0, 0.2, 1.0), 0.045, 0.085, 0.06,
        )

def main(args=None):
    rclpy.init(args=args)
    print("MPC Initialized")
    mpc_node = MPC()
    try:
        rclpy.spin(mpc_node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl-C: stop quietly
    finally:
        mpc_node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
