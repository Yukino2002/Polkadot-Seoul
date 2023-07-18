//! Dummy library wrapper!
//! Provide a safe abstraction over libdummy
//!
use crate::ext::{FFICtx, FFIWrapper, RustSideHandler};
pub use crate::my_lib_errors::MyError;
pub use crate::my_lib_errors::MyLibResult;
use std::ffi::CString;
use std::ptr::null;
#[cfg(feature = "with_lib_checks")]
use std::sync::RwLock;
mod my_lib_errors;
use log::debug;

#[cfg(feature = "with_lib_checks")]
#[macro_use]
extern crate lazy_static;

// These static muts are used to control the start and shutdown of the library.
// NOTE: accessing and setting this is NOT thread safe. Considering a lazy_static!
// or SyncLazy(when stable)
// NOTE: when using lazy_static the output of valgrind will show some blocks that are not freed
#[cfg(feature = "with_lib_checks")]
lazy_static! {
    static ref LIB_VALID: RwLock<bool> = RwLock::new(true);
    static ref LIB_STARTED: RwLock<bool> = RwLock::new(false);
}

#[cfg(feature = "with_lib_checks")]
pub fn cancel_call(dest: &str, ctx: *const FFICtx) -> i32 {
    let dest = CString::new(dest).unwrap();
    if *LIB_VALID.read().unwrap() {
        //Safety: calling extern function. This is valid as long as shutdown hasn't been called
        unsafe { crate::ext::cancel(dest.as_ptr(), ctx) }
    } else {
        // This means the library was shutdown, but we had a ctx that was not freed.
        // This will proceed to free the boxes.
        info!("delete after shutdown");
        -1
    }
}

#[cfg(not(feature = "with_lib_checks"))]
pub fn cancel_call(dest: &str, ctx: *const FFICtx) -> i32 {
    let dest = CString::new(dest).unwrap();
    //Safety: calling extern function. This is valid as long as shutdown hasn't been called
    unsafe { crate::ext::cancel(dest.as_ptr(), ctx) }
}

pub trait OnSend {
    //both of these methods need to be '&self' because the c side can reach back from multiple threads.
    fn on_send(&self, src: &str, arg: &[u8]);
    fn on_send_inline(&self, src: &str, arg: &[u8]) -> Vec<u8>;
}

/// Keep track of a given `handle: Box<dyn OnSend + Sync>` registered via the [`handler`] function.
//Allow dead code since both ptrs are only used by the C side
#[allow(dead_code)]
pub struct UserSpaceWrapper {
    ffi_wrapper: *mut FFIWrapper,
    ctx: *const FFICtx,
}

impl Drop for UserSpaceWrapper {
    fn drop(&mut self) {
        //NOTE: the UserSpaceWrapper object is normally associated with a 'dest'.
        // If the wrong string is passed to the 'libdummy' side it won't free the 'ctx' variable
        // and it would be a memory leak. In the real library that won't be a problem.

        let res = self.delete("");
        debug!("dropped UserSpaceWrapper, ctx freed:'{}'", res);
    }
}

impl UserSpaceWrapper {
    fn delete(&mut self, dest: &str) -> bool {
        if self.ctx == null() {
            return false;
        }

        let res = cancel_call(dest, self.ctx);

        //Safety: The boxes are created in 'new' and immediately consumed to raw ptrs.
        //        They are only ever read again in here just to drop them. Since this is called
        //        after calling 'cancel' above it will be safe to free the boxes
        unsafe {
            //Important!
            // To free all resources held by the FFIWrapper struct we need to:
            //   - Rebuild the Box<FFIWrapper>
            //   - Rebuild the Box<RustSideHandler> held inside the FFIWrapper
            //   - Rebuild the Box<dyn OnSend> held inside the RustSideHandler
            // all these boxes will be dropped here, freeing the resources.
            let ffi_obj_to_drop = std::boxed::Box::from_raw(self.ffi_wrapper);
            let self_rust_side_to_drop = std::boxed::Box::from_raw(ffi_obj_to_drop.self_rust_side);
            std::boxed::Box::from_raw(self_rust_side_to_drop.opaque);
        }
        self.ctx = null();
        res >= 0
    }

