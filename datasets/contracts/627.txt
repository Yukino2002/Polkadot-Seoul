#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

pub use self::dao::{Dao, DaoRef};

#[ink::contract]
pub mod dao {

	use ink_prelude::{string::String, vec::Vec};
	use ink_storage::{
		traits::{PackedLayout, SpreadAllocate, SpreadLayout},
		Mapping,
	};

	use ink_lang::utils::initialize_contract;
	use ink_storage::traits::KeyPtr;

	pub type ProposalId = u32;
	/// Number of blocks until proposal expires from the proposed block
	const EXPIRATION_BLOCK_FROM_NOW: BlockNumber = 250;

	/// Total member div this number as threshold
	const PROPOSAL_THRESHOLD_DIV: u32 = 2;

	/// Errors that can occur upon calling this contract.
	#[derive(Debug, PartialEq, Eq, scale::Encode, scale::Decode)]
	#[cfg_attr(feature = "std", derive(::scale_info::TypeInfo))]
	pub enum Error {
		AlreadyAMember,
		NotEnoughMembers,
		ThresholdError,
		Overflow,
		Expired,
		NotFound,
		NotExecutable,
		NotEnoughFunds,
		NotSupportedTx,
	}

	/// A Transaction is what `Proposers` can submit for voting.
	/// If votes pass a threshold, it will be executed by the DAO.
	/// Note: Struct from ink repo: multisig example
	#[derive(scale::Encode, scale::Decode, SpreadLayout, PackedLayout, Clone, Debug)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub struct Transaction {
		/// The `AccountId` of the contract that is called in this transaction.
		pub callee: AccountId,
		/// The selector bytes that identifies the function of the callee that should be called.
		pub selector: [u8; 4],
		/// The SCALE encoded parameters that are passed to the called function.
		pub input: Vec<u8>,
		/// The amount of chain balance that is transferred to the callee.
		pub transferred_value: Balance,
		/// Gas limit for the execution of the call.
		pub gas_limit: u64,
	}

	#[derive(
		scale::Encode, scale::Decode, Clone, Copy, SpreadLayout, PackedLayout, Debug, PartialEq,
	)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub enum ProposalStatus {
		Voting,
		Expired,
		Rejected,
		Passed,
		Executed,
	}

	#[derive(scale::Encode, scale::Decode, PackedLayout, SpreadLayout, Debug, SpreadAllocate)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub struct Votes {
		pub yes: u32,
		pub no: u32,
	}

	/// Proposal object created by the `propose` method
	#[derive(scale::Encode, scale::Decode, PackedLayout, SpreadLayout, Debug)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub struct Proposal {
		pub title: String,
		pub metadata_url: String,
		pub proposer: AccountId,
		// current block + EXPIRATION_BLOCK_FROM_NOW
		pub expires: BlockNumber,
		pub tx: ProposalType,
		pub status: ProposalStatus,
		/// Number of votes required to pass = 0.5 total voters the time this was proposed
		pub threshold: u32,
		pub votes: Votes,
	}

	impl Proposal {
		pub fn new(
			title: String,
			metadata_url: String,
			proposer: AccountId,
			current_block: BlockNumber,
			tx: ProposalType,
			members_count: u32,
		) -> Result<Self, Error> {
			let threshold =
				members_count.checked_div(PROPOSAL_THRESHOLD_DIV).ok_or(Error::ThresholdError)?;
			let expires =
				current_block.checked_add(EXPIRATION_BLOCK_FROM_NOW).ok_or(Error::Overflow)?;
			Ok(Self {
				title,
				metadata_url,
				proposer,
				expires,
				tx,
				status: ProposalStatus::Voting,
				threshold,
				votes: Votes { yes: 1, no: 0 },
			})
		}

		pub fn update_status(&mut self, executed: bool) {
			if executed {
				self.status = ProposalStatus::Executed;
			} else if self.votes.yes >= self.threshold {
				self.status = ProposalStatus::Passed;
			} else if self.votes.no >= self.threshold {
				self.status = ProposalStatus::Rejected;
			}
		}

		pub fn ensure_not_expired(&mut self, current_block_num: BlockNumber) -> Result<(), Error> {
			if current_block_num >= self.expires {
				// we do not need to update to if votes passed a threshold
				// as members can only vote once and no revoting
				if self.status == ProposalStatus::Voting {
					self.status = ProposalStatus::Expired;
				}
				return Err(Error::Expired);
			}
			Ok(())
		}

		pub fn can_execute(&self) -> bool {
			self.status == ProposalStatus::Passed
		}
	}

	#[derive(
		scale::Encode, scale::Decode, Clone, Copy, SpreadLayout, PackedLayout, Debug, PartialEq,
	)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub enum DaoType {
		Fanclub,
		Collab,
	}

	/// Type of proposal:
	/// We provide simple DAO operation and generic proxy call
	#[derive(scale::Encode, scale::Decode, Clone, SpreadLayout, PackedLayout, Debug)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub enum ProposalType {
		/// Send funds: Balance to an account: AccountId from the treasury
		Treasury(AccountId, Balance),
		/// Membership change vec of ID to their new did and role
		Membership(Vec<AccountId>, Vec<(String, Role)>),
		/// DAO metadata_url
		UpdateMetadata(String),
		/// DAO joining fee update
		UpdateFee(Balance),
		/// Have the DAO proxy this action, e.g. calling another contract
		Proxy(Transaction),
	}

	impl SpreadAllocate for DaoType {
		#[inline]
		fn allocate_spread(ptr: &mut KeyPtr) -> Self {
			ptr.advance_by(<BlockNumber>::FOOTPRINT * 2);
			Self::Fanclub
		}
	}

	/// Roles in the DAO
	/// Star: Transfer treasury, start poll + proposal
	/// Collab: Start poll + proposal, vote
	/// Member: Vote on poll and proposal
	#[derive(
		scale::Encode, scale::Decode, Clone, Copy, SpreadLayout, PackedLayout, Debug, PartialEq,
	)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub enum Role {
		/// This is usually the content creator(s) that this DAO supports.
		/// They have full access to the DAO funds but cannot vote
		Star,
		/// This is the role that runs a DAO
		/// i.e. in Meetup, they might be volunteers for venue booking, printing marketing materials
		Collab,
		/// This is a member, participant in the DAO and can vote
		Member,
	}

	#[ink(storage)]
	#[derive(SpreadAllocate)]
	pub struct Dao {
		/// name of dao
		name: String,
		/// metadata: ipfs link
		metadata_url: String,
		/// Governance type
		ty: DaoType,
		/// min fee to join
		fee: Balance,
		/// Members list
		members: Mapping<AccountId, (String, Role)>,
		/// Members count
		member_count: u32,
		/// Current proposals
		proposals: Mapping<ProposalId, Proposal>,
		/// total number of proposals
		next_proposal_id: ProposalId,
		/// Proposal Id and its Voting status
		votes: Mapping<(ProposalId, AccountId), bool>,
	}

	#[ink(event)]
	pub struct DaoCreated {
		name: String,
		metadata_url: String,
		joining_fee: Balance,
		ty: DaoType,
	}

	#[ink(event)]
	pub struct Joined {
		#[ink(topic)]
		account: AccountId,
		role: Role,
		total_count: u32,
	}

	#[ink(event)]
	pub struct Proposed {
		#[ink(topic)]
		title: String,
		#[ink(topic)]
		metadata_url: String,
		threshold: u32,
		expires: BlockNumber,
	}

	#[ink(event)]
	pub struct Voted {
		#[ink(topic)]
		proposal_id: ProposalId,
		voter: AccountId,
		#[ink(topic)]
		vote: bool,
		proposal_status: ProposalStatus,
	}

	#[ink(event)]
	pub struct Executed {
		#[ink(topic)]
		proposal_id: ProposalId,
		block: BlockNumber,
		#[ink(topic)]
		proposal_type: ProposalType,
	}

	#[derive(scale::Encode, scale::Decode, Debug, Clone, SpreadLayout, PackedLayout)]
	#[cfg_attr(feature = "std", derive(scale_info::TypeInfo, ink_storage::traits::StorageLayout))]
	pub struct Info {
		name: String,
		ty: DaoType,
		fee: Balance,
		metadata_url: String,
	}

	impl Dao {
		#[ink(constructor)]
		pub fn new(
			name: String,
			metadata_url: String,
			ty: DaoType,
			joining_fee: Balance,
			init_members: Option<Vec<(AccountId, String, Role)>>,
		) -> Self {
			initialize_contract(|c: &mut Self| {
				c.name = name.clone();
				c.ty = ty;
				c.fee = joining_fee;
				c.metadata_url = metadata_url.clone();
				c.members = <Mapping<AccountId, (String, Role)>>::default();

				if let Some(i) = init_members {
					for each in i {
						c.members.insert(each.0, &(each.1.clone(), each.2));
						c.member_count += 1;
						c.env().emit_event(Joined {
							account: each.0,
							role: each.2,
							total_count: c.member_count,
						});
					}
				}

				c.env().emit_event(DaoCreated { name, metadata_url, joining_fee, ty })
			})
		}

		/// Returns some useful info for the DAO
		#[ink(message)]
		pub fn info(&self) -> Info {
			Info {
				name: self.name.clone(),
				ty: self.ty,
				fee: self.fee,
				metadata_url: self.metadata_url.clone(),
			}
		}

		/// Return stars
		#[ink(message)]
		pub fn role_of(&self, member: AccountId) -> Option<Role> {
			if let Some(m) = self.members.get(member) {
				Some(m.1)
			} else {
				None
			}
		}

		/// Return total number of members
		#[ink(message)]
		pub fn total_members(&self) -> u32 {
			self.member_count
		}

		/// Return total proposals
		#[ink(message)]
		pub fn total_proposals(&self) -> u32 {
			self.next_proposal_id
		}

		/// Returns proposal info
		#[ink(message)]
		pub fn proposal_info(&self, proposal_id: ProposalId) -> Option<Proposal> {
			self.proposals.get(proposal_id)
		}

		/// Returns user vote status for the proposal
		#[ink(message)]
		pub fn vote_of(&self, proposal_id: ProposalId, account: AccountId) -> Option<bool> {
			self.votes.get((proposal_id, account))
		}

		/// Joing a DAO as a member
		#[ink(message, payable)]
		pub fn join(&mut self, did: String) -> Result<(), Error> {
			let caller = self.env().caller();
			assert!(self.env().transferred_value() >= self.fee);
			if self.members.contains(caller) {
				return Err(Error::AlreadyAMember);
			}
			self.members.insert(caller, &(did, Role::Member));
			let count = self.member_count;
			self.member_count = count.checked_add(1).ok_or(Error::Overflow)?;
			self.env().emit_event(Joined {
				account: caller,
				role: Role::Member,
				total_count: self.member_count,
			});
			Ok(())
		}

		#[ink(message)]
		pub fn propose(
			&mut self,
			proposal_type: ProposalType,
			title: String,
			metadata_url: String,
		) -> Result<u32, Error> {
			self.ensure_caller_is_member();
			let pid = self.next_proposal_id;
			let proposer = self.env().caller();
			let proposal = Proposal::new(
				title.clone(),
				metadata_url.clone(),
				proposer,
				self.env().block_number(),
				proposal_type,
				self.member_count,
			)?;

			self.proposals.insert(pid, &proposal);
			self.votes.insert((pid, proposer), &true);
			self.next_proposal_id = pid.checked_add(1).expect("Overflow");

			self.env().emit_event(Proposed {
				title,
				metadata_url,
				threshold: proposal.threshold,
				expires: proposal.expires,
			});
			Ok(pid)
		}

		#[ink(message)]
		pub fn vote(&mut self, proposal_id: ProposalId, vote: bool) -> Result<(), Error> {
			self.ensure_caller_is_member();
			self.ensure_new_vote(proposal_id);
			let key = (proposal_id, self.env().caller());
			self.votes.insert(key, &vote);
			let proposal = self.proposals.get(&proposal_id);
			if let Some(mut p) = proposal {
				p.ensure_not_expired(self.env().block_number())?;
				self.proposals.remove(&proposal_id);
				if vote {
					let yes = p.votes.yes;
					p.votes.yes = yes.checked_add(1).ok_or(Error::Overflow)?;
				} else {
					let no = p.votes.no;
					p.votes.no = no.checked_add(1).ok_or(Error::Overflow)?;
				}
				p.update_status(false);
				self.proposals.insert(proposal_id, &p);
				self.env().emit_event(Voted {
					proposal_id,
					voter: self.env().caller(),
					vote,
					proposal_status: p.status,
				});

				Ok(())
			} else {
				Err(Error::NotFound)
			}
		}

		#[ink(message)]
		pub fn execute(&mut self, proposal_id: ProposalId) -> Result<(), Error> {
			if let Some(mut p) = self.proposals.get(&proposal_id) {
				if p.status != ProposalStatus::Passed {
					return Err(Error::NotExecutable);
				}
				self.proposals.remove(&proposal_id);
				match p.tx.clone() {
					ProposalType::Treasury(to, balance) => {
						self.env().transfer(to, balance).map_err(|_| Error::NotEnoughFunds)?;
						p.status = ProposalStatus::Executed;
					},
					ProposalType::Membership(members, roles) => {
						for (i, m) in members.iter().enumerate() {
							if !self.members.contains(m) {
								self.member_count += 1;
							}
							self.members.insert(m, &(roles[i].0.clone(), roles[i].1))
						}
						p.status = ProposalStatus::Executed;
					},
					ProposalType::UpdateMetadata(url) => {
						self.metadata_url = url;
					},
					ProposalType::UpdateFee(fee) => {
						self.fee = fee;
					},
					_ => {
						panic!("not supported")
					},
				};
				self.proposals.insert(proposal_id, &p);
				self.env().emit_event(Executed {
					proposal_id,
					block: self.env().block_number(),
					proposal_type: p.tx,
				});
				Ok(())
			} else {
				Err(Error::NotFound)
			}
		}

		// Helpers
		/// Panic if the sender is not self
		/// Usually used to promote members
		fn ensure_from_dao(&self) {
			assert_eq!(self.env().caller(), self.env().account_id());
		}

		fn ensure_caller_is_member(&self) {
			assert!(self.members.contains(self.env().caller()), "Not caller");
		}

		fn ensure_new_vote(&self, proposal_id: u32) {
			assert!(!self.votes.contains((proposal_id, self.env().caller())), "Repeated vote");
		}
	}

	#[cfg(test)]
	mod tests {
		use super::*;
		use ink_env::test;
		use ink_lang as ink;

		fn default_accounts() -> test::DefaultAccounts<Environment> {
			ink_env::test::default_accounts::<Environment>()
		}

		fn create_collab_dao(
			joining_fee: Balance,
			init_members: Option<Vec<(AccountId, String, Role)>>,
		) -> Dao {
			Dao::new(
				String::from("newDAO"),
				String::from("ipfs"),
				DaoType::Collab,
				joining_fee,
				init_members,
			)
		}

		fn set_caller(caller: AccountId) {
			ink_env::test::set_caller::<Environment>(caller);
		}

		#[ink::test]
		fn create_dao_works() {
			let test_accounts = default_accounts();
			let dao = create_collab_dao(
				2,
				Some(vec![
					(test_accounts.alice, String::from("did:alice"), Role::Star),
					(test_accounts.bob, String::from("did:bob"), Role::Collab),
					(test_accounts.charlie, String::from("did:charlie"), Role::Member),
				]),
			);
			assert_eq!(dao.info().name, "newDAO");
			assert_eq!(dao.info().ty, DaoType::Collab);
			assert_eq!(dao.total_members(), 3);
			assert_eq!(dao.role_of(test_accounts.alice).unwrap(), Role::Star);
			assert_eq!(dao.role_of(test_accounts.bob).unwrap(), Role::Collab);
			assert_eq!(dao.role_of(test_accounts.charlie).unwrap(), Role::Member);
		}

		#[ink::test]
		fn join_works() {
			let test_accounts = default_accounts();
			let mut dao = create_collab_dao(
				2,
				Some(vec![(test_accounts.alice, String::from("did:alice"), Role::Star)]),
			);
			set_caller(test_accounts.bob);
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			dao.join("did:key:bobstring12345".to_string()).unwrap();
			assert_eq!(dao.role_of(test_accounts.bob).unwrap(), Role::Member);
			assert_eq!(dao.total_members(), 2);
		}

		#[ink::test]
		#[should_panic]
		fn join_fails_without_fund() {
			let test_accounts = default_accounts();
			let mut dao = create_collab_dao(
				2,
				Some(vec![(test_accounts.alice, String::from("did:alice"), Role::Star)]),
			);
			set_caller(test_accounts.bob);
			dao.join("did:key:bobstring12345".to_string()).unwrap();
		}

		#[ink::test]
		fn propose_works() {
			let test_accounts = default_accounts();
			let mut dao = create_collab_dao(2, None);
			let proposer = test_accounts.bob;
			let propser_did = "did:key:bobstring12345".to_string();
			let proposal = ProposalType::Treasury(test_accounts.charlie, 1);
			let title = "test proposal".to_string();
			let url = "ipfs::contenthash".to_string();

			// first joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.charlie);
			dao.join("did:key:charliddid".to_string()).unwrap();

			// second joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.eve);
			dao.join("did:key:evedid".to_string()).unwrap();

			// third joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.django);
			dao.join("did:key:djangodid".to_string()).unwrap();

			// third joiner and proposer
			set_caller(proposer);
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			dao.join(propser_did).unwrap();
			let proposal_id = dao.propose(proposal, title.clone(), url.clone()).unwrap();

			assert_eq!(proposal_id, 0);
			let info = dao.proposal_info(proposal_id).unwrap();
			println!("{:?}", info.expires);
			assert_eq!(info.proposer, proposer);
			assert_eq!(info.title, title);
			assert_eq!(info.metadata_url, url);
			assert_eq!(info.expires, EXPIRATION_BLOCK_FROM_NOW);
			assert_eq!(info.threshold, 2);
		}

		#[ink::test]
		fn vote_works() {
			let test_accounts = default_accounts();
			let mut dao = create_collab_dao(2, None);

			let proposer = test_accounts.bob;
			let propser_did = "did:key:bobstring12345".to_string();
			let proposal = ProposalType::Treasury(test_accounts.charlie, 1);
			let title = "test proposal".to_string();
			let url = "ipfs::contenthash".to_string();

			// first joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.charlie);
			dao.join("did:key:charliddid".to_string()).unwrap();

			// second joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.eve);
			dao.join("did:key:evedid".to_string()).unwrap();

			// third joiner and proposer
			set_caller(proposer);
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			dao.join(propser_did).unwrap();
			let proposal_id = dao.propose(proposal, title.clone(), url.clone()).unwrap();

			set_caller(test_accounts.charlie);
			dao.vote(proposal_id, true).unwrap();

			assert_eq!(dao.proposal_info(proposal_id).unwrap().status, ProposalStatus::Passed);
		}

		#[ink::test]
		fn execute_works() {
			let test_accounts = default_accounts();
			let mut dao = create_collab_dao(2, None);

			let proposer = test_accounts.bob;
			let propser_did = "did:key:bobstring12345".to_string();
			let proposal = ProposalType::Treasury(test_accounts.charlie, 1);
			let title = "test proposal".to_string();
			let url = "ipfs::contenthash".to_string();

			// first joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.charlie);
			dao.join("did:key:charliddid".to_string()).unwrap();

			// second joiner
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			set_caller(test_accounts.eve);
			dao.join("did:key:evedid".to_string()).unwrap();

			// third joiner and proposer
			set_caller(proposer);
			ink_env::test::set_value_transferred::<ink_env::DefaultEnvironment>(2);
			dao.join(propser_did).unwrap();
			let proposal_id = dao.propose(proposal, title.clone(), url.clone()).unwrap();

			set_caller(test_accounts.charlie);
			dao.vote(proposal_id, true).unwrap();

			let original_balance =
				ink_env::test::get_account_balance::<ink_env::DefaultEnvironment>(
					test_accounts.charlie,
				)
				.unwrap();

			dao.execute(proposal_id).unwrap();

			let post_balance = ink_env::test::get_account_balance::<ink_env::DefaultEnvironment>(
				test_accounts.charlie,
			)
			.unwrap();

			assert_eq!(post_balance - original_balance, 1);
		}
	}
}
