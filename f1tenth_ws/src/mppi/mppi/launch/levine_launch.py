"""Real-car NumPy MPPI + LiDAR soft cost: tunable settings only."""
import os
import sys
from launch import LaunchDescription
from launch_ros.actions import Node

PARAMETERS = {
    'waypoints_path': 'levine1.csv',
    "track": "not race",
    'T': 128,
    'H': 20,
    'DT': 0.05,
    'LAMBDA': 0.04,
    'U_STD': [2.0, 0.1],
    'Q': [50.0, 50.0, 5.0, 5.0],
    'Qf': [50.0, 50.0, 5.0, 5.0],
    'R': [0.01, 0.7],
    'Rd': [0.01, 1.0],
    'MIN_SPEED': 2.0,
    'MAX_SPEED': 6.0,
    'obstacle_avoidance': True,
    'obstacle_range_m': 2.0,
    'obstacle_weight': 100.0,
    'obstacle_clearance_m': 0.01,
    'visualize_samples': True,
}

def generate_launch_description():
    return LaunchDescription([
        Node(package='mppi', executable='mppi_node.py',
             prefix=[os.environ.get('MPPI_PYTHON', sys.executable)],
             output='screen', parameters=[PARAMETERS]),
    ])
