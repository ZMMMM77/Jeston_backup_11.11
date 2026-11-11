#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to raceline_msgs__srv__UpdateRaceline_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct UpdateRaceline_Request {
    /// flattened row-major
    pub data: Vec<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rows: u32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub cols: u32,

    /// "pure_pursuit" (cols=4) or "mppi" (cols=9)
    pub format: std::string::String,

}



impl Default for UpdateRaceline_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::UpdateRaceline_Request::default())
  }
}

impl rosidl_runtime_rs::Message for UpdateRaceline_Request {
  type RmwMsg = super::srv::rmw::UpdateRaceline_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        data: msg.data.as_slice().into(),
        rows: msg.rows,
        cols: msg.cols,
        format: msg.format.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        data: msg.data.as_slice().into(),
      rows: msg.rows,
      cols: msg.cols,
        format: msg.format.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      data: msg.data.into(),
      rows: msg.rows,
      cols: msg.cols,
      format: msg.format.to_string(),
    }
  }
}


// Corresponds to raceline_msgs__srv__UpdateRaceline_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct UpdateRaceline_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for UpdateRaceline_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::UpdateRaceline_Response::default())
  }
}

impl rosidl_runtime_rs::Message for UpdateRaceline_Response {
  type RmwMsg = super::srv::rmw::UpdateRaceline_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      message: msg.message.to_string(),
    }
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


