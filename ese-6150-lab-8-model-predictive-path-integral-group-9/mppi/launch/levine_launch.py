"""Real-car NumPy MPPI + LiDAR soft cost: tunable settings only."""
import os
import sys
from launch import LaunchDescription
from launch_ros.actions import Node

PARAMETERS = {
    'waypoints_path': 'levine.csv',
    'T': 512,
    'H': 15,
    'DT': 0.1,
    'LAMBDA': 0.06,
    'U_STD': [2.0, 0.12],
    'Q': [12.0, 12.0, 4.0, 4.0],
    'Qf': [10.0, 10.0, 4.0, 4.0],
    'R': [0.003, 0.5],
    'Rd': [0.003, 0.5],
    'MIN_SPEED': 1.0,
    'MAX_SPEED': 10.0,
    'obstacle_avoidance': True,
    'obstacle_range_m': 2.5,
    'obstacle_half_angle_deg': 30.0,  # each side of forward; total FOV = 90 deg
    'obstacle_weight': 40.0,
    'obstacle_clearance_m': 0.05,
    'visualize_samples': False,
}

def generate_launch_description():
    return LaunchDescription([
        Node(package='mppi', executable='mppi_node.py',
             prefix=[os.environ.get('MPPI_PYTHON', sys.executable)],
             output='screen', parameters=[PARAMETERS]),
    ])
