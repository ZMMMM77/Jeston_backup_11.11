"""Vehicle velocity estimation from particle-filter poses and an IMU.

The real car's particle filter reports only a pose (x, y, yaw at base_link, the
rear axle). The drift policy also needs body-frame velocities vx, vy and the yaw
rate r. This module estimates them with NumPy only, so it can be tested without ROS
(drift repo: ``scripts/test_state_estimator.py``). Copied from the drift repo's
``drift_env/estimator.py``; keep the two in sync.

``ImuPoseEstimator`` (use this one on the car)
    The IMU drives the prediction at its own rate: the gyro integrates yaw and the
    accelerometer, rotated into the map frame, integrates velocity and position.
    Each PF pose corrects position and yaw. The filter also estimates accelerometer
    and gyro biases. PF poses arrive late (scan time + PF compute), so the filter
    keeps its state at the time of the last PF pose and replays the buffered IMU
    samples up to the requested time.

``PfOnlyEstimator`` (fallback, no IMU)
    A constant-acceleration Kalman filter on the PF positions and a [yaw, r] filter
    on the PF yaw. With 2 cm PF noise at 40 Hz the velocity error is about
    0.5 m/s on the figure eight, well above the 0.1 m/s the policy was trained with.

Both return ``EstimatedState`` with vx, vy at base_link
(``twist_point="base_link"`` in ``drift_env.state.from_odom``). Sign convention as
in ``drift_env.state``: x forward, y left, yaw and r counterclockwise positive.
"""
from bisect import bisect_right
from collections import deque
from dataclasses import dataclass
import math

import numpy as np


def wrap(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _rot(yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s], [s, c]])


@dataclass
class EstimatedState:
    t: float            # time the state refers to [s]
    x: float            # base_link (rear axle) position, map frame [m]
    y: float
    yaw: float          # [rad], wrapped to (-pi, pi]
    vx: float           # body-frame longitudinal speed at base_link [m/s]
    vy: float           # body-frame lateral speed at base_link [m/s]
    r: float            # yaw rate [rad/s]
    speed: float        # |v| at base_link [m/s]
    beta_rear: float    # rear-axle sideslip [rad]
    vel_std: float      # 1-sigma velocity uncertainty per axis [m/s]
    age: float          # time since the last accepted PF pose [s]


def _make_state(t, xy, v_world, yaw, r, vel_std, age, min_vx):
    c, s = math.cos(yaw), math.sin(yaw)
    vx = c * v_world[0] + s * v_world[1]
    vy = -s * v_world[0] + c * v_world[1]
    return EstimatedState(
        t=t, x=float(xy[0]), y=float(xy[1]), yaw=wrap(yaw), vx=float(vx), vy=float(vy),
        r=float(r), speed=float(math.hypot(vx, vy)),
        beta_rear=math.atan2(vy, max(abs(vx), min_vx)), vel_std=float(vel_std), age=age)


class _Gate:
    """Rejects PF jumps; after ``max_rejects`` in a row the caller re-initializes.

    A pose is a jump if it is farther than ``gate_m`` from the prediction. For the
    first ``warmup`` poses after a (re)start, when the velocity is still unknown,
    the gate also allows three times the predicted position uncertainty."""

    def __init__(self, gate_m, max_rejects, warmup=10):
        self.gate_m, self.max_rejects, self.warmup = gate_m, max_rejects, warmup
        self.rejects = self.total_rejects = self.resets = 0
        self.since_reset = 0
        self.last_innovation = 0.0

    def check(self, innov, pred_std=0.0) -> str:
        self.last_innovation = float(np.hypot(*innov))
        widen = 3.0 * pred_std if self.since_reset < self.warmup else 0.0
        if self.last_innovation <= self.gate_m + widen:
            self.rejects = 0
            self.since_reset += 1
            return "accept"
        self.rejects += 1
        self.total_rejects += 1
        return "reset" if self.rejects >= self.max_rejects else "reject"