    fn new(dest: &str, handle: Box<dyn OnSend + Sync>) -> MyLibResult<Self> {
        let handle = std::boxed::Box::into_raw(handle);
        let rust_side_obj = Box::new(RustSideHandler { opaque: handle });

        let ffi_obj = Box::new(FFIWrapper {
            callback_with_return: crate::ext::handler_cb_with_return,
            callback: crate::ext::handler_cb,
            self_rust_side: std::boxed::Box::into_raw(rust_side_obj),
        });

        let ffi_obj = std::boxed::Box::into_raw(ffi_obj);
        let c_dest = CString::new(dest).unwrap();

        //Safety: calling extern function. This is valid as long as shutdown hasn't been called
        let ctx = unsafe { crate::ext::handler(c_dest.as_ptr(), ffi_obj) };
        if ctx == null() {
            Err(MyError::FailedToRegister {
                dest: dest.to_string(),
            })
        } else {
            Ok(UserSpaceWrapper {
                ffi_wrapper: ffi_obj,
                ctx,
            })
        }
    }
}

/// Private module that encapsulates all the extern parts of the library.
mod ext {
    use crate::OnSend;
    use log::debug;
    use std::ffi::{c_void, CStr};
    use std::os::raw::{c_char, c_int, c_uchar};
    use std::ptr::null;

    /// Struct introduced in order to send the fat ptr that represents an OnSend trait object
    /// through ffi.
    /// See [Passing dyn trait through ffi](../notes/fatptr_through_ffi.md)
    #[repr(C)]
    pub struct RustSideHandler {
        pub opaque: *mut dyn OnSend,
    }

    #[repr(C)]
    pub struct FFIBuf {
        pub data_ptr: *const c_uchar,
        pub data_len: usize,
        pub destroyer: extern "C" fn(FFIBuf),
        c_vec: *const c_void,
    }

    /// Structure defined by the libdummy header for data exchange.
    #[repr(C)]
    pub struct FFIWrapper {
        /// Function pointer used by the library to reach back
        pub callback: extern "C" fn(*mut RustSideHandler, *const c_char, *const c_uchar, usize),
        pub callback_with_return:
            extern "C" fn(*mut RustSideHandler, *const c_char, *const c_uchar, usize) -> FFIBuf,
        /// Entity that is meant to handle the callback. This field will be passed in as the
        /// first arg of the fn ptr above.
        pub self_rust_side: *mut RustSideHandler,
    }

    /// Represents the extern ptr to the Context struct given by the library.
    /// As long as this ptr is valid, the library will reach back to rust via the 'handler_cb' when
    /// callbacks occur. The FFICtx will be invalidated after a call to 'cancel'.
    /// This is an opaque struct not meant to be accessed by rust.
    #[repr(C)]
    pub struct FFICtx {
        _private: [u8; 0],
    }

    #[link(name = "dummy")]
    extern "C" {
        /// Sends a series of bytes to the given `dest`
        /// # Arguments
        /// * `dest` - null terminated string
        /// * `arg` - byte array of the data to be sent
        /// * `arg_len` - length of the `arg` byte array
        ///
        /// Returns an int where '>=0' is success
        ///
        pub fn send_async(dest: *const c_char, arg: *const c_uchar, arg_len: usize) -> c_int;

        /// Sends a series of bytes to the given `dest`
        /// # Arguments
        /// * `dest` - null terminated string
        /// * `arg` - byte array of the data to be sent
        /// * `arg_len` - length of the `arg` byte array
        ///
        /// Returns an int where '>=0' is success
        ///
        pub fn send_inline(dest: *const c_char, arg: *const c_uchar, arg_len: usize) -> FFIBuf;

        /// Register a handler on the given `dest`
        /// # Arguments
        /// * `dest` - null terminated string
        /// * `ffi_obj` - handler data to be used by libdummy
        ///
        /// Returns a context struct that corresponds to the given `ffi_obj`
        //NOTE: FFIWrapper includes a struct that has a trait object BUT it is not meant to be
        //      accessed by the c side so it should be safe.
        #[allow(improper_ctypes)]
        pub fn handler(dest: *const c_char, ffi_obj: *mut FFIWrapper) -> *const FFICtx;

        /// Sends a series of bytes to the given `dest`
        /// # Arguments
        /// * `dest` - null terminated string
        /// * `ctx` - ctx struct to cancel.
        /// Returns an int where '>=0' is success
        pub fn cancel(dest: *const c_char, ctx: *const FFICtx) -> c_int;
        ///Completely shutdown libdummy. After this call, no other extern method is valid.
        pub fn shutdown();
    }

