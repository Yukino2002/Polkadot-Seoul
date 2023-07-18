// Copyright 2021 Shin Yoshida
//
// "LGPL-3.0-or-later OR Apache-2.0 OR BSD-2-Clause"
//
// This is part of mouse-sqlite3
//
//  mouse-sqlite3 is free software: you can redistribute it and/or modify
//  it under the terms of the GNU Lesser General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  mouse-sqlite3 is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU Lesser General Public License for more details.
//
//  You should have received a copy of the GNU Lesser General Public License
//  along with mouse-sqlite3.  If not, see <http://www.gnu.org/licenses/>.
//
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
//
// Redistribution and use in source and binary forms, with or without modification, are permitted
// provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this list of
//    conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice, this
//    list of conditions and the following disclaimer in the documentation and/or other
//    materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
// INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
// NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
// PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

//! `mouse-sqlite3` is an implemetation of RDB module for `mouse` .

#![deny(missing_docs)]

mod connection;
mod error;
mod stmt;

pub use connection::Connection;
pub use error::Error;
use std::os::raw::{c_char, c_int, c_void};
use stmt::from_raw as stmt_from_raw;
pub use stmt::Stmt;

mod libsqlite3 {
    #[allow(non_camel_case_types)]
    pub enum sqlite3 {}

    #[allow(non_camel_case_types)]
    pub enum sqlite3_stmt {}
}
use libsqlite3::*;

// Constants for sqlite3_open_v2()
// https://www.sqlite.org/draft/c3ref/c_open_autoproxy.html
const SQLITE_OPEN_READWRITE: c_int = 0x00000002;
const SQLITE_OPEN_CREATE: c_int = 0x00000004;
const SQLITE_OPEN_MEMORY: c_int = 0x00000080;
const SQLITE_OPEN_NOMUTEX: c_int = 0x00008000;

// Error constants
// https://www.sqlite.org/draft/rescode.html
const SQLITE_OK: c_int = 0;
const SQLITE_TOOBIG: c_int = 18;
const SQLITE_RANGE: c_int = 25;
const SQLITE_DONE: c_int = 101;
const SQLITE_ROW: c_int = 100;

// Constants for column type
// https://www.sqlite.org/draft/c3ref/c_blob.html
const SQLITE_INTEGER: c_int = 1;
const SQLITE_BLOB: c_int = 4;
const SQLITE_NULL: c_int = 5;

#[link(name = "sqlite3")]
extern "C" {
    fn sqlite3_open_v2(
        filename: *const c_char,
        ppdb: *mut *mut sqlite3,
        flags: c_int,
        zvfs: *const c_char,
    ) -> c_int;
    fn sqlite3_close(pdb: *mut sqlite3) -> c_int;

    fn sqlite3_prepare_v2(
        pdb: *mut sqlite3,
        zsql: *const c_char,
        nbyte: c_int,
        ppstmt: *mut *mut sqlite3_stmt,
        pztail: *mut *const c_char,
    ) -> c_int;
    fn sqlite3_finalize(pstmt: *mut sqlite3_stmt) -> c_int;
    fn sqlite3_column_count(pstmt: *mut sqlite3_stmt) -> c_int;

    fn sqlite3_bind_blob(
        pstmt: *mut sqlite3_stmt,
        index: c_int,
        pval: *const c_void,
        vlen: c_int,
        destructor: *const c_void,
    ) -> c_int;
    fn sqlite3_bind_int64(pstmt: *mut sqlite3_stmt, index: c_int, val: i64) -> c_int;
    fn sqlite3_bind_null(pstmt: *mut sqlite3_stmt, index: c_int) -> c_int;

    fn sqlite3_clear_bindings(pstmt: *mut sqlite3_stmt) -> c_int;
    fn sqlite3_reset(pstmt: *mut sqlite3_stmt) -> c_int;

    fn sqlite3_step(pstmt: *mut sqlite3_stmt) -> c_int;

    fn sqlite3_column_type(pstmt: *mut sqlite3_stmt, icol: c_int) -> c_int;
    fn sqlite3_column_blob(pstmt: *mut sqlite3_stmt, icol: c_int) -> *const c_void;
    fn sqlite3_column_bytes(pstmt: *mut sqlite3_stmt, icol: c_int) -> c_int;
    fn sqlite3_column_int64(pstmt: *mut sqlite3_stmt, icol: c_int) -> i64;
}