# --------------------------------------------------------------------------- IMU
class ImuPoseEstimator:
    """IMU-driven velocity estimator corrected by PF poses.

    State, at the time of the last PF pose: position p (2), map-frame velocity v (2),
    accelerometer bias b_a (2, body frame); and separately yaw and gyro bias b_g.

    Inputs (all times in seconds on one clock, use the header stamps):
      update_imu(t, ax, ay, gz)  body-frame specific force [m/s^2] and yaw rate [rad/s],
                                 already in the car's axes (x forward, y left, z up)
                                 and with the startup bias removed
      update_pose(t, x, y, yaw)  PF pose of base_link in the map frame
      state_at(t)                state predicted to t
    """

    def __init__(self, pos_std=0.02, yaw_std=math.radians(1.0), acc_density=0.05,
                 acc_bias_walk=0.05, gyro_density=0.005, gyro_bias_walk=0.002,
                 imu_offset_x=0.0, gate_m=0.3, max_rejects=5, reset_dt=0.5,
                 max_predict_s=0.05, buffer_s=1.0, min_vx=0.3, r_extrapolate_s=0.02):
        self.r_extrapolate_s = r_extrapolate_s
        self.R_pos = pos_std ** 2
        self.R_yaw = yaw_std ** 2
        self.q_acc = acc_density ** 2       # accelerometer white noise density [(m/s^2)^2 / Hz]
        self.q_ba = acc_bias_walk ** 2
        self.q_g = gyro_density ** 2        # gyro white noise density [(rad/s)^2 / Hz]
        self.q_bg = gyro_bias_walk ** 2
        self.imu_offset_x = imu_offset_x    # IMU position ahead of base_link [m]
        self.gate = _Gate(gate_m, max_rejects)
        self.reset_dt = reset_dt
        self.max_predict_s = max_predict_s
        self.buffer_s = buffer_s
        self.min_vx = min_vx
        self.imu = deque()                  # (t, ax, ay, gz), increasing t
        self._imu_t = []                    # parallel list of times for bisect
        self.t = None
        self.X = np.zeros(6)                # px, py, vX, vY, bax, bay
        self.P = np.eye(6)
        self.Y = np.zeros(2)                # yaw, gyro bias
        self.PY = np.eye(2)

    @property
    def initialized(self):
        return self.t is not None

    @property
    def total_rejects(self):
        return self.gate.total_rejects

    @property
    def resets(self):
        return self.gate.resets

    # ---------------------------------------------------------------- inputs
    def update_imu(self, t, ax, ay, gz):
        if self.imu and t <= self.imu[-1][0]:
            return                          # duplicate or out-of-order sample
        self.imu.append((t, ax, ay, gz))
        self._imu_t.append(t)
        horizon = t - self.buffer_s
        if self.t is not None:
            horizon = min(horizon, self.t)
        # keep one sample at or before the anchor: it holds the IMU value after it
        while len(self.imu) > 2 and self.imu[1][0] <= horizon:
            self.imu.popleft()
            self._imu_t.pop(0)

    def update_pose(self, t, x, y, yaw) -> bool:
        """Add one PF pose. Returns False if it was rejected as a jump."""
        if self.t is None or t - self.t > self.reset_dt:
            self._reset(t, x, y, yaw, keep_velocity=False)
            return True
        if t <= self.t:
            return False
        X, P, Y, PY = self._propagate(self.X, self.P, self.Y, self.PY, self.t, t)
        verdict = self.gate.check(np.array([x, y]) - X[:2], math.sqrt(P[0, 0] + P[1, 1]))
        if verdict == "reset":
            self.X, self.P, self.Y, self.PY, self.t = X, P, Y, PY, t
            self._reset(t, x, y, yaw, keep_velocity=True)
            return True
        if verdict == "accept":
            # position
            S = P[:2, :2] + self.R_pos * np.eye(2)
            K = P[:, :2] @ np.linalg.inv(S)
            X = X + K @ (np.array([x, y]) - X[:2])
            P = P - K @ P[:2, :]
            # yaw
            k = PY[:, 0] / (PY[0, 0] + self.R_yaw)
            Y = Y + k * wrap(yaw - Y[0])
            PY = PY - np.outer(k, PY[0, :])
        self.X, self.P, self.Y, self.PY, self.t = X, 0.5 * (P + P.T), Y, 0.5 * (PY + PY.T), t
        return verdict == "accept"

    def _reset(self, t, x, y, yaw, keep_velocity):
        v = self.X[2:4] if keep_velocity else np.zeros(2)
        b = self.X[4:6] if self.t is not None else np.zeros(2)
        bg = self.Y[1] if self.t is not None else 0.0
        self.X = np.array([x, y, v[0], v[1], b[0], b[1]])
        # velocity is unknown after a start and doubtful after a run of rejected poses
        self.P = np.diag([self.R_pos, self.R_pos, 9.0, 9.0, 0.3 ** 2, 0.3 ** 2])
        self.Y = np.array([yaw, bg])
        self.PY = np.diag([self.R_yaw, 0.02 ** 2])
        self.t = t
        self.gate.rejects = self.gate.since_reset = 0
        self.gate.resets += 1

    # ------------------------------------------------------------ prediction
    def _samples(self, t0, t1):
        """IMU segments covering (t0, t1]: list of (dt, ax, ay, gz, dgz_dt).

        Each sample's value holds until the next sample (zero-order hold); the
        last value holds past the newest sample."""
        if not self.imu:
            return [(t1 - t0, 0.0, 0.0, 0.0, 0.0)]
        i = max(bisect_right(self._imu_t, t0) - 1, 0)
        segs, t = [], t0
        while t < t1:
            nxt = self._imu_t[i + 1] if i + 1 < len(self._imu_t) else math.inf
            end = min(nxt, t1)
            _, ax, ay, gz = self.imu[i]
            dgz = 0.0
            if i > 0:
                tp, _, _, gp = self.imu[i - 1]
                dgz = (gz - gp) / max(self.imu[i][0] - tp, 1e-3)
            if end > t:
                segs.append((end - t, ax, ay, gz, dgz))
            t = end
            i += 1
        return segs

    def _propagate(self, X, P, Y, PY, t0, t1):
        X, P, Y, PY = X.copy(), P.copy(), Y.copy(), PY.copy()
        lx = self.imu_offset_x
        for dt, ax, ay, gz, dgz in self._samples(t0, t1):
            r = gz - Y[1]
            # yaw: integrate the gyro
            yaw_mid = Y[0] + 0.5 * r * dt
            Y[0] += r * dt
            FY = np.array([[1.0, -dt], [0.0, 1.0]])
            PY = FY @ PY @ FY.T + np.diag([self.q_g * dt, self.q_bg * dt])
            # specific force at the IMU -> acceleration at base_link (rigid body)
            a_body = np.array([ax + r * r * lx, ay - dgz * lx]) - X[4:6]
            Rm = _rot(yaw_mid)
            u = Rm @ a_body
            X[0:2] += X[2:4] * dt + 0.5 * u * dt * dt
            X[2:4] += u * dt
            F = np.eye(6)
            F[0:2, 2:4] = dt * np.eye(2)
            F[0:2, 4:6] = -0.5 * dt * dt * Rm
            F[2:4, 4:6] = -dt * Rm
            Q = np.zeros((6, 6))
            Q[0:2, 0:2] = self.q_acc * dt ** 3 / 3 * np.eye(2)
            Q[0:2, 2:4] = Q[2:4, 0:2] = self.q_acc * dt ** 2 / 2 * np.eye(2)
            Q[2:4, 2:4] = self.q_acc * dt * np.eye(2)
            Q[4:6, 4:6] = self.q_ba * dt * np.eye(2)
            P = F @ P @ F.T + Q
        return X, P, Y, PY

    def state_at(self, t) -> EstimatedState:
        age = t - self.t
        newest = self.imu[-1][0] if self.imu else self.t
        t_end = max(self.t, min(t, newest + self.max_predict_s))
        X, P, Y, _ = self._propagate(self.X, self.P, self.Y, self.PY, self.t, t_end)
        r = 0.0
        if self.imu:
            # newest gyro reading, extrapolated over at most one VESC period (20 ms)
            # with the slope of the last two readings
            tg, _, _, gz = self.imu[-1]
            r = gz - Y[1]
            if len(self.imu) > 1:
                tp, _, _, gp = self.imu[-2]
                slope = (gz - gp) / max(tg - tp, 1e-3)
                r += slope * min(max(t_end - tg, 0.0), self.r_extrapolate_s)
        return _make_state(t_end, X[:2], X[2:4], Y[0], r,
                           math.sqrt(max(P[2, 2], 0.0)), age, self.min_vx)


