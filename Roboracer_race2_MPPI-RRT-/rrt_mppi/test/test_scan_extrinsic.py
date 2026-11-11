import sys, time, unittest, math
from pathlib import Path
from types import SimpleNamespace as NS
from collections import deque
from dataclasses import replace
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import rrt_mppi_node as m
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TransformStamped

class ScanExtrinsic(unittest.TestCase):

    def test_fixed_extrinsic_uses_interpolated_scan_time_pose_without_global_tf(self):
        scan = LaserScan()
        scan.header.stamp.sec = 10
        scan.header.stamp.nanosec = 50000000
        scan.header.frame_id = 'car/laser'
        scan.angle_min = -1.0
        scan.angle_increment = 0.1
        scan.range_min = 0.05
        scan.range_max = 8.0
        scan.ranges = [4.0] * 20

        class TF:

            def lookup_transform(self, target, source, stamp):
                assert target == 'car/base_link' and source == 'car/laser' and (stamp.nanoseconds == 0)
                out = TransformStamped()
                out.transform.translation.x = 0.275
                out.transform.rotation.w = 1.0
                return out
        now = time.monotonic()
        c = replace(m.Config(), visualize=False, grid_size_m=2.0, pose_to_rear_axle_x_m=0.1, pose_to_rear_axle_y_m=0.02)
        node = NS(cfg=c, latest_odom=NS(child_frame_id='car/base_link'), pending_scans=deque([(scan, now)]), history=deque([(10.0, np.array([10.0, 20.0, math.pi / 2, 0.0])), (10.1, np.array([11.0, 20.0, math.pi / 2, 0.0]))]), grid_stamp=None, tf=TF())
        recorded = []

        def grid(*args):
            recorded.append(args)
            return np.zeros((40, 40), dtype=np.int8)
        with patch.object(m, 'scan_grid', side_effect=grid):
            m.MPPINode.build_grid(node)
        np.testing.assert_allclose(recorded[0][5], [10.52, 20.175, math.pi / 2], atol=1e-10)
        np.testing.assert_allclose(recorded[0][6], [10.5, 20.0, math.pi / 2], atol=1e-10)
        self.assertEqual(node.grid_stamp, 10.05)
        self.assertEqual(node.grid_received, now)
if __name__ == '__main__':
    unittest.main()
