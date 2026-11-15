# drift_sensors

Velocity estimation for the drift policy, built in place (build/install/log stay in this folder).
Adapted from Roboracer-Final-Project `sensors_bringup`; our particle filter stays in `~/RL_drifting_input`.

Pipeline (see docs diagram): lidar -> ICP odometry, D435i IMU -> remap, both -> EKF (`/odom_ekf`)
-> particle filter predicts from it -> state merge -> `/drift/state_odom` for `drift_policy`.

## Build

    cd ~/drift_sensors
    colcon build
    source install/setup.bash

## Step 1: ICP only

    ros2 launch drift_sensors icp_launch.py      # after sick_bringup_launch.py
    ros2 topic hz /odom_icp
    ros2 topic echo /odom_icp --field twist.twist

Dependencies (apt): ros-jazzy-rtabmap-odom, ros-jazzy-robot-localization
