import sys, unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import rrt_mppi_node as m

class SteeringContinuity(unittest.TestCase):

    def test_circle_feedforward_matches_bicycle_turning_radius(self):
        c = m.Config()
        theta = np.linspace(0, 0.5, 11)
        radius = 2.0
        ref = np.column_stack((radius * np.sin(theta), radius * (1 - np.cos(theta)), theta, np.ones(11)))
        expected = np.arctan(c.WB / radius)
        np.testing.assert_allclose(m.reference_steering(ref, c), expected, atol=3e-05)
        ref[:, 1:3] *= -1
        np.testing.assert_allclose(m.reference_steering(ref, c), -expected, atol=3e-05)

    def test_stop_preserves_actual_steering_and_clears_acceleration(self):
        ctrl = m.MPPI(replace(m.Config(), T=16, H=10))
        ctrl.U[:] = 1.0
        ctrl.previous[:] = [2.0, 0.3]
        ctrl.reset()
        np.testing.assert_array_equal(ctrl.U[:, 0], 0.0)
        np.testing.assert_array_equal(ctrl.U[:, 1], 0.3)
        self.assertEqual(ctrl.previous[1], 0.3)
        self.assertIsNone(ctrl.steering_feedforward)

    def test_heading_wrap_and_stationary_reference_are_finite(self):
        c = m.Config()
        r = np.array([[0.0, 0.0, 3.13, 0.0], [0.1, 0.0, -3.13, 0.0], [0.1, 0.0, -3.13, 0.0]])
        u = m.reference_steering(r, c)
        self.assertTrue(np.isfinite(u).all())
        self.assertGreater(u[0], 0.0)
        self.assertEqual(u[1], 0.0)

    def test_seed_is_projected_through_actual_steering_rate_limits(self):
        c = replace(m.Config(), T=64, H=10)
        ctrl = m.MPPI(c)
        u = np.zeros((1, c.H, 2))
        u[:, :, 1] = c.MAX_STEER
        bounded = ctrl.project(u)[0, :, 1]
        self.assertLessEqual(abs(bounded[0]), c.MAX_STEER_RATE * c.DT + 1e-12)
        self.assertTrue(np.all(np.abs(np.diff(bounded)) <= c.MAX_STEER_RATE * c.DT + 1e-12))
if __name__ == '__main__':
    unittest.main()
