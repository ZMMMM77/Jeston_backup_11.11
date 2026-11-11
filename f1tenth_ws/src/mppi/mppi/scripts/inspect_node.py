#!/usr/bin/env python3
"""Record and replay MPPI decisions without duplicating the controller logic.

Run from the ROS environment in which `mppi_node` and `utils` are importable:

    python -i inspect.py --iterations 100 --ros-args -p visualize:=false

At the interactive prompt after collection:

    inspect_node.plot(5)

Only iterations that reach mppi_step are counted. The original node publishes
stop commands while waiting for valid odometry/scans, as before.
"""

# This file's required name, "inspect.py", also belongs to a Python stdlib module.
# When executed as a script, ensure dependencies can still import stdlib inspect.
PARAMETERS = {
    "waypoints_path": "race.csv",
    'T': 512,
    'H': 15,
    'DT': 0.1,
    'LAMBDA': 0.06,
    'U_STD': [2.0, 0.15],
    'Q': [12.0, 12.0, 4.0, 4.0],
    'Qf': [12.0, 12.0, 4.0, 4.0],
    'R': [0.003, 0.5],
    'Rd': [0.003, 0.5],
    'MIN_SPEED': 1.0,
    'MAX_SPEED': 6.0,
    'obstacle_avoidance': True,
    'obstacle_range_m': 2.5,
    'obstacle_weight': 100.0,
    'obstacle_clearance_m': 0.05,
    'visualize_samples': False,
}

import argparse
from bisect import bisect_left
from copy import deepcopy
import math
import time

import matplotlib.pyplot as plt
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException

from rclpy.parameter import Parameter

from mppi_node import MPPI, rollout, simulate, state_from_odom


