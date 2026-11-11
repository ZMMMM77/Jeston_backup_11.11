// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "raceline_msgs/srv/update_raceline.hpp"


#ifndef RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__TRAITS_HPP_
#define RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "raceline_msgs/srv/detail/update_raceline__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace raceline_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const UpdateRaceline_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: data
  {
    if (msg.data.size() == 0) {
      out << "data: []";
    } else {
      out << "data: [";
      size_t pending_items = msg.data.size();
      for (auto item : msg.data) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: rows
  {
    out << "rows: ";
    rosidl_generator_traits::value_to_yaml(msg.rows, out);
    out << ", ";
  }

  // member: cols
  {
    out << "cols: ";
    rosidl_generator_traits::value_to_yaml(msg.cols, out);
    out << ", ";
  }

  // member: format
  {
    out << "format: ";
    rosidl_generator_traits::value_to_yaml(msg.format, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const UpdateRaceline_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.data.size() == 0) {
      out << "data: []\n";
    } else {
      out << "data:\n";
      for (auto item : msg.data) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: rows
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "rows: ";
    rosidl_generator_traits::value_to_yaml(msg.rows, out);
    out << "\n";
  }

  // member: cols
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "cols: ";
    rosidl_generator_traits::value_to_yaml(msg.cols, out);
    out << "\n";
  }

  // member: format
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "format: ";
    rosidl_generator_traits::value_to_yaml(msg.format, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const UpdateRaceline_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace raceline_msgs

namespace rosidl_generator_traits
{

[[deprecated("use raceline_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const raceline_msgs::srv::UpdateRaceline_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  raceline_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use raceline_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const raceline_msgs::srv::UpdateRaceline_Request & msg)
{
  return raceline_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<raceline_msgs::srv::UpdateRaceline_Request>()
{
  return "raceline_msgs::srv::UpdateRaceline_Request";
}

template<>
inline const char * name<raceline_msgs::srv::UpdateRaceline_Request>()
{
  return "raceline_msgs/srv/UpdateRaceline_Request";
}

template<>
struct has_fixed_size<raceline_msgs::srv::UpdateRaceline_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<raceline_msgs::srv::UpdateRaceline_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<raceline_msgs::srv::UpdateRaceline_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace raceline_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const UpdateRaceline_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const UpdateRaceline_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const UpdateRaceline_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace raceline_msgs

namespace rosidl_generator_traits
{

[[deprecated("use raceline_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const raceline_msgs::srv::UpdateRaceline_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  raceline_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use raceline_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const raceline_msgs::srv::UpdateRaceline_Response & msg)
{
  return raceline_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<raceline_msgs::srv::UpdateRaceline_Response>()
{
  return "raceline_msgs::srv::UpdateRaceline_Response";
}

template<>
inline const char * name<raceline_msgs::srv::UpdateRaceline_Response>()
{
  return "raceline_msgs/srv/UpdateRaceline_Response";
}

template<>
struct has_fixed_size<raceline_msgs::srv::UpdateRaceline_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<raceline_msgs::srv::UpdateRaceline_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<raceline_msgs::srv::UpdateRaceline_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__traits.hpp"

namespace raceline_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const UpdateRaceline_Event & msg,
  std::ostream & out)
{
  out << "{";
  // member: info
  {
    out << "info: ";
    to_flow_style_yaml(msg.info, out);
    out << ", ";
  }

  // member: request
  {
    if (msg.request.size() == 0) {
      out << "request: []";
    } else {
      out << "request: [";
      size_t pending_items = msg.request.size();
      for (auto item : msg.request) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: response
  {
    if (msg.response.size() == 0) {
      out << "response: []";
    } else {
      out << "response: [";
      size_t pending_items = msg.response.size();
      for (auto item : msg.response) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const UpdateRaceline_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: info
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "info:\n";
    to_block_style_yaml(msg.info, out, indentation + 2);
  }

  // member: request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.request.size() == 0) {
      out << "request: []\n";
    } else {
      out << "request:\n";
      for (auto item : msg.request) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: response
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.response.size() == 0) {
      out << "response: []\n";
    } else {
      out << "response:\n";
      for (auto item : msg.response) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const UpdateRaceline_Event & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace raceline_msgs

namespace rosidl_generator_traits
{

[[deprecated("use raceline_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const raceline_msgs::srv::UpdateRaceline_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  raceline_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use raceline_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const raceline_msgs::srv::UpdateRaceline_Event & msg)
{
  return raceline_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<raceline_msgs::srv::UpdateRaceline_Event>()
{
  return "raceline_msgs::srv::UpdateRaceline_Event";
}

template<>
inline const char * name<raceline_msgs::srv::UpdateRaceline_Event>()
{
  return "raceline_msgs/srv/UpdateRaceline_Event";
}

template<>
struct has_fixed_size<raceline_msgs::srv::UpdateRaceline_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<raceline_msgs::srv::UpdateRaceline_Event>
  : std::integral_constant<bool, has_bounded_size<raceline_msgs::srv::UpdateRaceline_Request>::value && has_bounded_size<raceline_msgs::srv::UpdateRaceline_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<raceline_msgs::srv::UpdateRaceline_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<raceline_msgs::srv::UpdateRaceline>()
{
  return "raceline_msgs::srv::UpdateRaceline";
}

template<>
inline const char * name<raceline_msgs::srv::UpdateRaceline>()
{
  return "raceline_msgs/srv/UpdateRaceline";
}

template<>
struct has_fixed_size<raceline_msgs::srv::UpdateRaceline>
  : std::integral_constant<
    bool,
    has_fixed_size<raceline_msgs::srv::UpdateRaceline_Request>::value &&
    has_fixed_size<raceline_msgs::srv::UpdateRaceline_Response>::value
  >
{
};

template<>
struct has_bounded_size<raceline_msgs::srv::UpdateRaceline>
  : std::integral_constant<
    bool,
    has_bounded_size<raceline_msgs::srv::UpdateRaceline_Request>::value &&
    has_bounded_size<raceline_msgs::srv::UpdateRaceline_Response>::value
  >
{
};

template<>
struct is_service<raceline_msgs::srv::UpdateRaceline>
  : std::true_type
{
};

template<>
struct is_service_request<raceline_msgs::srv::UpdateRaceline_Request>
  : std::true_type
{
};

template<>
struct is_service_response<raceline_msgs::srv::UpdateRaceline_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__TRAITS_HPP_
