import sys, unittest, subprocess
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from builtin_interfaces.msg import Time
from visualization_msgs.msg import Marker
from rrt_mppi_node import MPPIVisualization, MPPINode
from planning_common import Config
from mppi import MPPI, rollout

class PureMPPIVisualizationTests(unittest.TestCase):

    def setUp(self):
        self.v = MPPIVisualization.__new__(MPPIVisualization)
        self.v.node = NS(config=Config(), get_clock=lambda: NS(now=lambda: NS(to_msg=lambda: Time())))
        self.refs = []
        self.preds = []
        self.display = []
        self.v.reference_pub = NS(publish=self.refs.append)
        self.v.prediction_pub = NS(publish=self.preds.append)
        self.v.display_pub = NS(publish=self.display.append)

    def test_reference_points_and_endpoint_are_separate_markers(self):
        reference = np.array([[0.0, 0.0, 0.0, 1.0], [0.4, 0.2, 0.1, 1.0], [0.8, 0.3, 0.2, 1.0]])
        self.v.publish_reference(reference)
        line, points, end = self.refs[-1].markers
        self.assertEqual(len(points.points), len(reference))
        self.assertEqual(end.type, Marker.SPHERE)
        self.assertAlmostEqual(end.pose.position.x, reference[-1, 0])
        self.assertGreater(end.scale.x, points.scale.x)

    def test_prediction_starts_at_current_state_and_marks_its_endpoint(self):
        from dataclasses import replace
        from mppi import MPPIConfig
        c = replace(MPPIConfig(), H=4)
        current = np.array([3.0, 2.0, 0.4, 0.5])
        u = np.zeros((1, c.H, 2))
        predicted = rollout(current, u, c)[0]
        self.v.publish_prediction(predicted[:, 0], predicted[:, 1])
        line, points, end = self.preds[-1].markers
        self.assertAlmostEqual(line.points[0].x, current[0])
        self.assertAlmostEqual(line.points[0].y, current[1])
        self.assertEqual(len(points.points), c.H + 1)
        self.assertAlmostEqual(end.pose.position.x, predicted[-1, 0])

    def test_stop_deletes_line_points_and_endpoint(self):
        self.v.publish_prediction([], [])
        self.assertEqual([m.action for m in self.preds[-1].markers], [Marker.DELETE] * 3)

    def test_active_sources_have_no_search_or_mode_switch(self):
        root = Path(__file__).resolve().parents[1]
        self.assertFalse((root / 'scripts/rrt_star.py').exists())
        for name in ['scripts/rrt_mppi_node.py', 'scripts/mppi.py', 'scripts/planning_common.py', 'launch/levine_launch.py']:
            text = (root / name).read_text()
            self.assertNotIn('rrt_enabled', text)
            self.assertNotIn('RRT_ON', text)
        self.assertNotIn('rrt_iterations', Config.__dataclass_fields__)

    def test_standalone_mppi_still_has_no_ros_dependency(self):
        root = str(Path(__file__).resolve().parents[1] / 'scripts')
        code = f"import sys;sys.path.insert(0,{root!r});from mppi import MPPI,Config;MPPI(Config());assert 'rclpy' not in sys.modules;assert 'rrt_star' not in sys.modules"
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
if __name__ == '__main__':
    unittest.main()
