#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "raceline_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__raceline_msgs__srv__UpdateRaceline_Request() -> *const std::ffi::c_void;
}

#[link(name = "raceline_msgs__rosidl_generator_c")]
extern "C" {
    fn raceline_msgs__srv__UpdateRaceline_Request__init(msg: *mut UpdateRaceline_Request) -> bool;
    fn raceline_msgs__srv__UpdateRaceline_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<UpdateRaceline_Request>, size: usize) -> bool;
    fn raceline_msgs__srv__UpdateRaceline_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<UpdateRaceline_Request>);
    fn raceline_msgs__srv__UpdateRaceline_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<UpdateRaceline_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<UpdateRaceline_Request>) -> bool;
}

// Corresponds to raceline_msgs__srv__UpdateRaceline_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct UpdateRaceline_Request {
    /// flattened row-major
    pub data: rosidl_runtime_rs::Sequence<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rows: u32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cols: u32,

    /// "pure_pursuit" (cols=4) or "mppi" (cols=9)
    pub format: rosidl_runtime_rs::String,

}



impl Default for UpdateRaceline_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !raceline_msgs__srv__UpdateRaceline_Request__init(&mut msg as *mut _) {
        panic!("Call to raceline_msgs__srv__UpdateRaceline_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for UpdateRaceline_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { raceline_msgs__srv__UpdateRaceline_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { raceline_msgs__srv__UpdateRaceline_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { raceline_msgs__srv__UpdateRaceline_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for UpdateRaceline_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for UpdateRaceline_Request where Self: Sized {
  const TYPE_NAME: &'static str = "raceline_msgs/srv/UpdateRaceline_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__raceline_msgs__srv__UpdateRaceline_Request() }
  }
}


#[link(name = "raceline_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__raceline_msgs__srv__UpdateRaceline_Response() -> *const std::ffi::c_void;
}

#[link(name = "raceline_msgs__rosidl_generator_c")]
extern "C" {
    fn raceline_msgs__srv__UpdateRaceline_Response__init(msg: *mut UpdateRaceline_Response) -> bool;
    fn raceline_msgs__srv__UpdateRaceline_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<UpdateRaceline_Response>, size: usize) -> bool;
    fn raceline_msgs__srv__UpdateRaceline_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<UpdateRaceline_Response>);
    fn raceline_msgs__srv__UpdateRaceline_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<UpdateRaceline_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<UpdateRaceline_Response>) -> bool;
}

// Corresponds to raceline_msgs__srv__UpdateRaceline_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct UpdateRaceline_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for UpdateRaceline_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !raceline_msgs__srv__UpdateRaceline_Response__init(&mut msg as *mut _) {
        panic!("Call to raceline_msgs__srv__UpdateRaceline_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for UpdateRaceline_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { raceline_msgs__srv__UpdateRaceline_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { raceline_msgs__srv__UpdateRaceline_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { raceline_msgs__srv__UpdateRaceline_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for UpdateRaceline_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for UpdateRaceline_Response where Self: Sized {
  const TYPE_NAME: &'static str = "raceline_msgs/srv/UpdateRaceline_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__raceline_msgs__srv__UpdateRaceline_Response() }
  }
}






#[link(name = "raceline_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__raceline_msgs__srv__UpdateRaceline() -> *const std::ffi::c_void;
}

// Corresponds to raceline_msgs__srv__UpdateRaceline
#[allow(missing_docs, non_camel_case_types)]
pub struct UpdateRaceline;

impl rosidl_runtime_rs::Service for UpdateRaceline {
    type Request = UpdateRaceline_Request;
    type Response = UpdateRaceline_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__raceline_msgs__srv__UpdateRaceline() }
    }
}


