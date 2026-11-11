# Basic NumPy MPPI with LiDAR soft proximity cost

Current flow: PF odometry + unchanged CSV -> Gaussian MPPI rollouts -> tracking,
control/slew and finite LiDAR proximity costs -> weighted controls -> /drive.
There is no collision rejection, final trajectory gate, braking gate, occupancy
grid boundary, detour sampler, sector crop, obstacle marker or speed smoother.
All usable scan angles are considered; obstacle_range_m still limits hit range.
Soft costs do not guarantee collision avoidance. Data-staleness/nonfinite checks
remain. Existing mux, Ackermann conversion and VESC nodes are unchanged.

Fixed real-car interfaces/defaults live in mppi_node.py. Launch contains tuning
parameters only. The user-selected pose offset and tuning values were retained.
/mppi/sampled_rollouts displays all sampled paths before weighting; no on-disk
recording is enabled. Reference/prediction/global-path topics are unchanged.

Build: colcon build --symlink-install --packages-select mppi
Start: source install/setup.bash && ros2 launch mppi levine_launch.py
No JAX. Runtime dependencies: NumPy, SciPy and the declared ROS packages.
