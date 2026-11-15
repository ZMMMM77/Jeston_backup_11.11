"""Full pipeline: D435i IMU + ICP -> EKF -> particle filter -> /drift/state_odom.

Before this: `source ~/realsense_ws/install/setup.bash` (camera driver with IMU) and start the
car with the EKF-owned TF:
    ros2 launch f1tenth_stack sick_bringup_launch.py vesc_config:=/home/nvidia/drift_sensors/config/vesc.yaml
Then, with the car still for 2 s:
    ros2 launch drift_sensors drift_sensors_launch.py
Node parameter blocks are copied from Roboracer-Final-Project sensors_bringup.launch.py.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml


def generate_launch_description():
    share = get_package_share_directory('drift_sensors')
    ekf_config = os.path.join(share, 'config', 'ekf.yaml')
    localize_config = os.path.join(share, 'config', 'localize.yaml')
    map_name = yaml.safe_load(open(localize_config))['map_server']['ros__parameters']['map']

    start_camera = DeclareLaunchArgument('start_camera', default_value='true',
                                         description='launch the D435i driver (IMU only)')

    # ── Camera: IMU streams only ─────────────────────────────────────────────
    realsense_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')),
        launch_arguments={
            'enable_gyro':      'true',
            'enable_accel':     'true',
            'unite_imu_method': '2',
            'gyro_fps':         '200',
            'accel_fps':        '250',
            'enable_color':     'false',
            'enable_depth':     'false',
            'enable_infra1':    'false',
            'enable_infra2':    'false',
        }.items(),
        condition=IfCondition(LaunchConfiguration('start_camera')),
    )

    imu_node = Node(
        package='drift_sensors',
        executable='d435i_imu',
        name='d435i_imu',
        output='screen',
    )

    # ── ICP Odometry ─────────────────────────────────────────────────────────
    icp_odom_node = Node(
        package='rtabmap_odom',
        executable='icp_odometry',
        name='icp_odometry',
        output='screen',
        parameters=[{
            'frame_id':                      'base_link',
            'odom_frame_id':                 'odom',
            'publish_tf':                    False,
            'approx_sync':                   True,
            'queue_size':                    10,

            # Registration
            'Reg/Strategy':                  '1',      # ICP
            'Reg/Force3DoF':                 'true',   # 2D plane only

            # 0=F2M (Frame-to-Map): builds local map, robust when single frames fail
            'Odom/Strategy':                 '0',

            # Primary guess: EKF odom TF. GuessMotion=true as secondary at startup.
            'guess_frame_id':                'odom',
            'Odom/GuessMotion':              'true',
            'Odom/GuessSmoothingDelay':      '0.1',

            # ICP params
            'Icp/MaxTranslation':            '1.0',    # 1m/frame handles 5m/s at 5Hz
            'Icp/MaxRotation':               '1.57',   # 90 deg/frame
            'Icp/VoxelSize':                 '0.05',
            'Icp/MaxCorrespondenceDistance': '0.15',
            'Icp/Iterations':                '50',

            # Reset immediately after any failure so the F2M map re-bootstraps
            'Odom/ResetCountdown':           '1',

            # Local map size for F2M
            'OdomF2M/MaxSize':               '2000',
        }],
        remappings=[
            ('scan', '/scan'),
            ('odom', '/odom_icp'),
            ('imu',  '/imu/data'),
        ],
    )

    # ── EKF: /odom_icp + /imu/data (+ /odom) -> /odom_ekf and odom->base_link TF ──
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config],
        remappings=[('odometry/filtered', '/odom_ekf')],
    )

    # ── Particle filter: predicts from /odom_ekf, publishes map->odom ────────
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[{'yaml_filename': os.path.join(share, 'maps', map_name + '.yaml')},
                    {'topic': 'map'},
                    {'frame_id': 'map'}],
    )
    lifecycle_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{'autostart': True}, {'node_names': ['map_server']}],
    )
    pf_node = Node(
        package='drift_sensors',
        executable='particle_filter',
        name='particle_filter',
        output='screen',
        parameters=[localize_config],
    )

    # ── PF pose + EKF twist -> /drift/state_odom ─────────────────────────────
    merge_node = Node(
        package='drift_sensors',
        executable='state_merge',
        name='drift_state_merge',
        output='screen',
    )

    return LaunchDescription([
        start_camera,
        realsense_node,
        imu_node,
        icp_odom_node,
        ekf_node,
        lifecycle_node,
        map_server_node,
        pf_node,
        merge_node,
    ])
