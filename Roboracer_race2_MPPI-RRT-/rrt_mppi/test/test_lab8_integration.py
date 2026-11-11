import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import unittest
from dataclasses import replace
import numpy as np
from rrt_mppi_node import Config
from rrt_mppi_node import MPPI
from rrt_mppi_node import rollout, cost

class IntegrationTests(unittest.TestCase):

    def test_lab8_rollout_cost_and_masked_weights(self):
        c = replace(Config(), T=40, H=8, INTEGRATOR='rk4', LAMBDA=0.1)
        m = MPPI(c)
        grid = np.zeros((240, 240), np.int8)
        origin = np.array([-6.0, -6.0])
        path = np.column_stack((np.linspace(0, 3, 100), np.zeros(100), np.zeros(100)))
        state = np.array([0.0, 0.0, 0.0, 0.2])
        action, ref, pred, stats = m.solve(state, path, 1.0, grid, origin)
        self.assertIsNotNone(action)
        self.assertEqual(m.lab.INTEGRATOR, 'rk4')
        np.testing.assert_allclose(pred, np.asarray(rollout(state, m.U[None], m.lab))[0], atol=1e-06)
        np.testing.assert_allclose(m.last_weights.sum(axis=0), 1.0, atol=1e-06)
        self.assertTrue(np.isfinite(np.asarray(cost(np.asarray(pred), np.asarray(m.U), np.asarray(ref), m.lab, 0.0))).all())
        grid[120, 124] = 100
        action, _, _, _ = m.solve(state, path, 1.0, grid, origin)
        self.assertIsNone(action)
        self.assertEqual(m.last_weights.sum(), 0.0)
if __name__ == '__main__':
    unittest.main()
