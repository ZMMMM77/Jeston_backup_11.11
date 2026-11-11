# Pure NumPy MPPI

The runtime contains no RRT planner, worker, switch or search parameters.
- scripts/mppi.py: independent numerical MPPI (no ROS dependency).
- scripts/planning_common.py: configuration, footprint collision and CSV reference helpers.
- scripts/rrt_mppi_node.py: ROS sensors, MPPI, visualization and independent drive watchdog.

The historical package/executable names are retained so existing commands work.

```bash
source /opt/ros/jazzy/setup.bash
source /home/nvidia/f1tenth_ws/install/setup.bash
cd /home/nvidia/Roboracer_race2_MPPI-RRT-
colcon build --symlink-install --packages-select rrt_mppi
source install/setup.bash
ros2 launch rrt_mppi levine_launch.py
```

Edit launch/levine_launch.py for MPPI tuning. Existing Python/launch/CSV edits
need only saving and restarting the controller, without another build.
The route is race.csv; fixed real-car interfaces are in realcar_config().
JAX is not required. Localization, drivers and Foxglove are started separately.

Display /rrt_mppi/display in Foxglove (map frame), disabling duplicate old Path layers:
- Dark grey dashed global CSV route.
- Blue reference points/line and a larger reference horizon endpoint.
- Orange predicted points/line and a larger predicted endpoint.
- Red measured vehicle position and measured motion direction.
- MPPI label. No historical trail, search tree or sampled rollout cloud.

Each predicted rollout starts at the measured state passed into that control update.
The larger endpoint is the end of the H*DT prediction horizon, not the final CSV lap goal.
Stale sensors, no safe rollout or a missed deadline still request a stop.
Both swept-body and terminal-braking checks and the drive watchdog remain active.
Drive output still passes through the existing mux; this change does not alter priorities.

Offline checks do not start nodes or publish drive commands:
```bash
python3 -m unittest discover -s rrt_mppi/test -v
```
