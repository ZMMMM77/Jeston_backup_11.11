# CMake generated Testfile for 
# Source directory: /home/nvidia/Roboracer_race2_MPPI-RRT-/rrt_mppi
# Build directory: /home/nvidia/Roboracer_race2_MPPI-RRT-/build/rrt_mppi
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(core_tests "/usr/bin/python3" "-u" "/opt/ros/jazzy/share/ament_cmake_test/cmake/run_test.py" "/home/nvidia/Roboracer_race2_MPPI-RRT-/build/rrt_mppi/test_results/rrt_mppi/core_tests.xunit.xml" "--package-name" "rrt_mppi" "--output-file" "/home/nvidia/Roboracer_race2_MPPI-RRT-/build/rrt_mppi/ament_cmake_pytest/core_tests.txt" "--append-env" "PYTHONPATH=/home/nvidia/Roboracer_race2_MPPI-RRT-/rrt_mppi/scripts" "--command" "/usr/bin/python3" "-u" "-m" "pytest" "/home/nvidia/Roboracer_race2_MPPI-RRT-/rrt_mppi/test" "-o" "cache_dir=/home/nvidia/Roboracer_race2_MPPI-RRT-/build/rrt_mppi/ament_cmake_pytest/core_tests/.cache" "--junit-xml=/home/nvidia/Roboracer_race2_MPPI-RRT-/build/rrt_mppi/test_results/rrt_mppi/core_tests.xunit.xml" "--junit-prefix=rrt_mppi")
set_tests_properties(core_tests PROPERTIES  LABELS "pytest" TIMEOUT "180" WORKING_DIRECTORY "/home/nvidia/Roboracer_race2_MPPI-RRT-/build/rrt_mppi" _BACKTRACE_TRIPLES "/opt/ros/jazzy/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/jazzy/share/ament_cmake_pytest/cmake/ament_add_pytest_test.cmake;177;ament_add_test;/home/nvidia/Roboracer_race2_MPPI-RRT-/rrt_mppi/CMakeLists.txt;9;ament_add_pytest_test;/home/nvidia/Roboracer_race2_MPPI-RRT-/rrt_mppi/CMakeLists.txt;0;")
