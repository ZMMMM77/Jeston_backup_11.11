import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import math
import unittest
from dataclasses import replace
import numpy as np
from rrt_mppi_node import Config
from rrt_mppi_node import collides, arc, arc_clear, path_clear, scan_grid, wrap
from rrt_mppi_node import MPPI, reference_from_path, advance

class CoreTests(unittest.TestCase):

    def setUp(self):
        self.c = Config().validate()
        self.grid = np.zeros((240, 240), np.int8)
        self.origin = np.array([-6.0, -6.0])
        self.body = self.c.geometry()

    def put(self, x, y, value=100):
        col, row = np.floor((np.array([x, y]) - self.origin) / 0.05).astype(int)
        self.grid[row, col] = value

    def hit(self, pose, padding=0.0):
        return collides(np.array(pose, dtype=float), self.grid, self.origin, 0.05, self.body, padding)

    def test_inflation_and_orientation(self):
        self.put(0.3, 0.2)
        self.body[3] = 0.06
        self.assertTrue(self.hit([0, 0, 0]))
        raw = self.body.copy()
        raw[3] = 0
        self.assertFalse(collides(np.zeros(3), self.grid, self.origin, 0.05, raw))
        self.grid.fill(0)
        self.put(0.42, 0)
        self.assertTrue(self.hit([0, 0, 0]))
        self.assertFalse(self.hit([0, 0, math.pi / 2]))

    def test_grid_cell_corner_not_just_center(self):
        self.put(0.46, 0.0)
        self.assertTrue(self.hit([0, 0, 0]))

    def test_unknown_and_bounds(self):
        self.put(0.2, 0, -1)
        self.assertTrue(self.hit([0, 0, 0]))
        self.assertTrue(self.hit([5.9, 0, 0]))

    def test_straight_sweep_catches_between_endpoints(self):
        self.put(1.0, 0)
        self.assertFalse(self.hit([0, 0, 0]))
        self.assertFalse(self.hit([2, 0, 0]))
        self.assertFalse(arc_clear(np.zeros(3), 2.0, 0.0, self.grid, self.origin, 0.05, self.body, 0.04))

    def test_turn_sweep_catches_front_corner(self):
        middle = arc(np.zeros(3), 0.7, 1.0)
        x = middle[0] + 0.43 * math.cos(middle[2]) - 0.14 * math.sin(middle[2])
        y = middle[1] + 0.43 * math.sin(middle[2]) + 0.14 * math.cos(middle[2])
        self.put(x, y)
        self.assertFalse(arc_clear(np.zeros(3), 1.4, 1.0, self.grid, self.origin, 0.05, self.body, 0.04))

    def test_scan_removes_disappeared_gate_and_preserves_hit(self):
        n = 1440
        angles = -math.pi
        da = 2 * math.pi / n
        origin = np.array([-6.0, -6.0])
        ranges = np.full(n, np.inf)
        ranges[n // 2] = 1.0
        grid = scan_grid(ranges, angles, da, 0.05, 8.0, np.zeros(3), np.zeros(3), origin, 240, 0.05, self.body)
        self.assertEqual(grid[120, 140], 100)
        ranges[n // 2] = np.inf
        opened = scan_grid(ranges, angles, da, 0.05, 8.0, np.zeros(3), np.zeros(3), origin, 240, 0.05, self.body)
        self.assertEqual(opened[120, 140], 0)

    def test_reference_stops_at_endpoint_and_wraps_yaw(self):
        path = np.column_stack((np.linspace(0, 1, 30), np.zeros(30), np.linspace(3.1, 3.2, 30)))
        ref = reference_from_path(np.array([0.98, 0, 3.18, 0.1]), path, 1.0, self.c)
        self.assertLessEqual(ref[-1, 0], 1.0)
        self.assertLess(ref[-1, 3], 0.1)

    def test_mppi_limits_and_safe_prediction(self):
        c = replace(self.c, T=80, H=15)
        m = MPPI(c)
        path = np.column_stack((np.linspace(0, 3, 100), np.zeros(100), np.zeros(100)))
        state = np.zeros(4)
        for _ in range(8):
            action, ref, pred, stats = m.solve(state, path, 1.0, self.grid, self.origin)
            self.assertIsNotNone(action, stats)
            self.assertLessEqual(abs(action[1] - m.previous[1]), c.MAX_STEER_RATE * c.DT + 1e-09)
            self.assertTrue(np.isfinite(pred).all())
            for i in range(c.H):
                nxt, d, k = advance(pred[i], m.U[i], c.DT, c.WB, c.MAX_SPEED, c.BRAKE_DECEL)
                self.assertTrue(arc_clear(pred[i, :3], d, k, self.grid, self.origin, 0.05, self.body, 0.04))
            m.previous = action.copy()
            state = pred[1]
        self.assertGreater(state[0], 0.01)

    def test_mppi_blocked_body_fails_closed(self):
        self.put(0.2, 0)
        m = MPPI(replace(self.c, T=20, H=5))
        path = np.array([[0.0, 0, 0], [3.0, 0, 0]])
        result = m.solve(np.zeros(4), path, 1.0, self.grid, self.origin)
        self.assertIsNone(result[0])
        self.assertEqual(result[3]['valid_samples'], 0)

    def test_braking_tail_rejects_short_horizon(self):
        self.grid[:, 139:141] = 100
        c = replace(self.c, H=1, T=20)
        m = MPPI(c)
        path = np.array([[0.0, 0, 0], [3.0, 0, 0]])
        result = m.solve(np.array([0.0, 0, 0, 1.5]), path, 1.5, self.grid, self.origin)
        self.assertIsNone(result[0])

    def test_braking_does_not_move_backward(self):
        nxt, d, _ = advance(np.array([0.0, 0, 0, 0.1]), np.array([-2.0, 0.0]), 0.1, 0.33, 1.5, 2.0)
        self.assertAlmostEqual(d, 0.0025)
        self.assertEqual(nxt[3], 0.0)

    def test_parameter_validation(self):
        for overrides in ({'LAMBDA': 0.0}, {'footprint_margin_m': -0.1}, {'U_STD': (0.0, 0.1)}, {'Q': (1.0, 2.0)}):
            with self.assertRaises(ValueError):
                replace(self.c, **overrides).validate()
if __name__ == '__main__':
    unittest.main()
