// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice
#include "raceline_msgs/srv/detail/update_raceline__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `format`
#include "rosidl_runtime_c/string_functions.h"

bool
raceline_msgs__srv__UpdateRaceline_Request__init(raceline_msgs__srv__UpdateRaceline_Request * msg)
{
  if (!msg) {
    return false;
  }
  // data
  if (!rosidl_runtime_c__double__Sequence__init(&msg->data, 0)) {
    raceline_msgs__srv__UpdateRaceline_Request__fini(msg);
    return false;
  }
  // rows
  // cols
  // format
  if (!rosidl_runtime_c__String__init(&msg->format)) {
    raceline_msgs__srv__UpdateRaceline_Request__fini(msg);
    return false;
  }
  return true;
}

void
raceline_msgs__srv__UpdateRaceline_Request__fini(raceline_msgs__srv__UpdateRaceline_Request * msg)
{
  if (!msg) {
    return;
  }
  // data
  rosidl_runtime_c__double__Sequence__fini(&msg->data);
  // rows
  // cols
  // format
  rosidl_runtime_c__String__fini(&msg->format);
}

bool
raceline_msgs__srv__UpdateRaceline_Request__are_equal(const raceline_msgs__srv__UpdateRaceline_Request * lhs, const raceline_msgs__srv__UpdateRaceline_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // data
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->data), &(rhs->data)))
  {
    return false;
  }
  // rows
  if (lhs->rows != rhs->rows) {
    return false;
  }
  // cols
  if (lhs->cols != rhs->cols) {
    return false;
  }
  // format
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->format), &(rhs->format)))
  {
    return false;
  }
  return true;
}

bool
raceline_msgs__srv__UpdateRaceline_Request__copy(
  const raceline_msgs__srv__UpdateRaceline_Request * input,
  raceline_msgs__srv__UpdateRaceline_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // data
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->data), &(output->data)))
  {
    return false;
  }
  // rows
  output->rows = input->rows;
  // cols
  output->cols = input->cols;
  // format
  if (!rosidl_runtime_c__String__copy(
      &(input->format), &(output->format)))
  {
    return false;
  }
  return true;
}

