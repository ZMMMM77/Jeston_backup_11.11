import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import numpy as np
from rrt_mppi_node import Config, collides, path_clear, arc_clear

class SweepRegression(unittest.TestCase):

    def test_forward_sweep_does_not_expand_into_blind_rear(self):
        c = Config()
        body = c.geometry()
        res = 0.05
        origin = np.array([-6.0, -6.0])
        grid = np.full((240, 240), -1, np.int8)
        yy, xx = np.mgrid[:240, :240]
        x = origin[0] + (xx + 0.5) * res
        y = origin[1] + (yy + 0.5) * res
        grid[x >= 0] = 0
        self_body = (np.abs(x - body[2]) <= body[0] / 2 + res / 2) & (np.abs(y) <= body[1] / 2 + res / 2)
        grid[self_body] = 0
        a = np.zeros(3)
        b = np.array([0.6, 0.0, 0.0])
        path = np.vstack((a, b))
        self.assertFalse(collides(a, grid, origin, res, body))
        self.assertTrue(path_clear(path, grid, origin, res, body))
        self.assertTrue(arc_clear(a, 0.6, 0.0, grid, origin, res, body, 0.04))
        grid[120, 134] = 100
        self.assertFalse(path_clear(path, grid, origin, res, body))
        self.assertFalse(arc_clear(a, 0.6, 0.0, grid, origin, res, body, 0.04))
if __name__ == '__main__':
    unittest.main()
