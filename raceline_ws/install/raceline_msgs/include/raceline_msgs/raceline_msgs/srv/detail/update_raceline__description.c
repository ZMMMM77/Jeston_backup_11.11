// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice

#include "raceline_msgs/srv/detail/update_raceline__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_raceline_msgs
const rosidl_type_hash_t *
raceline_msgs__srv__UpdateRaceline__get_type_hash(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x1c, 0x10, 0x1c, 0x5b, 0xec, 0xc7, 0xd7, 0x6e,
      0x12, 0x36, 0xb8, 0x6b, 0x02, 0xb6, 0xe0, 0xd4,
      0xed, 0x1b, 0xd8, 0x1c, 0xb0, 0x56, 0x8a, 0xbc,
      0xab, 0x25, 0x45, 0x59, 0xac, 0x90, 0xb4, 0x75,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_raceline_msgs
const rosidl_type_hash_t *
raceline_msgs__srv__UpdateRaceline_Request__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xfe, 0xfe, 0xa9, 0xdf, 0x9e, 0x35, 0x40, 0x24,
      0x42, 0x49, 0x03, 0xde, 0x36, 0x4e, 0x35, 0x2e,
      0xa5, 0x0b, 0x60, 0x8c, 0x0c, 0x49, 0x09, 0x73,
      0x96, 0x62, 0x4a, 0x36, 0x50, 0xd5, 0xab, 0xdf,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_raceline_msgs
const rosidl_type_hash_t *
raceline_msgs__srv__UpdateRaceline_Response__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x01, 0x67, 0x3c, 0x69, 0x74, 0x38, 0x78, 0x25,
      0x97, 0x2d, 0x4b, 0xb8, 0xa3, 0x6d, 0x86, 0x2b,
      0x17, 0xb6, 0x55, 0xc3, 0xa5, 0xe8, 0x54, 0xd6,
      0x53, 0x60, 0x95, 0xad, 0x52, 0x96, 0xcc, 0x7a,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_raceline_msgs
const rosidl_type_hash_t *
raceline_msgs__srv__UpdateRaceline_Event__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x93, 0xd6, 0xa6, 0x23, 0x3c, 0xf2, 0x62, 0x97,
      0xce, 0x84, 0x79, 0x18, 0x76, 0x42, 0xa6, 0xbe,
      0xea, 0xa5, 0x0f, 0x5d, 0xc5, 0xc4, 0x13, 0xd2,
      0x22, 0x9b, 0x00, 0x3d, 0xc7, 0xfb, 0xef, 0x7b,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "service_msgs/msg/detail/service_event_info__functions.h"
#include "builtin_interfaces/msg/detail/time__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t service_msgs__msg__ServiceEventInfo__EXPECTED_HASH = {1, {
    0x41, 0xbc, 0xbb, 0xe0, 0x7a, 0x75, 0xc9, 0xb5,
    0x2b, 0xc9, 0x6b, 0xfd, 0x5c, 0x24, 0xd7, 0xf0,
    0xfc, 0x0a, 0x08, 0xc0, 0xcb, 0x79, 0x21, 0xb3,
    0x37, 0x3c, 0x57, 0x32, 0x34, 0x5a, 0x6f, 0x45,
  }};
#endif

static char raceline_msgs__srv__UpdateRaceline__TYPE_NAME[] = "raceline_msgs/srv/UpdateRaceline";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char raceline_msgs__srv__UpdateRaceline_Event__TYPE_NAME[] = "raceline_msgs/srv/UpdateRaceline_Event";
static char raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME[] = "raceline_msgs/srv/UpdateRaceline_Request";
static char raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME[] = "raceline_msgs/srv/UpdateRaceline_Response";
static char service_msgs__msg__ServiceEventInfo__TYPE_NAME[] = "service_msgs/msg/ServiceEventInfo";

// Define type names, field names, and default values
static char raceline_msgs__srv__UpdateRaceline__FIELD_NAME__request_message[] = "request_message";
static char raceline_msgs__srv__UpdateRaceline__FIELD_NAME__response_message[] = "response_message";
static char raceline_msgs__srv__UpdateRaceline__FIELD_NAME__event_message[] = "event_message";

static rosidl_runtime_c__type_description__Field raceline_msgs__srv__UpdateRaceline__FIELDS[] = {
  {
    {raceline_msgs__srv__UpdateRaceline__FIELD_NAME__request_message, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME, 40, 40},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline__FIELD_NAME__response_message, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME, 41, 41},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline__FIELD_NAME__event_message, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {raceline_msgs__srv__UpdateRaceline_Event__TYPE_NAME, 38, 38},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription raceline_msgs__srv__UpdateRaceline__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Event__TYPE_NAME, 38, 38},
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME, 40, 40},
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME, 41, 41},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
raceline_msgs__srv__UpdateRaceline__get_type_description(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {raceline_msgs__srv__UpdateRaceline__TYPE_NAME, 32, 32},
      {raceline_msgs__srv__UpdateRaceline__FIELDS, 3, 3},
    },
    {raceline_msgs__srv__UpdateRaceline__REFERENCED_TYPE_DESCRIPTIONS, 5, 5},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = raceline_msgs__srv__UpdateRaceline_Event__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = raceline_msgs__srv__UpdateRaceline_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[3].fields = raceline_msgs__srv__UpdateRaceline_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[4].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__data[] = "data";
