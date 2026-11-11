"""Pure NumPy MPPI. Save tuning edits and restart; no rebuild needed."""
import os,sys
from pathlib import Path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

PARAMETERS = {'MAX_SPEED': 6.0,
 'MAX_ACCEL': 3.0,
 'speed_scale': 1.0,
 'T': 512,
 'H': 10,
 'DT': 0.05,
 'LAMBDA': 0.04,
 'U_STD': [3.0, 0.07],
 'Q': [4.0, 4.0, 1.5, 5.0],
 'Qf': [4.0, 4.0, 1.5, 5.0],
 'R': [0.01, 2.0],
 'Rd': [0.01, 2.0],
 'visualize': True,
 'reference_distance_m': 3.0}

def generate_launch_description():
    clock={'use_sim_time':ParameterValue(LaunchConfiguration('use_sim_time'),value_type=bool)}
    venv=Path.home()/'.venvs/mppi/bin/python3'
    python=os.environ.get('RRT_MPPI_PYTHON',str(venv) if venv.is_file() else sys.executable)
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time',default_value='false'),
        DeclareLaunchArgument('python_executable',default_value=python),
        Node(package='rrt_mppi',executable='rrt_mppi_node.py',arguments=['--drive-guard'],
             prefix=[LaunchConfiguration('python_executable')],output='screen',
             parameters=[{'max_speed':PARAMETERS['MAX_SPEED']},clock]),
        Node(package='rrt_mppi',executable='rrt_mppi_node.py',arguments=['--realcar'],
             prefix=[LaunchConfiguration('python_executable')],output='screen',
             parameters=[PARAMETERS,{'control_rate_hz':1.0/PARAMETERS['DT']},clock]),
    ])
