"""Offline interface checks: execute selected adapter definitions without nodes/JAX.

These check ROS message semantics and launch configuration; they do not replace
numerical MPPI tests, runtime TF checks or physical vehicle validation.
"""
import ast
import sys
import csv
import math
import tempfile
import time
import unittest
from collections import deque
from dataclasses import dataclass, fields, replace
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts/rrt_mppi_node.py'
sys.path.insert(0, str(ROOT / 'scripts'))
from planning_common import Config, wrap
tree = ast.parse(SOURCE.read_text())
selected = []
names = {'Config', 'canonical_frame', 'waypoint_file', 'load_waypoints', 'yaw', 'seconds', 'wrap'}
for node in tree.body:
    if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names:
        node.decorator_list = [] if node.name != 'Config' else node.decorator_list
        selected.append(node)
    if isinstance(node, ast.ClassDef) and node.name == 'MPPINode':
        selected.extend((n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in ('transform_pose', 'odom', 'build_grid')))

class TransformException(Exception):
    pass

class Time:

    @classmethod
    def from_msg(cls, stamp):
        return stamp
NSPACE = dict(Config=Config, wrap=wrap, np=np, math=math, csv=csv, time=time, deque=deque, FilePath=Path, dataclass=dataclass, fields=fields, replace=replace, TransformException=TransformException, Time=Time)
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), NSPACE)
Config = NSPACE['Config']

def quaternion(angle):
    return NS(w=math.cos(angle / 2), x=0.0, y=0.0, z=math.sin(angle / 2))

def pf_message():
    return NS(header=NS(frame_id='/map', stamp=NS(sec=10, nanosec=0)), child_frame_id='', pose=NS(pose=NS(position=NS(x=1.0, y=2.0), orientation=quaternion(math.pi / 2))), twist=NS(twist=NS(linear=NS(x=0.7, y=0.0))))

class RealCarAdapter(unittest.TestCase):

    def test_pf_map_slash_does_not_require_an_invalid_tf_lookup(self):
        node = NS(cfg=Config())
        pose = np.array([1.0, 2.0, 0.1])
        np.testing.assert_array_equal(NSPACE['transform_pose'](node, pose, '/map', NS()), pose)

    def test_laser_origin_pf_pose_becomes_rear_axle_and_scan_returns_to_laser(self):
        c = replace(Config(), odom_pose_frame='laser', pose_to_rear_axle_x_m=-0.27, visualize=False, grid_size_m=2.0)
        node = NS(cfg=c, odom_stamp=None, history=deque())
        node.transform_pose = lambda *args: NSPACE['transform_pose'](node, *args)
        NSPACE['odom'](node, pf_message())
        np.testing.assert_allclose(node.state, [1.0, 1.73, math.pi / 2, 0.7], atol=1e-12)
        scan = NS(header=NS(frame_id='/laser', stamp=NS(sec=10, nanosec=0)), ranges=[4.0] * 20, angle_min=-1.0, angle_increment=0.1, range_min=0.05, range_max=8.0)
        node.pending_scans = deque([(scan, time.monotonic())])
        node.grid_stamp = None
        captured = []

        def grid(*args):
            captured.append(args)
            return np.zeros((40, 40), dtype=np.int8)
        NSPACE['scan_grid'] = grid
        NSPACE['build_grid'](node)
        np.testing.assert_allclose(captured[0][5], [1.0, 2.0, math.pi / 2], atol=1e-12)
        np.testing.assert_allclose(captured[0][6], [1.0, 1.73, math.pi / 2], atol=1e-12)

    def test_non_map_frames_are_normalized_before_tf_lookup(self):
        calls = []

        class TF:

            def lookup_transform(self, target, source, stamp):
                calls.append((target, source))
                return NS(transform=NS(translation=NS(x=2.0, y=3.0), rotation=quaternion(0.0)))
        node = NS(cfg=Config(), tf=TF())
        result = NSPACE['transform_pose'](node, np.array([1.0, 2.0, 0.0]), '/odom', NS())
        self.assertEqual(calls, [('map', 'odom')])
        np.testing.assert_allclose(result, [3.0, 5.0, 0.0])

    def test_empty_frame_is_rejected(self):
        with self.assertRaises(TransformException):
            NSPACE['transform_pose'](NS(cfg=Config()), np.zeros(3), '', NS())

    def test_csv_name_resolves_in_package_not_working_directory(self):
        result = NSPACE['waypoint_file']('race.csv', 'race', '/package/share/rrt_mppi')
        self.assertEqual(result, Path('/package/share/rrt_mppi/waypoints/race.csv'))
        self.assertEqual(NSPACE['waypoint_file']('/home/nvidia/race.csv', 'race', '/share'), Path('/home/nvidia/race.csv'))

    def test_seven_column_race_csv_loads_xy_heading_speed(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'race.csv'
            p.write_text('# x,y,v,s,psi,kappa,ax\n0,0,2,0,0,0,0\n1,0,3,1,0,0,0\n1,1,4,2,1.57,0,0\n')
            waypoints = NSPACE['load_waypoints'](p)
            self.assertEqual(waypoints.shape, (3, 4))
            np.testing.assert_array_equal(waypoints[:, 3], [2.0, 3.0, 4.0])

    def test_realcar_launch_uses_localization_and_mux_input(self):
        text = (ROOT / 'launch/levine_launch.py').read_text()
        params = {}
        for node in ast.parse(text).body:
            if isinstance(node, ast.Assign) and any((isinstance(t, ast.Name) and t.id == 'PARAMETERS' for t in node.targets)):
                params = ast.literal_eval(node.value)
        profile = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'realcar_config'))
        ns = dict(NSPACE, Config=Config, replace=replace)
        exec(compile(ast.Module(body=[profile], type_ignores=[]), str(SOURCE), 'exec'), ns)
        from dataclasses import asdict
        params = {**asdict(ns['realcar_config']()), **params}
        self.assertEqual(params['waypoints_path'], 'race.csv')
        self.assertEqual(params['odom_topic'], '/pf/pose/odom')
        self.assertEqual(params['odom_pose_frame'], 'laser')
        self.assertEqual(params['pose_to_rear_axle_x_m'], -0.27)
        self.assertEqual(params['scan_topic'], '/scan')
        self.assertEqual(params['drive_topic'], '/drive')
        Config(**params).validate()
if __name__ == '__main__':
    unittest.main()
