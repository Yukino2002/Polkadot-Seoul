//  Copyright 2021 PolyCrypt GmbH
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

#![deny(warnings)]
#![allow(clippy::ptr_arg)]
#![deny(rustdoc::broken_intra_doc_links)]
#![deny(dead_code)]
#![deny(rustdoc::bare_urls)]
#![deny(unused_imports)]
#![doc(html_logo_url = "https://perun.network/images/Asset%2010.svg")]
#![doc(html_favicon_url = "https://perun.network/favicon-32x32.png")]
#![doc(issue_tracker_base_url = "https://github.com/perun-network/perun-cosmwasm/issues")]

//! *Perun CosmWASM Contracts* provides [go-perun](https://github.com/hyperledger-labs/go-perun) state channels for all Cosmos compatible blockchains.

pub mod contract;
pub mod crypto;
pub mod error;
pub mod msg;
pub mod storage;
#[cfg(test)]
pub mod test;
pub mod types;