static char raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__rows[] = "rows";
static char raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__cols[] = "cols";
static char raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__format[] = "format";

static rosidl_runtime_c__type_description__Field raceline_msgs__srv__UpdateRaceline_Request__FIELDS[] = {
  {
    {raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__data, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__rows, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__cols, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Request__FIELD_NAME__format, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
raceline_msgs__srv__UpdateRaceline_Request__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME, 40, 40},
      {raceline_msgs__srv__UpdateRaceline_Request__FIELDS, 4, 4},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char raceline_msgs__srv__UpdateRaceline_Response__FIELD_NAME__success[] = "success";
static char raceline_msgs__srv__UpdateRaceline_Response__FIELD_NAME__message[] = "message";

static rosidl_runtime_c__type_description__Field raceline_msgs__srv__UpdateRaceline_Response__FIELDS[] = {
  {
    {raceline_msgs__srv__UpdateRaceline_Response__FIELD_NAME__success, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Response__FIELD_NAME__message, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
raceline_msgs__srv__UpdateRaceline_Response__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME, 41, 41},
      {raceline_msgs__srv__UpdateRaceline_Response__FIELDS, 2, 2},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char raceline_msgs__srv__UpdateRaceline_Event__FIELD_NAME__info[] = "info";
static char raceline_msgs__srv__UpdateRaceline_Event__FIELD_NAME__request[] = "request";
static char raceline_msgs__srv__UpdateRaceline_Event__FIELD_NAME__response[] = "response";

static rosidl_runtime_c__type_description__Field raceline_msgs__srv__UpdateRaceline_Event__FIELDS[] = {
  {
    {raceline_msgs__srv__UpdateRaceline_Event__FIELD_NAME__info, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Event__FIELD_NAME__request, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME, 40, 40},
    },
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Event__FIELD_NAME__response, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME, 41, 41},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription raceline_msgs__srv__UpdateRaceline_Event__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME, 40, 40},
    {NULL, 0, 0},
  },
  {
    {raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME, 41, 41},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
raceline_msgs__srv__UpdateRaceline_Event__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {raceline_msgs__srv__UpdateRaceline_Event__TYPE_NAME, 38, 38},
      {raceline_msgs__srv__UpdateRaceline_Event__FIELDS, 3, 3},
    },
    {raceline_msgs__srv__UpdateRaceline_Event__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = raceline_msgs__srv__UpdateRaceline_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = raceline_msgs__srv__UpdateRaceline_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# UpdateRaceline.srv\n"
  "float64[] data # flattened row-major\n"
  "uint32 rows\n"
  "uint32 cols\n"
  "string format # \"pure_pursuit\" (cols=4) or \"mppi\" (cols=9)\n"
  "---\n"
  "bool success\n"
  "string message";

static char srv_encoding[] = "srv";
static char implicit_encoding[] = "implicit";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
raceline_msgs__srv__UpdateRaceline__get_individual_type_description_source(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {raceline_msgs__srv__UpdateRaceline__TYPE_NAME, 32, 32},
    {srv_encoding, 3, 3},
    {toplevel_type_raw_source, 172, 172},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
raceline_msgs__srv__UpdateRaceline_Request__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {raceline_msgs__srv__UpdateRaceline_Request__TYPE_NAME, 40, 40},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
raceline_msgs__srv__UpdateRaceline_Response__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {raceline_msgs__srv__UpdateRaceline_Response__TYPE_NAME, 41, 41},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
raceline_msgs__srv__UpdateRaceline_Event__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {raceline_msgs__srv__UpdateRaceline_Event__TYPE_NAME, 38, 38},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
raceline_msgs__srv__UpdateRaceline__get_type_description_sources(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[6];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 6, 6};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *raceline_msgs__srv__UpdateRaceline__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *raceline_msgs__srv__UpdateRaceline_Event__get_individual_type_description_source(NULL);
    sources[3] = *raceline_msgs__srv__UpdateRaceline_Request__get_individual_type_description_source(NULL);
    sources[4] = *raceline_msgs__srv__UpdateRaceline_Response__get_individual_type_description_source(NULL);
    sources[5] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
raceline_msgs__srv__UpdateRaceline_Request__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *raceline_msgs__srv__UpdateRaceline_Request__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
raceline_msgs__srv__UpdateRaceline_Response__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *raceline_msgs__srv__UpdateRaceline_Response__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
raceline_msgs__srv__UpdateRaceline_Event__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *raceline_msgs__srv__UpdateRaceline_Event__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *raceline_msgs__srv__UpdateRaceline_Request__get_individual_type_description_source(NULL);
    sources[3] = *raceline_msgs__srv__UpdateRaceline_Response__get_individual_type_description_source(NULL);
    sources[4] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
