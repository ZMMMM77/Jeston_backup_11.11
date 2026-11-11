import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import unittest
from collections import deque
from types import SimpleNamespace as NS
import numpy as np
from builtin_interfaces.msg import Time
from visualization_msgs.msg import Marker
from rrt_mppi_node import MPPIVisualization

class ActualMotionTests(unittest.TestCase):

    def setUp(self):
        self.v = MPPIVisualization.__new__(MPPIVisualization)
        self.v.node = NS(config=NS(MAX_SPEED=6.0, map_frame='map'), get_clock=lambda: NS(now=lambda: NS(to_msg=lambda: Time())))
        self.v.motion_history = deque(maxlen=16)
        self.v.actual_trail = deque(maxlen=400)
        self.v.actual_pub = None
        self.messages = []
        self.v.emit = lambda publisher, message: self.messages.append(message)

    def update(self, x, y, t, speed):
        self.v.publish_actual_motion(np.array([x, y, 0.0, speed]), t)
        return {m.ns: m for m in self.messages[-1].markers}

    def test_arrow_follows_measured_displacement_not_yaw(self):
        self.update(0, 0, 1.0, 1.0)
        m = self.update(0, 0.2, 1.2, 1.0)
        a = m['actual_direction']
        self.assertEqual(a.action, Marker.ADD)
        self.assertAlmostEqual(a.points[1].x, a.points[0].x)
        self.assertGreater(a.points[1].y, a.points[0].y)
        dot = m['actual_position']
        self.assertAlmostEqual(dot.pose.position.y, 0.2)
        self.assertGreater(dot.color.r, 0.8)
        self.assertLess(dot.color.g, 0.1)

    def test_stationary_and_duplicate_stamp_clear_arrow(self):
        self.update(0, 0, 1.0, 0.0)
        m = self.update(0.001, 0, 1.2, 0.0)
        self.assertEqual(m['actual_direction'].action, Marker.DELETE)
        self.update(0.1, 0, 1.2, 1.0)
        self.assertEqual(len(self.v.motion_history), 1)

    def test_localization_jump_starts_new_trail(self):
        self.update(0, 0, 1.0, 1.0)
        m = self.update(3, 0, 1.2, 1.0)
        self.assertEqual(m['actual_direction'].action, Marker.DELETE)
        self.assertEqual(len(self.v.motion_history), 1)
if __name__ == '__main__':
    unittest.main()
