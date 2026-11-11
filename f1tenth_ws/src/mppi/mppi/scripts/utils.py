# MIT License

# Copyright (c) Hongrui Zheng, Johannes Betz

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Utility functions for the Kinematic MPPI waypoint tracker

Author: Hongrui Zheng, Johannes Betz, Ahmad Amine
"""
import numpy as np


def nearest_point(point, trajectory):
    """
    Return the nearest point along the given piecewise linear trajectory.
    Args:
        point (numpy.ndarray, (2, )): (x, y) of current pose
        trajectory (numpy.ndarray, (N, 2)): array of (x, y) trajectory waypoints
            NOTE: points in trajectory must be unique. If they are not unique, a divide by 0 error will destroy the world
    Returns:
        nearest_point (numpy.ndarray, (2, )): nearest point on the trajectory to the point
        nearest_dist (float): distance to the nearest point
        t (float): nearest point's location as a segment between 0 and 1 on the vector formed by the closest two points on the trajectory. (p_i---*-------p_i+1)
        i (int): index of nearest point in the array of trajectory waypoints
    """
    diffs = trajectory[1:, :] - trajectory[:-1, :]
    l2s = diffs[:, 0] ** 2 + diffs[:, 1] ** 2
    dots = np.sum((point - trajectory[:-1, :]) * diffs, axis=1)
    t = np.clip(dots / l2s, 0.0, 1.0)
    projections = trajectory[:-1, :] + t[:, None] * diffs
    dists = np.linalg.norm(point - projections, axis=1)
    i = int(np.argmin(dists))
    return projections[i], dists[i], t[i], i


def calc_interpolated_ref_trajectory(x, y, cx, cy, cyaw, cv, dt, H):
    """Advance along a closed path by speed * dt using actual segment lengths."""
    xy = np.column_stack((cx, cy)).astype(float)
    yaw = np.asarray(cyaw, dtype=float)
    speed = np.asarray(cv, dtype=float)
    if (len(xy) < 2 or yaw.shape != (len(xy),) or speed.shape != (len(xy),)
            or not np.isfinite(xy).all() or not np.isfinite(yaw).all()
            or not np.isfinite(speed).all() or dt <= 0 or H < 0):
        raise ValueError('Invalid reference path or prediction horizon')

    next_xy = np.roll(xy, -1, axis=0)
    lengths = np.linalg.norm(next_xy - xy, axis=1)
    valid = lengths > 1e-8
    if not np.any(valid):
        raise ValueError('Reference path must contain distinct positions')
    start = xy[valid]
    delta = (next_xy - xy)[valid]
    lengths = lengths[valid]
    yaw_start = yaw[valid]
    yaw_delta = (np.roll(yaw, -1) - yaw)[valid]
    yaw_delta = np.arctan2(np.sin(yaw_delta), np.cos(yaw_delta))
    speed_start = speed[valid]
    speed_delta = (np.roll(speed, -1) - speed)[valid]
    arc = np.concatenate(([0.0], np.cumsum(lengths)))

    fraction = np.clip(np.sum((np.array([x, y]) - start) * delta, axis=1)
                       / lengths ** 2, 0.0, 1.0)
    projection = start + fraction[:, None] * delta
    nearest = np.argmin(np.sum((projection - [x, y]) ** 2, axis=1))
    distance = arc[nearest] + fraction[nearest] * lengths[nearest]
    ref = np.empty((H + 1, 4))
    for t in range(H + 1):
        distance %= arc[-1]
        segment = min(np.searchsorted(arc, distance, side='right') - 1,
                      len(lengths) - 1)
        fraction = (distance - arc[segment]) / lengths[segment]
        ref[t, :2] = start[segment] + fraction * delta[segment]
        ref[t, 2] = yaw_start[segment] + fraction * yaw_delta[segment]
        ref[t, 3] = speed_start[segment] + fraction * speed_delta[segment]
        distance += ref[t, 3] * dt
    return ref
