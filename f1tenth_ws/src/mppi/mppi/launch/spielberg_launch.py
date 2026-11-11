"""What the autograder runs on Spielberg (one lap):

    ros2 launch mppi spielberg_launch.py

Everything the graded run needs goes here: the nodes to start, the waypoints
to follow and the parameter values that suit Spielberg (levine_launch.py is
Levine's). Start your own nodes only: the simulator is already running.
"""
from pathlib import Path

from launch import LaunchDescription
from launch_ros.actions import Node

# scripts/mppi_node.py
EXECUTABLE = 'mppi_node.py'

# `track` tells the skeleton which waypoints to load; add this track's values
# for the other parameters your node declares, e.g. 'max_speed': 6.0, or give
# it a full .yaml config file
PARAMETERS = {
    # Path
    'track': 'spielberg',
    'waypoints_path': '',

    # Visualization
    'visualize': False,
    'visualize_samples': False,

    # MPPI sampling
    'T': 1024,
    'H': 20,
    'DT': 0.05,
    'INTEGRATOR': 'euler',
    'LAMBDA': 0.01,
    'U_STD': [1.0, 0.1],

    # Costs: states [x, y, yaw, v], inputs [a, steering]
    'Q': [5.0, 5.0, 1.0, 1.0],
    'Qf': [5.0, 5.0, 1.0, 1.0],
    'R': [0.01, 0.01],
    'Rd': [0.01, 1.0],

    # Vehicle and limits
    'WB': 0.33,
    'MIN_STEER': -0.4189,
    'MAX_STEER': 0.4189,
    'MIN_ACCEL': -3.0,
    'MAX_ACCEL': 3.0,
    'MIN_SPEED': 0.0,
    'MAX_SPEED': 6.0,

}


def generate_launch_description():
    mppi_python = Path.home() / '.venvs/mppi/bin/python3'
    return LaunchDescription([
        Node(
            package='mppi',
            executable=EXECUTABLE,
            prefix=[str(mppi_python)] if mppi_python.is_file() else [],
            output='screen',
            parameters=[PARAMETERS],
        ),
    ])
