/*
 * Copyright (c) 2022 XXIV
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
use std::os::raw::c_char;
use std::os::raw::c_int;
use std::ffi::CStr;
use std::ffi::CString;
use std::slice;
use fs_extra::copy_items;
use fs_extra::dir;
use fs_extra::move_items;
use fs_extra::remove_items;
use fs_extra::file;
use fs_extra::file::move_file;
use fs_extra::file::read_to_string;
use fs_extra::file::write_all;
use fs_extra::dir::create;
use fs_extra::dir::create_all;
use fs_extra::dir::get_dir_content;
use fs_extra::dir::get_dir_content2;
use fs_extra::dir::DirOptions;
use fs_extra::dir::get_size;
use fs_extra::dir::move_dir;

#[repr(C)]
struct copy_options_dir_t {
  overwrite: c_int,
  skip_exist: c_int,
  buffer_size: usize,
  copy_inside: c_int,
  content_only: c_int,
  depth: u64,
}

#[repr(C)]
struct copy_options_file_t {
  overwrite: c_int,
  skip_exist: c_int,
  buffer_size: usize,
}

#[repr(C)]
struct dir_content_t {
  dir_size: u64,
  files_length: usize,
  directories_length: usize,
  files: *mut *mut c_char,
  directories: *mut *mut c_char,
}

#[no_mangle]
unsafe extern "C" fn fs_extra_copy_items(from: *const *const c_char, from_length: usize,to: *const c_char, options: *const copy_options_dir_t) -> c_int {
  let opt = dir::CopyOptions{ overwrite: if (*options).overwrite == 0 { false } else { true } ,
                         skip_exist: if (*options).skip_exist == 0 { false } else { true },
                         buffer_size: (*options).buffer_size,
                         copy_inside: if (*options).copy_inside == 0 { false } else { true },
                         content_only: if (*options).content_only == 0 { false } else { true },
                         depth: (*options).depth };
  let paths = slice::from_raw_parts(from, from_length);
  let vec: Vec<String> = paths.iter().map(|&i| CStr::from_ptr(i).to_string_lossy().into_owned()).collect();
  let to_rs = match CStr::from_ptr(to).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match copy_items(&vec, to_rs, &opt) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_move_items(from_items: *const *const c_char, from_items_length: usize,to: *const c_char, options: *const copy_options_dir_t) -> c_int {
  let opt = dir::CopyOptions{ overwrite: if (*options).overwrite == 0 { false } else { true } ,
                         skip_exist: if (*options).skip_exist == 0 { false } else { true },
                         buffer_size: (*options).buffer_size,
                         copy_inside: if (*options).copy_inside == 0 { false } else { true },
                         content_only: if (*options).content_only == 0 { false } else { true },
                         depth: (*options).depth };
  let paths = slice::from_raw_parts(from_items, from_items_length);
  let vec: Vec<String> = paths.iter().map(|&i| CStr::from_ptr(i).to_string_lossy().into_owned()).collect();
  let to_rs = match CStr::from_ptr(to).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match move_items(&vec, to_rs, &opt) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_remove_items(from_items: *const *const c_char, from_items_length: usize) -> c_int {
  let paths = slice::from_raw_parts(from_items, from_items_length);
  let vec: Vec<String> = paths.iter().map(|&i| CStr::from_ptr(i).to_string_lossy().into_owned()).collect();
  match remove_items(&vec) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_file_copy(from: *const c_char, to: *const c_char, options: *const copy_options_file_t) -> c_int {
  let opt = file::CopyOptions{ overwrite: if (*options).overwrite == 0 { false } else { true } ,
                         skip_exist: if (*options).skip_exist == 0 { false } else { true },
                         buffer_size: (*options).buffer_size };
  let from_rs = match CStr::from_ptr(from).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };
  let to_rs = match CStr::from_ptr(to).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match file::copy(from_rs, to_rs, &opt) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_file_move_file(from: *const c_char, to: *const c_char, options: *const copy_options_file_t) -> c_int {
  let opt = file::CopyOptions{ overwrite: if (*options).overwrite == 0 { false } else { true } ,
                         skip_exist: if (*options).skip_exist == 0 { false } else { true },
                         buffer_size: (*options).buffer_size };
  let from_rs = match CStr::from_ptr(from).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };
  let to_rs = match CStr::from_ptr(to).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match move_file(from_rs, to_rs, &opt) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_file_read_to_string(path: *const c_char) -> *mut c_char {
  let path_rs = match CStr::from_ptr(path).to_str() {
      Ok(s) => s,
      Err(_) => return std::ptr::null_mut()
  };
  let res = match read_to_string(path_rs) {
    Ok(v) => v,
    Err(_) => return std::ptr::null_mut()
  };
  match CString::new(res) {
    Ok(s) => s.into_raw(),
    Err(_) => std::ptr::null_mut()
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_file_remove(path: *const c_char) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match file::remove(path_rs) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_file_write_all(path: *const c_char, content: *const c_char) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  let content_rs = match CStr::from_ptr(content).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match write_all(path_rs, content_rs) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_copy(from: *const c_char, to: *const c_char, options: *const copy_options_dir_t) -> c_int {
  let opt = dir::CopyOptions{ overwrite: if (*options).overwrite == 0 { false } else { true } ,
                         skip_exist: if (*options).skip_exist == 0 { false } else { true },
                         buffer_size: (*options).buffer_size,
                         copy_inside: if (*options).copy_inside == 0 { false } else { true },
                         content_only: if (*options).content_only == 0 { false } else { true },
                         depth: (*options).depth };
  let from_rs = match CStr::from_ptr(from).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };
  let to_rs = match CStr::from_ptr(to).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match dir::copy(from_rs, to_rs, &opt) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_create(path: *const c_char, erase: c_int) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match create(path_rs, if erase == 0 {false} else {true}) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_create_all(path: *const c_char, erase: c_int) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match create_all(path_rs, if erase == 0 {false} else {true}) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_get_dir_content(dir_content: *mut dir_content_t, path: *const c_char) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match get_dir_content(path_rs) {
    Ok(mut res) => {
      res.files.shrink_to_fit();
      res.directories.shrink_to_fit();
      let mut files: Vec<*mut c_char> = res.files.iter().map(|i| match CString::new(i.as_str()) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut()
      } ).collect();
      let mut directories: Vec<*mut c_char> = res.directories.iter().map(|i| match CString::new(i.as_str()) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut()
      } ).collect();
      (*dir_content).dir_size = res.dir_size;
      (*dir_content).files_length = files.len();
      (*dir_content).directories_length = directories.len();
      (*dir_content).files = files.as_mut_ptr();
      (*dir_content).directories = directories.as_mut_ptr();
      std::mem::forget(files);
      std::mem::forget(directories);
      0
    },
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_get_dir_content2(dir_content: *mut dir_content_t, path: *const c_char, depth: u64) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match get_dir_content2(path_rs, &DirOptions{
    depth: depth
  }) {
    Ok(mut res) => {
      res.files.shrink_to_fit();
      res.directories.shrink_to_fit();
      let mut files: Vec<*mut c_char> = res.files.iter().map(|i| match CString::new(i.as_str()) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut()
      } ).collect();
      let mut directories: Vec<*mut c_char> = res.directories.iter().map(|i| match CString::new(i.as_str()) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut()
      } ).collect();
      (*dir_content).dir_size = res.dir_size;
      (*dir_content).files_length = files.len();
      (*dir_content).directories_length = directories.len();
      (*dir_content).files = files.as_mut_ptr();
      (*dir_content).directories = directories.as_mut_ptr();
      std::mem::forget(files);
      std::mem::forget(directories);
      0
    },
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_get_size(path: *const c_char, size: *mut u64) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
    Ok(s) => s,
    Err(_) => return -1,
  };
  match get_size(path_rs) {
    Ok(v) => {
      *size = v;
      0
    },
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_move_dir(from: *const c_char, to: *const c_char, options: *const copy_options_dir_t) -> c_int {
  let opt = dir::CopyOptions{ overwrite: if (*options).overwrite == 0 { false } else { true } ,
                         skip_exist: if (*options).skip_exist == 0 { false } else { true },
                         buffer_size: (*options).buffer_size,
                         copy_inside: if (*options).copy_inside == 0 { false } else { true },
                         content_only: if (*options).content_only == 0 { false } else { true },
                         depth: (*options).depth };
  let from_rs = match CStr::from_ptr(from).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };
  let to_rs = match CStr::from_ptr(to).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match move_dir(from_rs, to_rs, &opt) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_dir_remove(path: *const c_char) -> c_int {
  let path_rs = match CStr::from_ptr(path).to_str() {
      Ok(s) => s,
      Err(_) => return -1,
  };

  match dir::remove(path_rs) {
    Ok(_) => 0,
    Err(_) => -1
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_clean_string(ptr: *mut c_char) {
  if !ptr.is_null() {
    _ = CString::from_raw(ptr);
  }
}

#[no_mangle]
unsafe extern "C" fn fs_extra_clean_dir_content(ptr: *mut dir_content_t) {
  if !ptr.is_null() {
    if !(*ptr).files.is_null() {
      let files = slice::from_raw_parts((*ptr).files, (*ptr).files_length);
      for &i in files {
        if !i.is_null() {
          _ = CString::from_raw(i);
        }
      }
      Vec::from_raw_parts((*ptr).files, (*ptr).files_length, (*ptr).files_length);
    }
    if !(*ptr).directories.is_null() {
      let directories = slice::from_raw_parts((*ptr).directories, (*ptr).directories_length);
      for &i in directories {
        if !i.is_null() {
          _ = CString::from_raw(i);
        }
      }
      Vec::from_raw_parts((*ptr).directories, (*ptr).directories_length, (*ptr).directories_length);
    }
  }
}