// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from raceline_msgs:srv/UpdateRaceline.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "raceline_msgs/srv/update_raceline.hpp"


#ifndef RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__STRUCT_HPP_
#define RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__raceline_msgs__srv__UpdateRaceline_Request __attribute__((deprecated))
#else
# define DEPRECATED__raceline_msgs__srv__UpdateRaceline_Request __declspec(deprecated)
#endif

namespace raceline_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct UpdateRaceline_Request_
{
  using Type = UpdateRaceline_Request_<ContainerAllocator>;

  explicit UpdateRaceline_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->rows = 0ul;
      this->cols = 0ul;
      this->format = "";
    }
  }

  explicit UpdateRaceline_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : format(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->rows = 0ul;
      this->cols = 0ul;
      this->format = "";
    }
  }

  // field types and members
  using _data_type =
    std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>>;
  _data_type data;
  using _rows_type =
    uint32_t;
  _rows_type rows;
  using _cols_type =
    uint32_t;
  _cols_type cols;
  using _format_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _format_type format;

  // setters for named parameter idiom
  Type & set__data(
    const std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>> & _arg)
  {
    this->data = _arg;
    return *this;
  }
  Type & set__rows(
    const uint32_t & _arg)
  {
    this->rows = _arg;
    return *this;
  }
  Type & set__cols(
    const uint32_t & _arg)
  {
    this->cols = _arg;
    return *this;
  }
  Type & set__format(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->format = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__raceline_msgs__srv__UpdateRaceline_Request
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__raceline_msgs__srv__UpdateRaceline_Request
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const UpdateRaceline_Request_ & other) const
  {
    if (this->data != other.data) {
      return false;
    }
    if (this->rows != other.rows) {
      return false;
    }
    if (this->cols != other.cols) {
      return false;
    }
    if (this->format != other.format) {
      return false;
    }
    return true;
  }
  bool operator!=(const UpdateRaceline_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct UpdateRaceline_Request_

// alias to use template instance with default allocator
using UpdateRaceline_Request =
  raceline_msgs::srv::UpdateRaceline_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace raceline_msgs


#ifndef _WIN32
# define DEPRECATED__raceline_msgs__srv__UpdateRaceline_Response __attribute__((deprecated))
#else
# define DEPRECATED__raceline_msgs__srv__UpdateRaceline_Response __declspec(deprecated)
#endif

namespace raceline_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct UpdateRaceline_Response_
{
  using Type = UpdateRaceline_Response_<ContainerAllocator>;

  explicit UpdateRaceline_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  explicit UpdateRaceline_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__raceline_msgs__srv__UpdateRaceline_Response
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__raceline_msgs__srv__UpdateRaceline_Response
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const UpdateRaceline_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const UpdateRaceline_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct UpdateRaceline_Response_

// alias to use template instance with default allocator
using UpdateRaceline_Response =
  raceline_msgs::srv::UpdateRaceline_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace raceline_msgs


// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__raceline_msgs__srv__UpdateRaceline_Event __attribute__((deprecated))
#else
# define DEPRECATED__raceline_msgs__srv__UpdateRaceline_Event __declspec(deprecated)
#endif

namespace raceline_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct UpdateRaceline_Event_
{
  using Type = UpdateRaceline_Event_<ContainerAllocator>;

  explicit UpdateRaceline_Event_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit UpdateRaceline_Event_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    service_msgs::msg::ServiceEventInfo_<ContainerAllocator>;
  _info_type info;
  using _request_type =
    rosidl_runtime_cpp::BoundedVector<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>>;
  _request_type request;
  using _response_type =
    rosidl_runtime_cpp::BoundedVector<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>>;
  _response_type response;

  // setters for named parameter idiom
  Type & set__info(
    const service_msgs::msg::ServiceEventInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__request(
    const rosidl_runtime_cpp::BoundedVector<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<raceline_msgs::srv::UpdateRaceline_Request_<ContainerAllocator>>> & _arg)
  {
    this->request = _arg;
    return *this;
  }
  Type & set__response(
    const rosidl_runtime_cpp::BoundedVector<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>, 1, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<raceline_msgs::srv::UpdateRaceline_Response_<ContainerAllocator>>> & _arg)
  {
    this->response = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator> *;
  using ConstRawPtr =
    const raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__raceline_msgs__srv__UpdateRaceline_Event
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__raceline_msgs__srv__UpdateRaceline_Event
    std::shared_ptr<raceline_msgs::srv::UpdateRaceline_Event_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const UpdateRaceline_Event_ & other) const
  {
    if (this->info != other.info) {
      return false;
    }
    if (this->request != other.request) {
      return false;
    }
    if (this->response != other.response) {
      return false;
    }
    return true;
  }
  bool operator!=(const UpdateRaceline_Event_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct UpdateRaceline_Event_

// alias to use template instance with default allocator
using UpdateRaceline_Event =
  raceline_msgs::srv::UpdateRaceline_Event_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace raceline_msgs

namespace raceline_msgs
{

namespace srv
{

struct UpdateRaceline
{
  using Request = raceline_msgs::srv::UpdateRaceline_Request;
  using Response = raceline_msgs::srv::UpdateRaceline_Response;
  using Event = raceline_msgs::srv::UpdateRaceline_Event;
};

}  // namespace srv

}  // namespace raceline_msgs

#endif  // RACELINE_MSGS__SRV__DETAIL__UPDATE_RACELINE__STRUCT_HPP_
