"""What the autograder runs on levine_obs (the straight path, the turn and the full lap) and
for the obstacle checks:

    ros2 launch lab7_pkg levine_launch.py

Everything your planner needs goes here: one node or several, Python or C++,
and the parameter values you tuned. Start your own nodes only: the simulator
is already running.
"""
from launch import LaunchDescription
from launch_ros.actions import Node

# 'rrt_node.py' is scripts/rrt_node.py, 'rrt_node' is the C++
# src/rrt_node.cpp: name the one you wrote
EXECUTABLE = 'rrt_node.py'

# values for the parameters your node declares
# e.g. {'max_speed': 3.0} or give it a full .yaml config file
PARAMETERS = {

    'inflation_radius_m': 0.10, #radius of the robot's footprint
    'rrt_step_m': 0.5,  #how long each RRT step is in meters
    'rrt_goal_distance_m': 3.0, #从全局 CSV 选择前方 RRT 参考目标的距离     
    'goal_tolerance_m': 0.2, #distance from the goal to consider the goal reached
    'goal_sample_rate': 0.75, #probability of sampling the goal instead of a random point 

    'lookahead_m': 1.6,
    'straight_lookahead_m': 5.0,
    'curve_preview_m': 5.0,
    'max_speed_mps': 5.0,
    'speed_scale': 0.4,
}

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='lab7_pkg',
            executable=EXECUTABLE,
            output='screen',
            parameters=[PARAMETERS],
        ),
    ])

