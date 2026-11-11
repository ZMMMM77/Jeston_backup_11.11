import sys, unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import rrt_mppi_node as m

class StationaryRecovery(unittest.TestCase):

    def cfg(self):
        return replace(m.Config(), T=256, H=10, DT=0.05, MAX_ACCEL=5.0, MAX_SPEED=10.0, LAMBDA=0.04, U_STD=(2.0, 0.07), Q=(4.0, 4.0, 1.5, 3.0), Qf=(4.0, 4.0, 1.5, 3.0), R=(0.01, 2.0), Rd=(0.01, 2.0))

    def test_centers_steering_before_applying_forward_acceleration(self):
        c = self.cfg()
        ref = np.tile([0.0, 0.0, 0.0, 1.0], (c.H + 1, 1))
        u = m.stationary_recovery_controls(np.zeros(4), np.array([0.0, 0.33]), ref, c)
        self.assertTrue(np.all(u[0, :, 0] == 0.0))
        moving = u[1]
        self.assertTrue(np.all(moving[moving[:, 1] != 0.0, 0] == 0.0))
        self.assertGreater(moving[-1, 0], -1e-10)
        self.assertTrue(np.any(moving[:, 0] > 0.0))
        self.assertEqual(moving[-1, 1], 0.0)

    def test_endpoint_stop_is_not_overridden(self):
        c = self.cfg()
        ref = np.zeros((c.H + 1, 4))
        u = m.stationary_recovery_controls(np.zeros(4), np.zeros(2), ref, c)
        self.assertTrue(np.all(u[:, :, 0] == 0.0))

    def test_captured_low_speed_blind_region_can_recover_without_clearing_grid(self):
        c = self.cfg()
        a = np.load(Path(__file__).parent / 'fixtures/stationary_recovery.npz')
        state = a['state'].copy()
        start = state.copy()
        grid = a['grid']
        original = grid.copy()
        origin = a['origin']
        path = a['path']
        ctrl = m.MPPI(c)
        ctrl.previous[1] = float(a['steer'])
        ctrl.reset()
        speeds = []
        for _ in range(16):
            action, ref, pred, stats = ctrl.solve(state, path, 1.0, grid, origin)
            self.assertIsNotNone(action, stats)
            self.assertTrue(ctrl.valid(pred[None], ctrl.U[None], grid, origin)[0])
            ctrl.previous = action.copy()
            state = pred[1].copy()
            speeds.append(state[3])
        self.assertGreater(max(speeds), 0.1)
        self.assertGreater(np.linalg.norm(state[:2] - start[:2]), 0.02)
        np.testing.assert_array_equal(grid, original)
if __name__ == '__main__':
    unittest.main()
