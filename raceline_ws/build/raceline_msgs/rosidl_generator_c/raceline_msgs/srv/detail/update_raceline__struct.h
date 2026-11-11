// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "raceline_msgs/srv/update_raceline.h"


#ifndef RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__STRUCT_H_
#define RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'data'
#include "rosidl_runtime_c/primitives_sequence.h"
// Member 'format'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/UpdateRaceline in the package raceline_msgs.
typedef struct raceline_msgs__srv__UpdateRaceline_Request
{
  /// flattened row-major
  rosidl_runtime_c__double__Sequence data;
  uint32_t rows;
  uint32_t cols;
  /// "pure_pursuit" (cols=4) or "mppi" (cols=9)
  rosidl_runtime_c__String format;
} raceline_msgs__srv__UpdateRaceline_Request;

// Struct for a sequence of raceline_msgs__srv__UpdateRaceline_Request.
typedef struct raceline_msgs__srv__UpdateRaceline_Request__Sequence
{
  raceline_msgs__srv__UpdateRaceline_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} raceline_msgs__srv__UpdateRaceline_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/UpdateRaceline in the package raceline_msgs.
typedef struct raceline_msgs__srv__UpdateRaceline_Response
{
  bool success;
  rosidl_runtime_c__String message;
} raceline_msgs__srv__UpdateRaceline_Response;

// Struct for a sequence of raceline_msgs__srv__UpdateRaceline_Response.
typedef struct raceline_msgs__srv__UpdateRaceline_Response__Sequence
{
  raceline_msgs__srv__UpdateRaceline_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} raceline_msgs__srv__UpdateRaceline_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  raceline_msgs__srv__UpdateRaceline_Event__request__MAX_SIZE = 1
};
// response
enum
{
  raceline_msgs__srv__UpdateRaceline_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/UpdateRaceline in the package raceline_msgs.
typedef struct raceline_msgs__srv__UpdateRaceline_Event
{
  service_msgs__msg__ServiceEventInfo info;
  raceline_msgs__srv__UpdateRaceline_Request__Sequence request;
  raceline_msgs__srv__UpdateRaceline_Response__Sequence response;
} raceline_msgs__srv__UpdateRaceline_Event;

// Struct for a sequence of raceline_msgs__srv__UpdateRaceline_Event.
typedef struct raceline_msgs__srv__UpdateRaceline_Event__Sequence
{
  raceline_msgs__srv__UpdateRaceline_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} raceline_msgs__srv__UpdateRaceline_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__STRUCT_H_
