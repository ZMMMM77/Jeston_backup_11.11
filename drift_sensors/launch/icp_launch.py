"""Step 1: ICP lidar odometry only.

Aligns each /scan against a local map of recent scans and publishes the
body-frame motion as /odom_icp (pose in odom frame, twist in base_link).
The icp_odometry parameter block is copied from Roboracer-Final-Project
sensors_bringup.launch.py; only the IMU remap is left out until step 2.

Needs: sick_bringup_launch.py running (gives /scan, base_link->laser TF and
the VESC odom->base_link TF that ICP uses as its motion guess).

    ros2 launch drift_sensors icp_launch.py
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
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

            # Odometry strategy
            # 0=F2M (Frame-to-Map): builds local map, robust when single frames fail
            # 1=F2F (Frame-to-Frame): fails when car moves fast
            'Odom/Strategy':                 '0',

            # Primary guess: odom TF (VESC now, EKF in step 2).
            # GuessMotion=true as secondary: used when TF lookup is unavailable at startup.
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
            # at the current odom position instead of staying stale.
            'Odom/ResetCountdown':           '1',

            # Local map size for F2M
            'OdomF2M/MaxSize':               '2000',
        }],
        remappings=[
            ('scan', '/scan'),
            ('odom', '/odom_icp'),
        ],
    )

    return LaunchDescription([icp_odom_node])