# ------------------------------------------------------------------- PF only
class _AxisCA:
    """Constant-acceleration Kalman filter for x and y sharing one covariance."""

    def __init__(self, pos_std, jerk_psd):
        self.R, self.q = pos_std ** 2, jerk_psd
        self.X = np.zeros((3, 2))
        self.P = np.eye(3)

    @staticmethod
    def F(dt):
        return np.array([[1.0, dt, 0.5 * dt * dt], [0.0, 1.0, dt], [0.0, 0.0, 1.0]])

    def Q(self, dt):
        return self.q * np.array([[dt ** 5 / 20, dt ** 4 / 8, dt ** 3 / 6],
                                  [dt ** 4 / 8, dt ** 3 / 3, dt ** 2 / 2],
                                  [dt ** 3 / 6, dt ** 2 / 2, dt]])

    def reset(self, xy, vel=(0.0, 0.0)):
        self.X = np.array([xy, vel, (0.0, 0.0)], dtype=float)
        self.P = np.diag([self.R, 9.0, 225.0])

    def predict(self, dt):
        F = self.F(dt)
        self.X = F @ self.X
        self.P = F @ self.P @ F.T + self.Q(dt)

    def correct(self, xy):
        innov = np.asarray(xy, float) - self.X[0]
        K = self.P[:, 0] / (self.P[0, 0] + self.R)
        self.X += np.outer(K, innov)
        self.P -= np.outer(K, self.P[0, :])


