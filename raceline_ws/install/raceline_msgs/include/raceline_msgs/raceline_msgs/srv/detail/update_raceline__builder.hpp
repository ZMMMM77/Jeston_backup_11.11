// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "raceline_msgs/srv/update_raceline.hpp"


#ifndef RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__BUILDER_HPP_
#define RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "raceline_msgs/srv/detail/update_raceline__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace raceline_msgs
{

namespace srv
{

namespace builder
{

class Init_UpdateRaceline_Request_format
{
public:
  explicit Init_UpdateRaceline_Request_format(::raceline_msgs::srv::UpdateRaceline_Request & msg)
  : msg_(msg)
  {}
  ::raceline_msgs::srv::UpdateRaceline_Request format(::raceline_msgs::srv::UpdateRaceline_Request::_format_type arg)
  {
    msg_.format = std::move(arg);
    return std::move(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Request msg_;
};

class Init_UpdateRaceline_Request_cols
{
public:
  explicit Init_UpdateRaceline_Request_cols(::raceline_msgs::srv::UpdateRaceline_Request & msg)
  : msg_(msg)
  {}
  Init_UpdateRaceline_Request_format cols(::raceline_msgs::srv::UpdateRaceline_Request::_cols_type arg)
  {
    msg_.cols = std::move(arg);
    return Init_UpdateRaceline_Request_format(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Request msg_;
};

class Init_UpdateRaceline_Request_rows
{
public:
  explicit Init_UpdateRaceline_Request_rows(::raceline_msgs::srv::UpdateRaceline_Request & msg)
  : msg_(msg)
  {}
  Init_UpdateRaceline_Request_cols rows(::raceline_msgs::srv::UpdateRaceline_Request::_rows_type arg)
  {
    msg_.rows = std::move(arg);
    return Init_UpdateRaceline_Request_cols(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Request msg_;
};

class Init_UpdateRaceline_Request_data
{
public:
  Init_UpdateRaceline_Request_data()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_UpdateRaceline_Request_rows data(::raceline_msgs::srv::UpdateRaceline_Request::_data_type arg)
  {
    msg_.data = std::move(arg);
    return Init_UpdateRaceline_Request_rows(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::raceline_msgs::srv::UpdateRaceline_Request>()
{
  return raceline_msgs::srv::builder::Init_UpdateRaceline_Request_data();
}

}  // namespace raceline_msgs


namespace raceline_msgs
{

namespace srv
{

namespace builder
{

class Init_UpdateRaceline_Response_message
{
public:
  explicit Init_UpdateRaceline_Response_message(::raceline_msgs::srv::UpdateRaceline_Response & msg)
  : msg_(msg)
  {}
  ::raceline_msgs::srv::UpdateRaceline_Response message(::raceline_msgs::srv::UpdateRaceline_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Response msg_;
};

class Init_UpdateRaceline_Response_success
{
public:
  Init_UpdateRaceline_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_UpdateRaceline_Response_message success(::raceline_msgs::srv::UpdateRaceline_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_UpdateRaceline_Response_message(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::raceline_msgs::srv::UpdateRaceline_Response>()
{
  return raceline_msgs::srv::builder::Init_UpdateRaceline_Response_success();
}

}  // namespace raceline_msgs


namespace raceline_msgs
{

namespace srv
{

namespace builder
{

class Init_UpdateRaceline_Event_response
{
public:
  explicit Init_UpdateRaceline_Event_response(::raceline_msgs::srv::UpdateRaceline_Event & msg)
  : msg_(msg)
  {}
  ::raceline_msgs::srv::UpdateRaceline_Event response(::raceline_msgs::srv::UpdateRaceline_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Event msg_;
};

class Init_UpdateRaceline_Event_request
{
public:
  explicit Init_UpdateRaceline_Event_request(::raceline_msgs::srv::UpdateRaceline_Event & msg)
  : msg_(msg)
  {}
  Init_UpdateRaceline_Event_response request(::raceline_msgs::srv::UpdateRaceline_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_UpdateRaceline_Event_response(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Event msg_;
};

class Init_UpdateRaceline_Event_info
{
public:
  Init_UpdateRaceline_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_UpdateRaceline_Event_request info(::raceline_msgs::srv::UpdateRaceline_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_UpdateRaceline_Event_request(msg_);
  }

private:
  ::raceline_msgs::srv::UpdateRaceline_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::raceline_msgs::srv::UpdateRaceline_Event>()
{
  return raceline_msgs::srv::builder::Init_UpdateRaceline_Event_info();
}

}  // namespace raceline_msgs

#endif  // RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__BUILDER_HPP_
