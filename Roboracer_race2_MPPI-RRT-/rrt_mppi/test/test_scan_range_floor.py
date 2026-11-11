import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import unittest
from dataclasses import replace
import numpy as np
from rrt_mppi_node import Config, scan_grid, collides

class ScanRangeFloorTests(unittest.TestCase):

    def setUp(self):
        self.c = Config()
        self.origin = np.array([-3.0, -3.0])
        self.rear = np.zeros(3)
        self.laser = np.array([0.27, 0.0, 0.0])

    def grid(self, ranges, rmin):
        return scan_grid(np.asarray(ranges, dtype=float), 0.0, np.pi / 2, rmin, 8.0, self.laser, self.rear, self.origin, 120, 0.05, self.c.geometry())

    def test_two_mm_return_reproduces_start_blocked_then_is_rejected(self):
        old = self.grid([0.002, 1.0], 0.0)
        new = self.grid([0.002, 1.0], self.c.scan_min_valid_range_m)
        self.assertTrue(collides(self.rear, old, self.origin, 0.05, self.c.geometry()))
        self.assertFalse(collides(self.rear, new, self.origin, 0.05, self.c.geometry()))
        col, row = np.floor((np.array([0.27, 1.0]) - self.origin) / 0.05).astype(int)
        self.assertEqual(new[row, col], 100)

    def test_rejected_beam_does_not_clear_or_extend_free_space(self):
        np.testing.assert_array_equal(self.grid([0.002], 0.05), self.grid([np.nan], 0.05))
        g = self.grid([0.002], 0.05)
        col, row = np.floor((np.array([-0.5, 0.0]) - self.origin) / 0.05).astype(int)
        self.assertEqual(g[row, col], -1)

    def test_real_obstacle_is_not_cleared_even_inside_body(self):
        g = self.grid([0.1], 0.05)
        self.assertTrue(collides(self.rear, g, self.origin, 0.05, self.c.geometry()))

    def test_range_floor_validation(self):
        for bad in (-0.01, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                replace(self.c, scan_min_valid_range_m=bad).validate()
        replace(self.c, scan_min_valid_range_m=0.0).validate()
if __name__ == '__main__':
    unittest.main()
