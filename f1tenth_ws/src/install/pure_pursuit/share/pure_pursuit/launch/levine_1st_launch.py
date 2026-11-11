"""This is the launch file used by the autograder to run on Levine (levine_blocked, three laps):

    ros2 launch pure_pursuit levine_launch.py

Use this to launch the nodes you need for your pure-pursuit implementation and pass in any parameters specified
for this track (spielberg_launch.py is Spielberg's). Do NOT run the simulator here as the autograder will 
launch it separately
"""
from launch import LaunchDescription
from launch_ros.actions import Node

# 'pure_pursuit_node.py' is scripts/pure_pursuit_node.py, 'pure_pursuit_node'
# is the C++ src/pure_pursuit_node.cpp: name the one you wrote
EXECUTABLE = 'pure_pursuit_node.py'

# this map's values for the parameters your node declares
# e.g. {'max_speed': 6.0} or give it a full .yaml config file

PARAMETERS = {
    'track': '0842pm',
    'lookahead_m': 0.65,
    'straight_lookahead_m':2.5,
    'curve_preview_m': 4.0,
    'curve_kappa_low': 0.05,
    'curve_kappa_high': 1.5,
    'lookahead_shrink_rate_mps': 3.0,
    'lookahead_grow_rate_mps': 1.0,
    'speed_scale': 1.04,
    'max_speed_mps': 6.0,
    'pose_topic': "/pf/pose/odom",
}

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pure_pursuit',
            executable=EXECUTABLE,
            output='screen',
            parameters=[PARAMETERS],
        ),
    ])