    /// Function callback used by the library to reach back to rust.
    pub extern "C" fn handler_cb(
        rust_obj: *mut RustSideHandler,
        dest: *const c_char,
        arg: *const c_uchar,
        arg_len: usize,
    ) {
        //Safety: This is the most critical unsafe block.
        // This block assumes the C library honors its contract and will NOT trigger this callback
        // with a RustSideHandler that has already been freed. As a reminder, a
        // RustSideHandler comes paired up with an FFICtx. Once the FFCtx is returned to the C via
        // 'cancel' the associated RustSideHandler is freed.
        unsafe {
            //TODO: should it read lib valid here ??
            let dest = CStr::from_ptr(dest);
            let sl = std::slice::from_raw_parts(arg, arg_len);
            (*(*rust_obj).opaque).on_send(dest.to_str().unwrap(), sl);
        }
    }

    pub extern "C" fn destroy_buf(done: FFIBuf) {
        debug!("DESTORY");
        unsafe {
            // let ffibuf = std::boxed::Box::from_raw(done);
            let p = done.data_ptr as *mut u8;
            Vec::from_raw_parts(p, done.data_len, done.data_len);
        }
    }

    /// Function callback used by the library to reach back to rust.
    pub extern "C" fn handler_cb_with_return(
        rust_obj: *mut RustSideHandler,
        dest: *const c_char,
        arg: *const c_uchar,
        arg_len: usize,
    ) -> FFIBuf {
        //Safety: This is the most critical unsafe block.
        // This block assumes the C library honors its contract and will NOT trigger this callback
        // with a RustSideHandler that has already been freed. As a reminder, a
        // RustSideHandler comes paired up with an FFICtx. Once the FFCtx is returned to the C via
        // 'cancel' the associated RustSideHandler is freed.
        let mut data = unsafe {
            let dest = CStr::from_ptr(dest);
            let sl = std::slice::from_raw_parts(arg, arg_len);
            (*(*rust_obj).opaque).on_send_inline(dest.to_str().unwrap(), sl)
        };

        debug!("VEC FROM C SIDE SIZE INLINE {}", data.len());

        // let ptr =  data.as_ptr();
        data.shrink_to_fit();
        let cnt = data.len();
        let ptr = data.as_mut_ptr();
        // IMPORTANT: we forget here because we assume c will play nice and give the vector back
        // when it's done (see 'destroy_buf') above.
        std::mem::forget(data);
        FFIBuf {
            data_ptr: ptr,
            data_len: cnt,
            destroyer: destroy_buf,
            c_vec: null(),
        }
    }
}

pub struct LibDummy {
    // Make LibDummy a ZST with a private field so it can only be instantiated via the
    // start_lib function (factory style)
    _hide: (),
}

#[cfg(feature = "with_lib_checks")]
pub fn start_lib() -> Result<LibDummy, &'static str> {
    let mut lib_started_w_lock = LIB_STARTED.write().unwrap();
    if !*lib_started_w_lock {
        *lib_started_w_lock = false
    } else {
        return Err("Already initialized");
    }
    return Ok(LibDummy { _hide: () });
}

#[cfg(not(feature = "with_lib_checks"))]
pub fn start_lib() -> Result<LibDummy, &'static str> {
    return Ok(LibDummy { _hide: () });
}

impl LibDummy {
    /// Sends a series of bytes to the given `dest`
    /// # Arguments
    /// * `dest` - destination for the data
    /// * `data` - byte array of the data to be sent
    ///
    /// Returns true if operation is a success
    ///
    pub fn send(&self, dest: &str, data: &[u8]) -> bool {
        let dest = CString::new(dest).unwrap();

        //Safety: calling extern function. This is valid as long as shutdown hasn't been called
        let res = unsafe { crate::ext::send_async(dest.as_ptr(), data.as_ptr(), data.len()) };

        res >= 0
    }

