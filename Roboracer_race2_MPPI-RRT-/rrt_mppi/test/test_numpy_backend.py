"""Numerical regression checks for the dependency-free Lab8 backend."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import unittest
from dataclasses import replace
import numpy as np
from rrt_mppi_node import MPPIConfig, rollout, cost, mppi_step

class NumpyBackendTests(unittest.TestCase):

    def test_straight_acceleration_analytic_euler_and_rk4(self):
        h, dt = (12, 0.05)
        accelerations = np.array([-0.2, 0.0, 0.8])
        controls = np.zeros((3, h, 2))
        controls[..., 0] = accelerations[:, None]
        k = np.arange(h + 1)
        for integrator in ('euler', 'rk4'):
            c = replace(MPPIConfig(), H=h, DT=dt, INTEGRATOR=integrator)
            x = rollout(np.array([2.0, 3.0, 0.0, 1.0]), controls, c)
            distance = k * dt + 0.5 * accelerations[:, None] * dt ** 2 * k * (k - (integrator == 'euler'))
            np.testing.assert_allclose(x[..., 0], 2 + distance, atol=1e-12)
            np.testing.assert_allclose(x[..., 3], 1 + accelerations[:, None] * k * dt, atol=1e-12)
            np.testing.assert_allclose(x[..., 1], 3.0)
            np.testing.assert_allclose(x[..., 2], 0.0)

    def test_constant_turn_rk4_matches_circle(self):
        c = replace(MPPIConfig(), H=20, DT=0.05, INTEGRATOR='rk4')
        u = np.zeros((2, c.H, 2))
        u[..., 1] = np.array([0.2, -0.2])[:, None]
        x = rollout(np.array([0.0, 0.0, 0.0, 1.0]), u, c)
        curvature = np.tan(u[:, 0, 1]) / c.WB
        theta = curvature * c.H * c.DT
        np.testing.assert_allclose(x[:, -1, 0], np.sin(theta) / curvature, atol=1e-08)
        np.testing.assert_allclose(x[:, -1, 1], (1 - np.cos(theta)) / curvature, atol=1e-08)
        np.testing.assert_allclose(x[:, -1, 2], theta, atol=1e-12)

    def test_terminal_heading_slew_and_speed_penalties(self):
        c = replace(MPPIConfig(), H=1, MAX_SPEED=1.0, Qf=(1.0, 2.0, 3.0, 4.0), R=(0.1, 0.2), Rd=(0.3, 0.4))
        x = np.array([[0.0, 0.0, 0.0, 0.0], [1.0, 2.0, 2 * np.pi + 0.1, 1.5]])
        ref = np.zeros((2, 4))
        u = np.array([[0.2, 0.3]])
        expected = 1 + 2 * 4 + 3 * 0.1 ** 2 + 4 * 1.5 ** 2 + 0.1 * 0.2 ** 2 + 0.2 * 0.3 ** 2 + 0.4 * (0.3 - 0.1) ** 2 + 1000 * 0.5 ** 2
        np.testing.assert_allclose(cost(x, u, ref, c, 0.1), [expected])
        np.testing.assert_allclose(cost(np.stack([x, x]), np.stack([u, u]), ref, c, 0.1), [[expected], [expected]])

    def test_seeded_numpy_update_bounds_and_weights(self):
        c = replace(MPPIConfig(), T=32, H=5)
        state = np.zeros(4)
        u = np.zeros((c.H, 2))
        ref = np.zeros((c.H + 1, 4))
        a, x, w = mppi_step(9, u, state, ref, c)
        np.testing.assert_array_equal(a, mppi_step(9, u, state, ref, c)[0])
        self.assertEqual(x.shape, (c.T, c.H + 1, 4))
        np.testing.assert_allclose(w.sum(axis=0), 1.0)
        self.assertTrue(np.isfinite(x).all() and np.isfinite(a).all())
        self.assertTrue((a >= [c.MIN_ACCEL, c.MIN_STEER]).all())
        self.assertTrue((a <= [c.MAX_ACCEL, c.MAX_STEER]).all())
if __name__ == '__main__':
    unittest.main()