raceline_msgs__srv__UpdateRaceline_Request *
raceline_msgs__srv__UpdateRaceline_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Request * msg = (raceline_msgs__srv__UpdateRaceline_Request *)allocator.allocate(sizeof(raceline_msgs__srv__UpdateRaceline_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(raceline_msgs__srv__UpdateRaceline_Request));
  bool success = raceline_msgs__srv__UpdateRaceline_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
raceline_msgs__srv__UpdateRaceline_Request__destroy(raceline_msgs__srv__UpdateRaceline_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    raceline_msgs__srv__UpdateRaceline_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
raceline_msgs__srv__UpdateRaceline_Request__Sequence__init(raceline_msgs__srv__UpdateRaceline_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Request * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(raceline_msgs__srv__UpdateRaceline_Request)) {
      return false;
    }
    data = (raceline_msgs__srv__UpdateRaceline_Request *)allocator.zero_allocate(size, sizeof(raceline_msgs__srv__UpdateRaceline_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = raceline_msgs__srv__UpdateRaceline_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        raceline_msgs__srv__UpdateRaceline_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
raceline_msgs__srv__UpdateRaceline_Request__Sequence__fini(raceline_msgs__srv__UpdateRaceline_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      raceline_msgs__srv__UpdateRaceline_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

raceline_msgs__srv__UpdateRaceline_Request__Sequence *
raceline_msgs__srv__UpdateRaceline_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Request__Sequence * array = (raceline_msgs__srv__UpdateRaceline_Request__Sequence *)allocator.allocate(sizeof(raceline_msgs__srv__UpdateRaceline_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = raceline_msgs__srv__UpdateRaceline_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
raceline_msgs__srv__UpdateRaceline_Request__Sequence__destroy(raceline_msgs__srv__UpdateRaceline_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    raceline_msgs__srv__UpdateRaceline_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
raceline_msgs__srv__UpdateRaceline_Request__Sequence__are_equal(const raceline_msgs__srv__UpdateRaceline_Request__Sequence * lhs, const raceline_msgs__srv__UpdateRaceline_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!raceline_msgs__srv__UpdateRaceline_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
raceline_msgs__srv__UpdateRaceline_Request__Sequence__copy(
  const raceline_msgs__srv__UpdateRaceline_Request__Sequence * input,
  raceline_msgs__srv__UpdateRaceline_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(raceline_msgs__srv__UpdateRaceline_Request)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(raceline_msgs__srv__UpdateRaceline_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    raceline_msgs__srv__UpdateRaceline_Request * data =
      (raceline_msgs__srv__UpdateRaceline_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!raceline_msgs__srv__UpdateRaceline_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          raceline_msgs__srv__UpdateRaceline_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!raceline_msgs__srv__UpdateRaceline_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
raceline_msgs__srv__UpdateRaceline_Response__init(raceline_msgs__srv__UpdateRaceline_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    raceline_msgs__srv__UpdateRaceline_Response__fini(msg);
    return false;
  }
  return true;
}

void
raceline_msgs__srv__UpdateRaceline_Response__fini(raceline_msgs__srv__UpdateRaceline_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
raceline_msgs__srv__UpdateRaceline_Response__are_equal(const raceline_msgs__srv__UpdateRaceline_Response * lhs, const raceline_msgs__srv__UpdateRaceline_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
raceline_msgs__srv__UpdateRaceline_Response__copy(
  const raceline_msgs__srv__UpdateRaceline_Response * input,
  raceline_msgs__srv__UpdateRaceline_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

raceline_msgs__srv__UpdateRaceline_Response *
raceline_msgs__srv__UpdateRaceline_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Response * msg = (raceline_msgs__srv__UpdateRaceline_Response *)allocator.allocate(sizeof(raceline_msgs__srv__UpdateRaceline_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(raceline_msgs__srv__UpdateRaceline_Response));
  bool success = raceline_msgs__srv__UpdateRaceline_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
raceline_msgs__srv__UpdateRaceline_Response__destroy(raceline_msgs__srv__UpdateRaceline_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    raceline_msgs__srv__UpdateRaceline_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
raceline_msgs__srv__UpdateRaceline_Response__Sequence__init(raceline_msgs__srv__UpdateRaceline_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Response * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(raceline_msgs__srv__UpdateRaceline_Response)) {
      return false;
    }
    data = (raceline_msgs__srv__UpdateRaceline_Response *)allocator.zero_allocate(size, sizeof(raceline_msgs__srv__UpdateRaceline_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = raceline_msgs__srv__UpdateRaceline_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        raceline_msgs__srv__UpdateRaceline_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
raceline_msgs__srv__UpdateRaceline_Response__Sequence__fini(raceline_msgs__srv__UpdateRaceline_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      raceline_msgs__srv__UpdateRaceline_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

raceline_msgs__srv__UpdateRaceline_Response__Sequence *
raceline_msgs__srv__UpdateRaceline_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Response__Sequence * array = (raceline_msgs__srv__UpdateRaceline_Response__Sequence *)allocator.allocate(sizeof(raceline_msgs__srv__UpdateRaceline_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = raceline_msgs__srv__UpdateRaceline_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
raceline_msgs__srv__UpdateRaceline_Response__Sequence__destroy(raceline_msgs__srv__UpdateRaceline_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    raceline_msgs__srv__UpdateRaceline_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
raceline_msgs__srv__UpdateRaceline_Response__Sequence__are_equal(const raceline_msgs__srv__UpdateRaceline_Response__Sequence * lhs, const raceline_msgs__srv__UpdateRaceline_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!raceline_msgs__srv__UpdateRaceline_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
raceline_msgs__srv__UpdateRaceline_Response__Sequence__copy(
  const raceline_msgs__srv__UpdateRaceline_Response__Sequence * input,
  raceline_msgs__srv__UpdateRaceline_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(raceline_msgs__srv__UpdateRaceline_Response)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(raceline_msgs__srv__UpdateRaceline_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    raceline_msgs__srv__UpdateRaceline_Response * data =
      (raceline_msgs__srv__UpdateRaceline_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!raceline_msgs__srv__UpdateRaceline_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          raceline_msgs__srv__UpdateRaceline_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!raceline_msgs__srv__UpdateRaceline_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
#include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "raceline_msgs/srv/detail/update_raceline__functions.h"

bool
raceline_msgs__srv__UpdateRaceline_Event__init(raceline_msgs__srv__UpdateRaceline_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    raceline_msgs__srv__UpdateRaceline_Event__fini(msg);
    return false;
  }
  // request
  if (!raceline_msgs__srv__UpdateRaceline_Request__Sequence__init(&msg->request, 0)) {
    raceline_msgs__srv__UpdateRaceline_Event__fini(msg);
    return false;
  }
  // response
  if (!raceline_msgs__srv__UpdateRaceline_Response__Sequence__init(&msg->response, 0)) {
    raceline_msgs__srv__UpdateRaceline_Event__fini(msg);
    return false;
  }
  return true;
}

void
raceline_msgs__srv__UpdateRaceline_Event__fini(raceline_msgs__srv__UpdateRaceline_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  raceline_msgs__srv__UpdateRaceline_Request__Sequence__fini(&msg->request);
  // response
  raceline_msgs__srv__UpdateRaceline_Response__Sequence__fini(&msg->response);
}

bool
raceline_msgs__srv__UpdateRaceline_Event__are_equal(const raceline_msgs__srv__UpdateRaceline_Event * lhs, const raceline_msgs__srv__UpdateRaceline_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!raceline_msgs__srv__UpdateRaceline_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!raceline_msgs__srv__UpdateRaceline_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
raceline_msgs__srv__UpdateRaceline_Event__copy(
  const raceline_msgs__srv__UpdateRaceline_Event * input,
  raceline_msgs__srv__UpdateRaceline_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!raceline_msgs__srv__UpdateRaceline_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!raceline_msgs__srv__UpdateRaceline_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

raceline_msgs__srv__UpdateRaceline_Event *
raceline_msgs__srv__UpdateRaceline_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Event * msg = (raceline_msgs__srv__UpdateRaceline_Event *)allocator.allocate(sizeof(raceline_msgs__srv__UpdateRaceline_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(raceline_msgs__srv__UpdateRaceline_Event));
  bool success = raceline_msgs__srv__UpdateRaceline_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
raceline_msgs__srv__UpdateRaceline_Event__destroy(raceline_msgs__srv__UpdateRaceline_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    raceline_msgs__srv__UpdateRaceline_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
raceline_msgs__srv__UpdateRaceline_Event__Sequence__init(raceline_msgs__srv__UpdateRaceline_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Event * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(raceline_msgs__srv__UpdateRaceline_Event)) {
      return false;
    }
    data = (raceline_msgs__srv__UpdateRaceline_Event *)allocator.zero_allocate(size, sizeof(raceline_msgs__srv__UpdateRaceline_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = raceline_msgs__srv__UpdateRaceline_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        raceline_msgs__srv__UpdateRaceline_Event__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
raceline_msgs__srv__UpdateRaceline_Event__Sequence__fini(raceline_msgs__srv__UpdateRaceline_Event__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      raceline_msgs__srv__UpdateRaceline_Event__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

raceline_msgs__srv__UpdateRaceline_Event__Sequence *
raceline_msgs__srv__UpdateRaceline_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  raceline_msgs__srv__UpdateRaceline_Event__Sequence * array = (raceline_msgs__srv__UpdateRaceline_Event__Sequence *)allocator.allocate(sizeof(raceline_msgs__srv__UpdateRaceline_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = raceline_msgs__srv__UpdateRaceline_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
raceline_msgs__srv__UpdateRaceline_Event__Sequence__destroy(raceline_msgs__srv__UpdateRaceline_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    raceline_msgs__srv__UpdateRaceline_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
raceline_msgs__srv__UpdateRaceline_Event__Sequence__are_equal(const raceline_msgs__srv__UpdateRaceline_Event__Sequence * lhs, const raceline_msgs__srv__UpdateRaceline_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!raceline_msgs__srv__UpdateRaceline_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
raceline_msgs__srv__UpdateRaceline_Event__Sequence__copy(
  const raceline_msgs__srv__UpdateRaceline_Event__Sequence * input,
  raceline_msgs__srv__UpdateRaceline_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(raceline_msgs__srv__UpdateRaceline_Event)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(raceline_msgs__srv__UpdateRaceline_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    raceline_msgs__srv__UpdateRaceline_Event * data =
      (raceline_msgs__srv__UpdateRaceline_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!raceline_msgs__srv__UpdateRaceline_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          raceline_msgs__srv__UpdateRaceline_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!raceline_msgs__srv__UpdateRaceline_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
