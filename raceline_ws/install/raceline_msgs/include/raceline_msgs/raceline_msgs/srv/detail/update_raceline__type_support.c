// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "raceline_msgs/srv/detail/update_raceline__rosidl_typesupport_introspection_c.h"
#include "raceline_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "raceline_msgs/srv/detail/update_raceline__functions.h"
#include "raceline_msgs/srv/detail/update_raceline__struct.h"


// Include directives for member types
// Member `data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `format`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  raceline_msgs__srv__UpdateRaceline_Request__init(message_memory);
}

void raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_fini_function(void * message_memory)
{
  raceline_msgs__srv__UpdateRaceline_Request__fini(message_memory);
}

size_t raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__size_function__UpdateRaceline_Request__data(
  const void * untyped_member)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return member->size;
}

const void * raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Request__data(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void * raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Request__data(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__fetch_function__UpdateRaceline_Request__data(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const double * item =
    ((const double *)
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Request__data(untyped_member, index));
  double * value =
    (double *)(untyped_value);
  *value = *item;
}

void raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__assign_function__UpdateRaceline_Request__data(
  void * untyped_member, size_t index, const void * untyped_value)
{
  double * item =
    ((double *)
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Request__data(untyped_member, index));
  const double * value =
    (const double *)(untyped_value);
  *item = *value;
}

bool raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__resize_function__UpdateRaceline_Request__data(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  rosidl_runtime_c__double__Sequence__fini(member);
  return rosidl_runtime_c__double__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_member_array[4] = {
  {
    "data",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Request, data),  // bytes offset in struct
    NULL,  // default value
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__size_function__UpdateRaceline_Request__data,  // size() function pointer
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Request__data,  // get_const(index) function pointer
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Request__data,  // get(index) function pointer
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__fetch_function__UpdateRaceline_Request__data,  // fetch(index, &value) function pointer
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__assign_function__UpdateRaceline_Request__data,  // assign(index, value) function pointer
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__resize_function__UpdateRaceline_Request__data  // resize(index) function pointer
  },
  {
    "rows",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Request, rows),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "cols",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Request, cols),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "format",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Request, format),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_members = {
  "raceline_msgs__srv",  // message namespace
  "UpdateRaceline_Request",  // message name
  4,  // number of fields
  sizeof(raceline_msgs__srv__UpdateRaceline_Request),
  false,  // has_any_key_member_
  raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_member_array,  // message members
  raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_type_support_handle = {
  0,
  &raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_members,
  get_message_typesupport_handle_function,
  &raceline_msgs__srv__UpdateRaceline_Request__get_type_hash,
  &raceline_msgs__srv__UpdateRaceline_Request__get_type_description,
  &raceline_msgs__srv__UpdateRaceline_Request__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_raceline_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Request)() {
  if (!raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_type_support_handle.typesupport_identifier) {
    raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__rosidl_typesupport_introspection_c.h"
// already included above
// #include "raceline_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__functions.h"
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__struct.h"


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  raceline_msgs__srv__UpdateRaceline_Response__init(message_memory);
}

void raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_fini_function(void * message_memory)
{
  raceline_msgs__srv__UpdateRaceline_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_member_array[2] = {
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "message",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Response, message),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_members = {
  "raceline_msgs__srv",  // message namespace
  "UpdateRaceline_Response",  // message name
  2,  // number of fields
  sizeof(raceline_msgs__srv__UpdateRaceline_Response),
  false,  // has_any_key_member_
  raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_member_array,  // message members
  raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle = {
  0,
  &raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_members,
  get_message_typesupport_handle_function,
  &raceline_msgs__srv__UpdateRaceline_Response__get_type_hash,
  &raceline_msgs__srv__UpdateRaceline_Response__get_type_description,
  &raceline_msgs__srv__UpdateRaceline_Response__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_raceline_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Response)() {
  if (!raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle.typesupport_identifier) {
    raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__rosidl_typesupport_introspection_c.h"
// already included above
// #include "raceline_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__functions.h"
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__struct.h"


// Include directives for member types
// Member `info`
#include "service_msgs/msg/service_event_info.h"
// Member `info`
#include "service_msgs/msg/detail/service_event_info__rosidl_typesupport_introspection_c.h"
// Member `request`
// Member `response`
#include "raceline_msgs/srv/update_raceline.h"
// Member `request`
// Member `response`
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  raceline_msgs__srv__UpdateRaceline_Event__init(message_memory);
}

void raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_fini_function(void * message_memory)
{
  raceline_msgs__srv__UpdateRaceline_Event__fini(message_memory);
}

size_t raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__size_function__UpdateRaceline_Event__request(
  const void * untyped_member)
{
  const raceline_msgs__srv__UpdateRaceline_Request__Sequence * member =
    (const raceline_msgs__srv__UpdateRaceline_Request__Sequence *)(untyped_member);
  return member->size;
}

const void * raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Event__request(
  const void * untyped_member, size_t index)
{
  const raceline_msgs__srv__UpdateRaceline_Request__Sequence * member =
    (const raceline_msgs__srv__UpdateRaceline_Request__Sequence *)(untyped_member);
  return &member->data[index];
}

void * raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Event__request(
  void * untyped_member, size_t index)
{
  raceline_msgs__srv__UpdateRaceline_Request__Sequence * member =
    (raceline_msgs__srv__UpdateRaceline_Request__Sequence *)(untyped_member);
  return &member->data[index];
}

void raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__fetch_function__UpdateRaceline_Event__request(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const raceline_msgs__srv__UpdateRaceline_Request * item =
    ((const raceline_msgs__srv__UpdateRaceline_Request *)
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Event__request(untyped_member, index));
  raceline_msgs__srv__UpdateRaceline_Request * value =
    (raceline_msgs__srv__UpdateRaceline_Request *)(untyped_value);
  *value = *item;
}

void raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__assign_function__UpdateRaceline_Event__request(
  void * untyped_member, size_t index, const void * untyped_value)
{
  raceline_msgs__srv__UpdateRaceline_Request * item =
    ((raceline_msgs__srv__UpdateRaceline_Request *)
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Event__request(untyped_member, index));
  const raceline_msgs__srv__UpdateRaceline_Request * value =
    (const raceline_msgs__srv__UpdateRaceline_Request *)(untyped_value);
  *item = *value;
}

bool raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__resize_function__UpdateRaceline_Event__request(
  void * untyped_member, size_t size)
{
  raceline_msgs__srv__UpdateRaceline_Request__Sequence * member =
    (raceline_msgs__srv__UpdateRaceline_Request__Sequence *)(untyped_member);
  raceline_msgs__srv__UpdateRaceline_Request__Sequence__fini(member);
  return raceline_msgs__srv__UpdateRaceline_Request__Sequence__init(member, size);
}

size_t raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__size_function__UpdateRaceline_Event__response(
  const void * untyped_member)
{
  const raceline_msgs__srv__UpdateRaceline_Response__Sequence * member =
    (const raceline_msgs__srv__UpdateRaceline_Response__Sequence *)(untyped_member);
  return member->size;
}

const void * raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Event__response(
  const void * untyped_member, size_t index)
{
  const raceline_msgs__srv__UpdateRaceline_Response__Sequence * member =
    (const raceline_msgs__srv__UpdateRaceline_Response__Sequence *)(untyped_member);
  return &member->data[index];
}

void * raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Event__response(
  void * untyped_member, size_t index)
{
  raceline_msgs__srv__UpdateRaceline_Response__Sequence * member =
    (raceline_msgs__srv__UpdateRaceline_Response__Sequence *)(untyped_member);
  return &member->data[index];
}

void raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__fetch_function__UpdateRaceline_Event__response(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const raceline_msgs__srv__UpdateRaceline_Response * item =
    ((const raceline_msgs__srv__UpdateRaceline_Response *)
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Event__response(untyped_member, index));
  raceline_msgs__srv__UpdateRaceline_Response * value =
    (raceline_msgs__srv__UpdateRaceline_Response *)(untyped_value);
  *value = *item;
}

void raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__assign_function__UpdateRaceline_Event__response(
  void * untyped_member, size_t index, const void * untyped_value)
{
  raceline_msgs__srv__UpdateRaceline_Response * item =
    ((raceline_msgs__srv__UpdateRaceline_Response *)
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Event__response(untyped_member, index));
  const raceline_msgs__srv__UpdateRaceline_Response * value =
    (const raceline_msgs__srv__UpdateRaceline_Response *)(untyped_value);
  *item = *value;
}

bool raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__resize_function__UpdateRaceline_Event__response(
  void * untyped_member, size_t size)
{
  raceline_msgs__srv__UpdateRaceline_Response__Sequence * member =
    (raceline_msgs__srv__UpdateRaceline_Response__Sequence *)(untyped_member);
  raceline_msgs__srv__UpdateRaceline_Response__Sequence__fini(member);
  return raceline_msgs__srv__UpdateRaceline_Response__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_member_array[3] = {
  {
    "info",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Event, info),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "request",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Event, request),  // bytes offset in struct
    NULL,  // default value
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__size_function__UpdateRaceline_Event__request,  // size() function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Event__request,  // get_const(index) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Event__request,  // get(index) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__fetch_function__UpdateRaceline_Event__request,  // fetch(index, &value) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__assign_function__UpdateRaceline_Event__request,  // assign(index, value) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__resize_function__UpdateRaceline_Event__request  // resize(index) function pointer
  },
  {
    "response",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(raceline_msgs__srv__UpdateRaceline_Event, response),  // bytes offset in struct
    NULL,  // default value
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__size_function__UpdateRaceline_Event__response,  // size() function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_const_function__UpdateRaceline_Event__response,  // get_const(index) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__get_function__UpdateRaceline_Event__response,  // get(index) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__fetch_function__UpdateRaceline_Event__response,  // fetch(index, &value) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__assign_function__UpdateRaceline_Event__response,  // assign(index, value) function pointer
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__resize_function__UpdateRaceline_Event__response  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_members = {
  "raceline_msgs__srv",  // message namespace
  "UpdateRaceline_Event",  // message name
  3,  // number of fields
  sizeof(raceline_msgs__srv__UpdateRaceline_Event),
  false,  // has_any_key_member_
  raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_member_array,  // message members
  raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_init_function,  // function to initialize message memory (memory has to be allocated)
  raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_type_support_handle = {
  0,
  &raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_members,
  get_message_typesupport_handle_function,
  &raceline_msgs__srv__UpdateRaceline_Event__get_type_hash,
  &raceline_msgs__srv__UpdateRaceline_Event__get_type_description,
  &raceline_msgs__srv__UpdateRaceline_Event__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_raceline_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Event)() {
  raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, service_msgs, msg, ServiceEventInfo)();
  raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Request)();
  raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_member_array[2].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Response)();
  if (!raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_type_support_handle.typesupport_identifier) {
    raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "raceline_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_members = {
  "raceline_msgs__srv",  // service namespace
  "UpdateRaceline",  // service name
  // the following fields are initialized below on first access
  NULL,  // request message
  // raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_type_support_handle,
  NULL,  // response message
  // raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle
  NULL  // event_message
  // raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle
};


static rosidl_service_type_support_t raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_type_support_handle = {
  0,
  &raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_members,
  get_service_typesupport_handle_function,
  &raceline_msgs__srv__UpdateRaceline_Request__rosidl_typesupport_introspection_c__UpdateRaceline_Request_message_type_support_handle,
  &raceline_msgs__srv__UpdateRaceline_Response__rosidl_typesupport_introspection_c__UpdateRaceline_Response_message_type_support_handle,
  &raceline_msgs__srv__UpdateRaceline_Event__rosidl_typesupport_introspection_c__UpdateRaceline_Event_message_type_support_handle,
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_CREATE_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    raceline_msgs,
    srv,
    UpdateRaceline
  ),
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_DESTROY_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    raceline_msgs,
    srv,
    UpdateRaceline
  ),
  &raceline_msgs__srv__UpdateRaceline__get_type_hash,
  &raceline_msgs__srv__UpdateRaceline__get_type_description,
  &raceline_msgs__srv__UpdateRaceline__get_type_description_sources,
};

// Forward declaration of message type support functions for service members
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Request)(void);

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Response)(void);

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Event)(void);

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_raceline_msgs
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline)(void) {
  if (!raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_type_support_handle.typesupport_identifier) {
    raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Response)()->data;
  }
  if (!service_members->event_members_) {
    service_members->event_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, raceline_msgs, srv, UpdateRaceline_Event)()->data;
  }

  return &raceline_msgs__srv__detail__update_raceline__rosidl_typesupport_introspection_c__UpdateRaceline_service_type_support_handle;
}
