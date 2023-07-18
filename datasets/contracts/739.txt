/*
 * MIT License (MIT)
 * Copyright (c) 2019 Activeledger
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

//! # Activeledger Transaction Helper
//!
//! <img src="https://www.activeledger.io/wp-content/uploads/2018/09/Asset-23.png" alt="Activeledger" width="300"/>
//!
//! Activeledger is a powerful distributed ledger technology.
//! Think about it as a single ledger, which is updated simultaneously in multiple locations.
//! As the data is written to a ledger, it is approved and confirmed by all other locations.
//!
//! ## This Crate
//!
//! This crate provides Rust developers an easy way to build up transactions without needing other crates, such as Serde.
//!
//! This crate provides macros as well as builders that help create a transaction with the correct structure.
//! Additionally it provides two methods of creating a complete onboarding transaction. With and without a provided key.
//!
//! ## Additional Activeledger crates
//! Adhearing to the Rust mentality of keeping things small we have created other crates that can be used in conjunction
//! with this one to add additional functionality.
//!
//! These crates are:
//! * [activeledger](https://github.com/activeledger/SDK-Rust) - The main SDK. ([Crate](https://crates.io/crates/activeledger))
//! * [active_sse](https://github.com/activeledger/SDK-Rust-Events) - To build transactions without worrying about the JSON. ([Crate](https://crates.io/crates/active-events))
//!
//! ## Links
//!
//! [Activeledger](https://activeledger.io)
//!
//! [Activeledger Developers portal](https://developers.activeledger.io)
//!
//! [Activeledger on GitHub](https://github.com/activeledger/activeledger)
//!
//! [Activeledger on NPM](https://www.npmjs.com/package/@activeledger/activeledger)
//!
//! [This SDK on GitHub](https://github.com/activeledger/SDK-Rust)
//!
//! [Report Issues](https://github.com/activeledger/SDK-Rust/issues)
//!
//! ## Example usage
//!
//! ```
//! # use active_tx::{PacketBuilder, TransactionBuilder, Key, packet_data, signees};
//! # use activeledger::key::EllipticCurve;
//! # fn main() {
//! let input = packet_data!({"[streamid]": {"input": "data"}});
//!
//! let input_data = PacketBuilder::new(input).build().unwrap();
//!  
//! let mut tx_builder = TransactionBuilder::new("namespace", "contract");
//!
//! let streamid = "streamid";
//! let key = Key::Ec(EllipticCurve::new(streamid).unwrap());
//!
//! let signees = signees![{streamid => key}];
//!
//! let tx = tx_builder
//!     .input(input_data)
//!     .unwrap()
//!     .build(signees)
//!     .unwrap();
//! # }
//! ```
//!
//! For more information on the usage of this crate see the [`TransactionBuilder`] documentation.

mod error;
mod macros;
mod packet_builder;
mod transaction_builder;

pub use error::{TxBuilderError, TxBuilderResult};
pub use packet_builder::{PacketBuilder, PacketData, PacketValue};
pub use transaction_builder::{Key, KeyType, Signees, TransactionBuilder};
