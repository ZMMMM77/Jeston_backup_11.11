"""What the autograder runs on Levine (levine_blocked, three laps, and the pose checks):

    ros2 launch mpc levine_launch.py

Everything the graded run needs goes here: one node or several, Python or
C++, the waypoints to follow and the parameter values that suit Levine
(spielberg_launch.py is Spielberg's). Start your own nodes only: the
simulator is already running.
"""
from launch import LaunchDescription
from launch_ros.actions import Node

# 'mpc_node.py' is scripts/mpc_node.py, 'mpc_node' is the C++
# src/mpc_node.cpp: name the one you wrote
EXECUTABLE = 'mpc_node.py'

# `track` tells the skeleton which waypoints to load; add this track's values
# for the other parameters your node declares, e.g. 'max_speed': 6.0, or give
# it a full .yaml config file
PARAMETERS = {
    'track': '0842pm',
    'max_speed': 4.0,
    'Rk': [0.01, 120.0],  # [acceleration, steering angle]
    'Rdk': [0.01, 250.0],  # [acceleration, steering angle]
    'Qk': [13.5, 13.5, 5.5, 13.0],  # [x, y, speed, yaw]
    'Qfk': [13.5, 13.5, 5.5, 13.0],  # [x, y, speed, yaw]
}


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='mpc',
            executable=EXECUTABLE,
            output='screen',
            parameters=[PARAMETERS],
            remappings=[('/ego_racecar/odom', '/pf/pose/odom')],
        ),
    ])