class InspectMPPI(MPPI):
    def __init__(self, N_iter=100, parameter_overrides = []):
        if N_iter < 1:
            raise ValueError("N_iter must be positive")
        super().__init__(parameter_overrides = parameter_overrides)
        self.N_iter = int(N_iter)
        self.iter = 0  # number of decisions recorded (indices are 0, ..., iter-1)
        self.finished = False

        # These six lists have matching indices, one per completed MPPI step.
        self.warm_start_history = []  # (H, NU): rolled-over input sequence
        self.key_history = []         # PRNG seed passed to mppi_step
        self.trajectory_history = []  # (H+1, NX): resulting nominal state rollout
        self.ref_history = []         # (H+1, NX): actual reference passed to MPPI
        self.state_history = []       # (NX,): rear-axle state [x, y, yaw, v]
        self.scan_history = []        # LaserScan message, or None if LiDAR disabled

        # Small extras useful for analysis / exact scan positioning.
        self.selected_U_history = []
        self.scan_pose_bracket_history = []

        self._pending_ref = None
        self._pending_scan = None
        self._pending_scan_pose_bracket = None

    def calc_ref_trajectory(self, *args, **kwargs):
        """Capture the *same* reference calculated by the parent, at no recompute cost."""
        ref = super().calc_ref_trajectory(*args, **kwargs)
        self._pending_ref = np.array(ref, copy=True)
        return ref

    def scan_soft_cost(self):
        """The source calls this `scan_soft_cost`, not `scan_cost_soft`."""
        obstacle_cost = super().scan_soft_cost()
        self._pending_scan = deepcopy(self.scan_msg)

        # Save only the 1-2 odometry poses bracketing this scan's timestamp.
        # This permits full raw LiDAR visualization in map coordinates later.
        stamp = (self.scan_msg.header.stamp.sec
                 + self.scan_msg.header.stamp.nanosec * 1e-9)
        history = list(self.pose_history)
        k = bisect_left([item[0] for item in history], stamp)
        if 0 < k < len(history):
            bracket = (history[k - 1], history[k])
        else:
            bracket = (history[min(k, len(history) - 1)],)
            self._pending_scan_pose_bracket = tuple(
                (float(t), pose.copy()) for t, pose in bracket
            )
        return obstacle_cost

    def control_callback(self):
        if self.finished:
            return

        # Values the parent will overwrite/consume during this callback.
        odom = self.latest_odom
        previous_U = self.U.copy()
        key_before = self.key
        self._pending_ref = None
        self._pending_scan = None
        self._pending_scan_pose_bracket = None

        super().control_callback()

        # `key` changes only after the parent's validity checks succeed and
        # immediately before mppi_step. Don't record failed/waiting callbacks.
        if self.key == key_before:
            return

        state = state_from_odom(odom, self.map_frame, self.pose_x, self.pose_y)
        warm_start = np.concatenate((previous_U[1:], previous_U[-1:]), axis=0)
        selected_U = self.U.copy()

        self.warm_start_history.append(warm_start)
        self.key_history.append(int(self.key))
        self.selected_U_history.append(selected_U)
        self.trajectory_history.append(simulate(state, selected_U, self.config))
        self.ref_history.append(self._pending_ref)
        self.state_history.append(state.copy())
        self.scan_history.append(self._pending_scan)
        self.scan_pose_bracket_history.append(self._pending_scan_pose_bracket)

        self.iter += 1
        if self.iter >= self.N_iter:
            # Do not shut down rclpy here: main() exits its spin_once loop when
            # `finished` becomes True. This lets the stop command be published.
            self.publish_stop()
            self.control_timer.cancel()
            self.finished = True
            print(f"MPPI inspection complete: recorded {self.iter} decisions; "
                  "stop command published.", flush=True)

    def _scan_points_xy(self, i):
        """Transform the stored raw scan from laser frame to map coordinates."""
        scan = self.scan_history[i]
        bracket = self.scan_pose_bracket_history[i]
        if scan is None or bracket is None:
            return np.empty((0, 2))

        if len(bracket) == 1:
            rear = bracket[0][1].copy()
        else:
            (t0, a), (t1, b) = bracket
            stamp = scan.header.stamp.sec + scan.header.stamp.nanosec * 1e-9
            f = (stamp - t0) / (t1 - t0)
            rear = a + f * (b - a)
            rear[2] = a[2] + f * math.atan2(
                math.sin(b[2] - a[2]), math.cos(b[2] - a[2])
            )

        # Same pose-to-rear-axle convention as the base scan_soft_cost method.
        c, s = math.cos(rear[2]), math.sin(rear[2])
        laser_xy = rear[:2] - np.array([
            c * self.pose_x - s * self.pose_y,
            s * self.pose_x + c * self.pose_y,
        ])
        ranges = np.asarray(scan.ranges, dtype=float)
        angles = scan.angle_min + np.arange(len(ranges)) * scan.angle_increment
        valid = (np.isfinite(ranges)
                 & (ranges >= scan.range_min)
                 & (ranges < scan.range_max))
        r = ranges[valid]
        a = angles[valid]
        local = np.column_stack((r * np.cos(a), r * np.sin(a)))
        return local @ np.array([[c, s], [-s, c]]) + laser_xy

    def plot(self, i, n_alternates=40, ax=None):
        """Plot recorded decision i (zero-indexed) and sampled alternatives.

        Alternatives are regenerated using the original seed and warm start;
        all T sampled trajectories are *not* kept in memory during collection.
        """
        if not 0 <= i < self.iter:
            raise IndexError(f"Decision index must be in [0, {self.iter - 1}]")
        if n_alternates < 0:
            raise ValueError("n_alternates must be nonnegative")

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        else:
            fig = ax.figure

        cfg = self.config
        x0 = self.state_history[i]
        if n_alternates:
            # Exactly the same Gaussian draw shape/order and clipping as mppi_step.
            rng = np.random.default_rng(self.key_history[i])
            noise = rng.standard_normal((cfg.T, cfg.H, cfg.NU))
            indices = np.linspace(
                0, cfg.T - 1, min(int(n_alternates), cfg.T), dtype=int
            )
            sampled_U = np.clip(
                self.warm_start_history[i][None]
                + noise[indices] * np.asarray(cfg.U_STD),
                [cfg.MIN_ACCEL, cfg.MIN_STEER],
                [cfg.MAX_ACCEL, cfg.MAX_STEER],
            )
            paths = rollout(x0, sampled_U, cfg)
            for j, path in enumerate(paths):
                ax.plot(path[:, 0], path[:, 1], color="0.6", alpha=0.25,
                        linewidth=0.9, label="Candidate rollouts" if j == 0 else None)

        scan_xy = self._scan_points_xy(i)
        if len(scan_xy):
            ax.scatter(scan_xy[:, 0], scan_xy[:, 1], s=3, color="0.3",
                       alpha=0.6, label="LiDAR returns", rasterized=True)

        chosen = self.trajectory_history[i]
        ax.plot(chosen[:, 0], chosen[:, 1], "b-", linewidth=2.5,
                label="Chosen nominal rollout")
        reference = self.ref_history[i]
        ax.scatter(reference[:, 0], reference[:, 1], color="tab:orange",
                   marker="x", s=40, label="Reference waypoints", zorder=4)
        ax.scatter([x0[0]], [x0[1]], color="tab:red", s=75,
                   label="Vehicle", zorder=5)
        ax.arrow(x0[0], x0[1], 0.35 * np.cos(x0[2]), 0.35 * np.sin(x0[2]),
                 head_width=0.12, head_length=0.15, color="tab:red",
                 length_includes_head=True, zorder=5)

        ax.set(xlabel="x [m]", ylabel="y [m]", title=f"MPPI decision {i} (key={self.key_history[i]}, x={x0[0]:.2f}, y={x0[1]:.2f})")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")
        fig.tight_layout()
        plt.show()
        
    def plot_history(self):
        states = np.asarray(self.state_history)

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.scatter(self.waypoints[:, 0], self.waypoints[:, 1],
                   s=5, color="gray", label="Waypoints")

        sc = ax.scatter(states[:, 0], states[:, 1],
                        c=np.arange(len(states)), cmap="viridis",
                        s=12, label="Vehicle history")

        fig.colorbar(sc, ax=ax, label="History index")
        ax.set_aspect("equal")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        ax.legend()
        plt.show()

    def find_near(self, x, y, radius=0.5):
        states = np.asarray(self.state_history)
        if len(states) == 0:
            return np.array([], dtype=int)

        d = np.linalg.norm(states[:, :2] - [x, y], axis=1)
        indices = np.flatnonzero(d <= radius)
        return indices[np.argsort(d[indices])]


def main(args=None):
    parser = argparse.ArgumentParser(description="Record a fixed number of MPPI decisions")
    parser.add_argument("--iterations", type=int, default=100)
    options, ros_args = parser.parse_known_args(args)

    rclpy.init(args=ros_args)
    node = InspectMPPI(N_iter=options.iterations, parameter_overrides=[
        Parameter(name,value=value) for name, value in PARAMETERS.items()
    ])
    try:
        # rclpy.spin(node) does NOT stop when a timer is cancelled. An explicit
        # loop lets the completion flag terminate spinning cleanly.
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        print("Inspection interrupted; sending stop command.", flush=True)
    finally:
        if rclpy.ok():
            node.publish_stop()
            time.sleep(0.1)  # allow the stop publication to reach DDS before teardown
        node.destroy_node()
        rclpy.try_shutdown()
    return node


if __name__ == "__main__":
    # `python -i inspect.py ...` preserves this object after collection.
    inspect_node = main()
