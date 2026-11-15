"""PF pose + VESC IMU -> /drift/state_odom for the drift policy.

Start after the car bringup and localize_launch.py, with the car still for 2 s:
    ros2 launch rl_drifting_input state_estimator_launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(get_package_share_directory('rl_drifting_input'), 'config', 'state_estimator.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('estimator_config', default_value=config,
                              description='state_estimator_node parameters'),
        Node(
            package='rl_drifting_input',
            executable='state_estimator',
            name='drift_state_estimator',
            output='screen',
            parameters=[LaunchConfiguration('estimator_config')],
        ),
    ])
