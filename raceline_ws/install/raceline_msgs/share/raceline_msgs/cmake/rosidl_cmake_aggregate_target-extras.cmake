# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target raceline_msgs::raceline_msgs
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${raceline_msgs_TARGETS}.
if(raceline_msgs_TARGETS AND NOT TARGET raceline_msgs::raceline_msgs)
  add_library(raceline_msgs::raceline_msgs INTERFACE IMPORTED)
  set_target_properties(raceline_msgs::raceline_msgs PROPERTIES
    INTERFACE_LINK_LIBRARIES "${raceline_msgs_TARGETS}")
endif()
