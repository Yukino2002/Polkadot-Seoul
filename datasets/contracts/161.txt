//! # Ink-Governance
//!
//! Ink-Governance is a library crate to simplify the creation of governance based smart contracts written in [ink!](https://use.ink/).
//! It’s supposed to be an extension of the [open-brush library](https://openbrush.io/) , so it depends on it.
//!
//! It is a modular system where the resulting smart contract is composed of a core governor module where a sub-module for counting the votes
//! and one for extracting the weight of the votes must be added. Other optional extensions can be added to costumize the module.
//! Each module is imported by a feature flag in Cargo.toml dependencies import.
//! List of all features [here](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/Cargo.toml).
//!
//! Example of Cargo.toml
//!
//!
//! ```ignore
//! [dependencies]
//!
//! ink        = { version = "~4.0.0", default-features = false }
//! openbrush  = { git = "https://github.com/727-Ventures/openbrush-contracts", default-features = false }
//! scale      = { package = "parity-scale-codec", version = "3.4.0", default-features = false, features = ["derive"] }
//! scale-info = { version = "2.3.1", default-features = false, features = ["derive"], optional = true }
//!
//! ink-governance = { version = "0.1.0", default-features = false, features = ["governor_group"] }
//!
//! [dev-dependencies]
//! ink_e2e = { version = "~4.0.0" }
//!
//! [features]
//! default = ["std"]
//! std = [
//!    "ink/std",
//!    "scale/std",
//!    "scale-info/std",
//!    "openbrush/std",
//!    "ink-governance/std"
//! ]
//!
//! ink-as-dependency = []
//! e2e-tests = []
//! ```
//!
//! ## Governance Modules
//!
//! | Name | Trait definition | Traits default implementation |Crate Feature |  Description |
//! | :-------- | :------- | :--------------| :------------| :-----|
//! | governor  |  [Governor](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/traits/governance/governor.rs)  | [Governor](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/governance/governor.rs)  |["governor"] | Core of the governance system.   |
//! | counting_simple | [CountingSimple](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/traits/governance/modules/counting_simple.rs)| [CountingSimple](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/governance/modules/governor_counting_simple.rs) | ["counting_simple"] | Simple voting mechanism with 3 voting options: Against, For and Abstain.|
//! | voting_group | [VotingGroup](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/traits/governance/modules/voting_group.rs) | [VotingGroup](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/governance/modules/governor_voting_group.rs)| ["voting_group"] | Extracts voting weight from a group of members controlled by an admin.
//!
//! ## Extensions
//!
//! | Name | Trait definition | Traits default implementation |Crate Feature |  Description |
//! | :-------- | :------- | :--------------| :------------| :-----|
//! | governor_settings  |  [GovernorSettings](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/traits/governance/extensions/settings.rs)  | [GovernorSettings](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/governance/extensions/governor_settings.rs)  |["governor_settings"] | Extension of Governor to update settings through governance.   |
//!
//! ## Other Modules
//!
//! | Name | Trait definition | Traits default implementation |Crate Feature |  Description |
//! | :-------- | :------- | :--------------| :------------| :-----|
//! | psp22_votes  |  [PSP22Votes](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/traits/token/psp22/extensions/votes.rs)  | [PSP22Votes](https://github.com/alessandro-baldassarre/ink-governance/blob/main/crate/src/token/psp22/extensions/psp22_votes.rs)  |["psp22_votes"] | Extension of PSP22 to support voting and delegation.   |
//!
//! ## How to use
//!
//! You can find complete implementations in the [tests](https://github.com/alessandro-baldassarre/ink-governance/tree/main/tests) folder.
//!
//! ```ignore
//! #[openbrush::contract]
//! pub mod gov_group {
//!
//! // --snip--
//!    
//! #[ink(storage)]
//!        #[derive(Default, Storage)]
//!        pub struct Contract {
//!            #[storage_field]
//!            governor: Data<Counting,Voting>,
//!        }
//!
//!        impl Governor for Contract {}
//!
//!        impl VotingGroup for Contract {}
//!
//!        impl CountingSimple for Contract {}
//!
//!        impl Contract {
//!
//!        #[ink(constructor)]
//!        pub fn new(
//!            admin: Option<AccountId>,
//!            init_members: Vec<VotingMember>,
//!        ) -> Result<Self, ContractError> {
//!
//!            let mut instance = Self::default();
//!
//!            let admin = admin.unwrap_or(Self::env().caller());
//!
//!            VotingGroup::_init_members(
//!                &mut instance,
//!                admin,
//!                init_members,
//!            )?;
//!
//!            Ok(instance)
//!        }
//!    }
//! }
//! ```

#![cfg_attr(not(feature = "std"), no_std)]
#![feature(min_specialization)]

/// Traits definition and wrappers used in ink_governance contracts
pub mod traits;

mod governance;
mod token;

#[cfg(feature = "governor")]
pub use governance::governor;

#[cfg(feature = "governor_settings")]
pub use governance::extensions::governor_settings;

#[cfg(feature = "governor_counting_simple")]
pub use governance::modules::governor_counting_simple;

#[cfg(feature = "governor_voting_group")]
pub use governance::modules::governor_voting_group;

#[cfg(feature = "psp22_votes")]
pub use token::psp22::extensions::psp22_votes;
