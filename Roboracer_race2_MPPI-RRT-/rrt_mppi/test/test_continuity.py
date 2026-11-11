import sys, time, unittest
from pathlib import Path
from types import SimpleNamespace as NS
from collections import deque
from dataclasses import replace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import rrt_mppi_node as m
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped

class Continuity(unittest.TestCase):

    def test_use_recent_transformable_scan_when_latest_tf_not_ready(self):

        def scan(ns):
            s = LaserScan()
            s.header.frame_id = 'laser'
            s.header.stamp.sec = 10
            s.header.stamp.nanosec = ns
            s.angle_min = -3.14
            s.angle_increment = 0.4
            s.range_min = 0.05
            s.range_max = 8.0
            s.ranges = [4.0] * 16
            return s
        older, newer = (scan(0), scan(50000000))
        arrival = time.monotonic()

        class TF:

            def lookup_transform(self, target, source, stamp):
                if stamp.nanoseconds > 10000000000:
                    raise m.TransformException('newest transform not yet available')
                t = TransformStamped()
                t.transform.rotation.w = 1.0
                return t
        node = NS(cfg=replace(m.Config(), visualize=False, grid_size_m=2.0), pending_scans=deque([(older, arrival), (newer, arrival)], maxlen=12), history=deque([(10.0, np.zeros(4)), (10.05, np.zeros(4))]), grid_stamp=None, tf=TF())
        m.MPPINode.build_grid(node)
        self.assertEqual(node.grid_stamp, 10.0)
        self.assertEqual(len(node.pending_scans), 1)
        self.assertEqual(node.pending_scans[0][0].header.stamp.nanosec, 50000000)
        self.assertEqual(node.grid_received, arrival)

    def test_expired_scan_cannot_be_reused(self):
        s = LaserScan()
        s.header.stamp.sec = 10
        node = NS(cfg=m.Config(), pending_scans=deque([(s, time.monotonic() - 1)]), history=deque([(10.0, np.zeros(4))]), grid_stamp=None)
        m.MPPINode.build_grid(node)
        self.assertIsNone(node.grid_stamp)
if __name__ == '__main__':
    unittest.main()
