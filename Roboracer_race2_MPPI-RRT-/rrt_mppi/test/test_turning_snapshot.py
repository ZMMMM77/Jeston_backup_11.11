import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import rrt_mppi_node as m

class TurningSnapshot(unittest.TestCase):

    def test_ambiguous_unknown_envelope_refines_without_clearing_grid(self):
        a = np.load(Path(__file__).parent / 'fixtures/turning_grid.npz')
        q = a['state']
        g = a['grid']
        o = a['origin']
        before = g.copy()
        b = m.Config().geometry()
        for k, expected in ((0.01, True), (-0.01, False), (0.1, True), (-0.1, False)):
            path = np.array([m.arc(q, d, k) for d in np.linspace(0, 0.6, 31)])
            self.assertEqual(m.path_clear(path, g, o, 0.05, b), expected)
        np.testing.assert_array_equal(g, before)
if __name__ == '__main__':
    unittest.main()