    /// Sends a series of bytes to the given `dest`
    /// # Arguments
    /// * `dest` - destination for the data
    /// * `data` - byte array of the data to be sent
    ///
    /// Returns data from a handler that was previously registered.
    ///
    pub fn send_inline(&self, dest: &str, data: &[u8]) -> Vec<u8> {
        let dest = CString::new(dest).unwrap();

        //Safety: calling extern function. This is valid as long as shutdown hasn't been called
        let res = unsafe { crate::ext::send_inline(dest.as_ptr(), data.as_ptr(), data.len()) };

        debug!("WE GOT SOMETHING {}", res.data_len);
        let slice: &[u8] = unsafe { std::slice::from_raw_parts(res.data_ptr, res.data_len) };

        let mut dst: Vec<u8> = Vec::with_capacity(slice.len());

        for b in slice {
            dst.push(b.clone());
        }
        // TODO BENCHMARK THIS
        // dst.as_mut_slice().copy_from_slice(slice);

        (res.destroyer)(res);
        dst
    }

    /// Register a handler on the given `dest`
    /// # Arguments
    /// * `dest` - route the given `handler` should receive data on.
    /// * `handle` - handler data to be used by libdummy
    ///
    /// Returns a context struct that corresponds to the given `ffi_obj`
    pub fn handler(
        &self,
        dest: &str,
        handle: Box<dyn OnSend + Sync>,
    ) -> MyLibResult<UserSpaceWrapper> {
        UserSpaceWrapper::new(dest, handle)
    }

    /// Cancel a `dest`/`user_wrapper` combination. This should correspond to the ones received by a call
    /// to [`handler`]
    /// # Arguments
    /// * `dest` - same route used that produced the given `user_wrapper`
    /// * `user_wrapper` - handler to cancel.
    pub fn cancel(&self, dest: &str, user_wrapper: UserSpaceWrapper) -> bool {
        let mut user_wrapper = user_wrapper;
        user_wrapper.delete(dest)
    }

    ///Completely shutdown libdummy. After this call, no other extern method is valid.
    ///
    /// # Arguments
    /// * 'self' - consume the library so it can no longer be used.
    #[cfg(feature = "with_lib_checks")]
    pub fn shutdown(self) {
        let mut lib_valid_w_lock = LIB_VALID.write().unwrap();
        *lib_valid_w_lock = false;

        unsafe {
            crate::ext::shutdown();
        }
    }

    #[cfg(not(feature = "with_lib_checks"))]
    pub fn shutdown(self) {
        unsafe {
            crate::ext::shutdown();
        }
    }
}

#[cfg(test)]
mod tests {
    use crate::OnSend;
    use std::mem::{size_of, transmute};

    struct TestStruct;
    impl OnSend for TestStruct {
        fn on_send(&self, _src: &str, _arg: &[u8]) {
            unimplemented!()
        }

        fn on_send_inline(&self, _src: &str, _arg: &[u8]) -> Vec<u8> {
            unimplemented!()
        }
    }
    struct TestStruct2;
    impl OnSend for TestStruct2 {
        fn on_send(&self, _src: &str, _arg: &[u8]) {
            unimplemented!()
        }

        fn on_send_inline(&self, _src: &str, _arg: &[u8]) -> Vec<u8> {
            unimplemented!()
        }
    }

    #[test]
    fn fat_ptr() {
        // https://iandouglasscott.com/2018/05/28/exploring-rust-fat-pointers/
        // So, this is a fat pointer.
        dbg!(size_of::<*mut dyn OnSend>());

        let handle: Box<dyn OnSend> = Box::new(TestStruct {});
        let handle = std::boxed::Box::into_raw(handle);

        dbg!(unsafe { transmute::<_, (usize, usize)>(handle) });
        dbg!(handle);

        let handle2: Box<dyn OnSend> = Box::new(TestStruct2 {});
        let handle2 = std::boxed::Box::into_raw(handle2);

        dbg!(unsafe { transmute::<_, (usize, usize)>(handle2) });
        dbg!(handle2);
    }
}