class YawRateKF:
    """[yaw, r] Kalman filter driven by yaw measurements only."""

    def __init__(self, yaw_std=math.radians(1.0), yaw_acc_psd=400.0):
        self.R, self.q = yaw_std ** 2, yaw_acc_psd
        self.x = np.zeros(2)
        self.P = np.eye(2)
        self.t = None

    def reset(self, t, yaw, r=0.0):
        self.t, self.x, self.P = t, np.array([yaw, r]), np.diag([self.R, 4.0])

    def update(self, t, yaw):
        if self.t is None:
            return self.reset(t, yaw)
        dt = t - self.t
        if dt > 0:
            F = np.array([[1.0, dt], [0.0, 1.0]])
            Q = self.q * np.array([[dt ** 3 / 3, dt ** 2 / 2], [dt ** 2 / 2, dt]])
            self.x = F @ self.x
            self.P = F @ self.P @ F.T + Q
            self.t = t
        k = self.P[:, 0] / (self.P[0, 0] + self.R)
        self.x += k * wrap(yaw - self.x[0])
        self.P -= np.outer(k, self.P[0, :])

    def at(self, t):
        return self.x[0] + self.x[1] * (t - self.t), self.x[1]


class PfOnlyEstimator:
    """Fallback without an IMU: velocities from PF poses alone (noisy, see module doc)."""

    def __init__(self, pos_std=0.02, jerk_psd=100.0, yaw_std=math.radians(1.0),
                 yaw_acc_psd=400.0, gate_m=0.3, max_rejects=5, reset_dt=0.5,
                 max_predict_s=0.05, min_vx=0.3):
        self.pos = _AxisCA(pos_std, jerk_psd)
        self.yaw = YawRateKF(yaw_std, yaw_acc_psd)
        self.gate = _Gate(gate_m, max_rejects)
        self.reset_dt, self.max_predict_s, self.min_vx = reset_dt, max_predict_s, min_vx
        self.t = None

    initialized = ImuPoseEstimator.initialized
    total_rejects = ImuPoseEstimator.total_rejects
    resets = ImuPoseEstimator.resets

    def update_imu(self, t, ax, ay, gz):
        pass

    def update_pose(self, t, x, y, yaw) -> bool:
        if self.t is None or t - self.t > self.reset_dt:
            self._reset(t, x, y, yaw, keep_velocity=False)
            return True
        dt = t - self.t
        if dt <= 0:
            return False
        self.pos.predict(dt)
        self.t = t
        verdict = self.gate.check(np.array([x, y]) - self.pos.X[0], math.sqrt(2.0 * self.pos.P[0, 0]))
        if verdict == "reset":
            self._reset(t, x, y, yaw, keep_velocity=True)
            return True
        if verdict == "reject":
            return False
        self.pos.correct((x, y))
        self.yaw.update(t, yaw)
        return True

    def _reset(self, t, x, y, yaw, keep_velocity):
        self.pos.reset((x, y), tuple(self.pos.X[1]) if keep_velocity else (0.0, 0.0))
        self.yaw.reset(t, yaw)
        self.t = t
        self.gate.rejects = self.gate.since_reset = 0
        self.gate.resets += 1

    def state_at(self, t) -> EstimatedState:
        age = t - self.t
        dt = min(max(age, 0.0), self.max_predict_s)
        X = self.pos.F(dt) @ self.pos.X
        yaw, r = self.yaw.at(self.t + dt)
        return _make_state(self.t + dt, X[0], X[1], yaw, r,
                           math.sqrt(max(self.pos.P[1, 1], 0.0)), age, self.min_vx)
