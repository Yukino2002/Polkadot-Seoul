#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
mod task_auction {
    use ink_prelude::string::String;

    #[ink(storage)]
    pub struct TaskAuction {
        description: String,
        pay_multiplier: u8,
        current_bid: Balance,
        contractor: AccountId,
        client: AccountId,
        jury: AccountId,
        deadline: Timestamp,
        extension: Timestamp,

        contractor_confirm: Option<bool>,
        client_confirm: Option<bool>,
    }

    #[ink(event)]
    pub struct Bid {
        #[ink(topic)]
        bid: Balance,
        #[ink(topic)]
        contractor: AccountId,
    }

    #[ink(event)]
    pub struct Confirm {
        #[ink(topic)]
        value: bool,
        #[ink(topic)]
        source: AccountId,
    }

    #[ink(event)]
    pub struct Dispute {
        #[ink(topic)]
        commission: Balance,
        #[ink(topic)]
        jury: AccountId,
    }

    #[ink(event)]
    pub struct Extend {
        #[ink(topic)]
        deadline: Timestamp,
    }

    #[ink(event)]
    pub struct Transfer {
        #[ink(topic)]
        balance: Balance,
        #[ink(topic)]
        account: AccountId,
    }

    impl TaskAuction {
        #[ink(constructor)]
        pub fn new(
            description: String,
            pay_multiplier: u8,
            jury: AccountId,
            duration: Timestamp,
            extension: Timestamp,
        ) -> Self {
            Self {
                description,
                pay_multiplier,
                current_bid: Self::env().balance() / Balance::from(pay_multiplier + 1),
                contractor: Self::env().account_id(),
                client: Self::env().caller(),
                jury,
                deadline: Self::env().block_timestamp() + duration,
                extension,
                contractor_confirm: None,
                client_confirm: None,
            }
        }

        #[ink(message, payable)]
        pub fn extend(&mut self, extension: Timestamp) -> Timestamp {
            assert_eq!(Self::env().caller(), self.client);
            assert!(self.accepting_bids() || self.contractor == Self::env().account_id());
            // add funds on extend call
            if self.contractor == Self::env().account_id() {
                self.current_bid = Self::env().balance() / Balance::from(self.pay_multiplier + 1);
            } else {
                assert!(self.accepting_bids());
            }
            self.deadline += extension;
            Self::env().emit_event(Extend {
                deadline: self.deadline,
            });
            self.deadline
        }

        #[ink(message, payable, selector = "0xCAFEBABE")]
        pub fn bid(&mut self) {
            // only allow bids before deadline
            assert!(self.accepting_bids());
            // bid must be within %50 - %99 of previous bid
            assert!(Self::env().transferred_balance() * 2 > self.current_bid);
            assert!(Self::env().transferred_balance() * 100 < self.current_bid * 99);
            // disallow bids from jury or previous bidder (to discourage spam)
            let caller = Self::env().caller();
            assert_ne!(caller, self.jury);
            assert_ne!(caller, self.contractor);
            // refund previous bidder and update current bid
            Self::transfer_or_terminate(self.current_bid, self.contractor);
            self.update_bid(Self::env().transferred_balance(), caller);
        }

        #[ink(message)]
        pub fn cancel(&mut self) {
            assert!(!self.in_dispute());
            if Self::env().caller() == self.contractor {
                // contractor cancelled
                if self.accepting_bids() {
                    // refund contractor if pre deadline
                    Self::transfer_or_terminate(self.current_bid, self.contractor);
                }
                // reset bid
                self.update_bid(
                    Self::env().balance() / Balance::from(self.pay_multiplier + 1),
                    Self::env().account_id(),
                );
            } else if Self::env().caller() == self.client {
                // client cancelled, refund contractor and terminate auction
                let refund = if self.accepting_bids() {
                    self.current_bid
                } else {
                    // full payment if past deadline
                    self.current_bid * (Balance::from(self.pay_multiplier) + 1)
                };
                Self::transfer_or_terminate(refund, self.contractor);
                Self::env().terminate_contract(self.client);
            } else {
                panic!("unrelated caller");
            }
        }

        #[ink(message)]
        pub fn confirm(&mut self, value: bool) {
            assert!(!self.accepting_bids());
            let source = Self::env().caller();
            // if in dispute, allow jury verdict or concession from either party
            if self.in_dispute() {
                if source == self.jury
                    || ((source == self.client) && value)
                    || ((source == self.contractor) && !value)
                {
                    // jury gets paid either way
                    Self::transfer_or_terminate(self.current_bid, self.jury);
                    Self::env().emit_event(Confirm { value, source });
                    if value {
                        // pay contractor if task deemed to be fulfilled
                        Self::transfer_or_terminate(
                            self.current_bid * (Balance::from(self.pay_multiplier) + 1),
                            self.contractor,
                        );
                    }
                    Self::env().terminate_contract(self.client);
                } else {
                    panic!("unresolved dispute");
                }
            } else if source == self.client {
                self.client_confirm = Some(value);
                Self::env().emit_event(Confirm { value, source });
                // represent no bidder case as well
                if value && self.contractor == Self::env().account_id() {
                    Self::env().terminate_contract(self.client);
                }
            } else if source == self.contractor {
                self.contractor_confirm = Some(value);
                Self::env().emit_event(Confirm { value, source });
            } else {
                panic!("unrelated caller");
            }
            // check if termination conditions are satisfied
            if self.contractor_confirm == Some(true) {
                if self.client_confirm == Some(true) {
                    // mutually confirmed, pay contractor and terminate
                    Self::transfer_or_terminate(
                        self.current_bid * (Balance::from(self.pay_multiplier) + 1),
                        self.contractor,
                    );
                    Self::env().terminate_contract(self.client);
                } else {
                    // dispute triggered
                    Self::env().emit_event(Dispute {
                        commission: self.current_bid,
                        jury: self.jury,
                    });
                }
            }
        }

        /// Predicates

        #[ink(message)]
        pub fn accepting_bids(&self) -> bool {
            Self::env().block_timestamp() < self.deadline
        }

        #[ink(message)]
        pub fn in_dispute(&self) -> bool {
            (self.contractor_confirm, self.client_confirm) == (Some(true), Some(false))
        }

        /// Getters

        #[ink(message)]
        pub fn get_description(&self) -> String {
            self.description.clone()
        }

        #[ink(message)]
        pub fn get_pay_multiplier(&self) -> u8 {
            self.pay_multiplier
        }

        #[ink(message)]
        pub fn get_current_bid(&self) -> Balance {
            self.current_bid
        }

        #[ink(message)]
        pub fn get_current_pay(&self) -> Balance {
            self.current_bid * Balance::from(self.pay_multiplier)
        }

        #[ink(message)]
        pub fn get_contractor(&self) -> AccountId {
            self.contractor
        }

        #[ink(message)]
        pub fn get_client(&self) -> AccountId {
            self.client
        }

        #[ink(message)]
        pub fn get_jury(&self) -> AccountId {
            self.jury
        }

        #[ink(message)]
        pub fn get_deadline(&self) -> Timestamp {
            self.deadline
        }

        #[ink(message)]
        pub fn get_extension(&self) -> Timestamp {
            self.extension
        }

        #[ink(message)]
        pub fn get_contractor_confirm(&self) -> Option<bool> {
            self.contractor_confirm
        }

        #[ink(message)]
        pub fn get_client_confirm(&self) -> Option<bool> {
            self.client_confirm
        }

        /// Internal Helpers

        fn update_bid(&mut self, bid: Balance, contractor: AccountId) {
            self.current_bid = bid;
            self.contractor = contractor;
            self.contractor_confirm = None;
            Self::env().emit_event(Bid { bid, contractor });
            let deadline = Self::env().block_timestamp() + self.extension;
            if deadline > self.deadline {
                self.deadline = deadline;
                Self::env().emit_event(Extend { deadline });
            }
        }

        fn transfer_or_terminate(balance: Balance, account: AccountId) {
            if let Err(_) = Self::env().transfer(account, balance) {
                Self::env().terminate_contract(account);
            }
            Self::env().emit_event(Transfer { balance, account });
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use ink_env::{call, test};
        use ink_lang as ink;

        const BLOCK_DURATION: Timestamp = 5;

        #[ink::test]
        #[should_panic(expected = "attempt to add with overflow")]
        fn pay_multiplier_overflow() {
            TaskAuction::new("test desc".into(), 255, AccountId::from([1; 32]), 0, 0);
        }

        #[ink::test]
        fn auction_extend() {
            let mut task_auction = new_task_auction(100, 1, BLOCK_DURATION, 0);
            assert!(task_auction.accepting_bids());
            advance_block();
            assert!(!task_auction.accepting_bids());
            task_auction.extend(BLOCK_DURATION);
            assert!(task_auction.accepting_bids());
            advance_block();
            assert!(!task_auction.accepting_bids());
        }

        #[ink::test]
        #[should_panic(
            expected = "`(left != right)`\n  left: `AccountId([2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])`,\n right: `AccountId([2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2])`"
        )]
        fn bid_jury_reject() {
            let mut task_auction = new_task_auction(100, 1, BLOCK_DURATION, 0);
            assert_eq!(task_auction.get_current_bid(), 50);
            let accounts = default_accounts();
            call_payable(49, accounts.bob, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
        }

        #[ink::test]
        #[should_panic(
            expected = "Self::env().transferred_balance() * 100 < self.current_bid * 99"
        )]
        fn bid_below_increment() {
            let mut task_auction = new_task_auction(100, 1, BLOCK_DURATION, 0);
            assert_eq!(task_auction.get_current_bid(), 50);
            let accounts = default_accounts();
            call_payable(50, accounts.charlie, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
        }

        #[ink::test]
        #[should_panic(expected = "Self::env().transferred_balance() * 2 > self.current_bid")]
        fn bid_devalue_reject() {
            let mut task_auction = new_task_auction(100, 1, BLOCK_DURATION, 0);
            assert_eq!(task_auction.get_current_bid(), 50);
            let accounts = default_accounts();
            call_payable(10, accounts.charlie, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
        }

        #[ink::test]
        #[should_panic(expected = "self.accepting_bids()")]
        fn bid_closed() {
            let mut task_auction = new_task_auction(1000, 1, BLOCK_DURATION, 0);
            advance_block();
            advance_block();
            let accounts = default_accounts();
            set_sender(accounts.bob);
            task_auction.bid();
        }

        #[ink::test]
        fn bid_rally() {
            let mut task_auction = new_task_auction(1000, 1, BLOCK_DURATION, 0);
            // default contractor is contract itself
            assert_eq!(task_auction.get_current_bid(), 500);
            assert_eq!(task_auction.get_contractor(), contract_id());
            // charlie bids 400
            let accounts = default_accounts();
            call_payable(400, accounts.charlie, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
            assert_eq!(task_auction.get_current_bid(), 400);
            assert_eq!(task_auction.get_contractor(), accounts.charlie);
            // eve bids 300
            call_payable(300, accounts.eve, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
            assert_eq!(task_auction.get_current_bid(), 300);
            assert_eq!(task_auction.get_contractor(), accounts.eve);
            // charlie bids 200
            call_payable(200, accounts.charlie, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
            assert_eq!(task_auction.get_current_bid(), 200);
            assert_eq!(task_auction.get_contractor(), accounts.charlie);
        }

        #[ink::test]
        #[should_panic(expected = "!self.in_dispute()")]
        fn cancel_in_dispute() {
            let mut task_auction = disputed_auction();
            assert!(task_auction.in_dispute());
            task_auction.cancel();
        }

        #[ink::test]
        #[should_panic(expected = "unrelated caller")]
        fn cancel_unrelated_caller() {
            let mut task_auction = on_going_auction();
            set_sender(default_accounts().eve);
            task_auction.cancel();
        }

        #[ink::test]
        fn cancel_client_soft() {
            let mut task_auction = on_going_auction();
            assert!(task_auction.accepting_bids());
            let accounts = default_accounts();
            set_sender(accounts.alice);
            let endowment = get_balance(contract_id()) - task_auction.get_current_bid();
            ink_env::test::assert_contract_termination::<ink_env::DefaultEnvironment, _>(
                move || task_auction.cancel(),
                accounts.alice,
                endowment,
            );
        }

        #[ink::test]
        fn cancel_client_hard() {
            let mut task_auction = on_going_auction();
            advance_block();
            assert!(!task_auction.accepting_bids());
            let accounts = default_accounts();
            set_sender(accounts.alice);
            let endowment = get_balance(contract_id()) - (2 * task_auction.get_current_bid());
            ink_env::test::assert_contract_termination::<ink_env::DefaultEnvironment, _>(
                move || task_auction.cancel(),
                accounts.alice,
                endowment,
            );
        }

        #[ink::test]
        fn cancel_contractor_soft() {
            let mut task_auction = on_going_auction();
            assert!(task_auction.accepting_bids());
            let accounts = default_accounts();
            let pay = task_auction.get_current_bid();
            let charlie_balance = get_balance(accounts.charlie);
            set_sender(accounts.charlie);
            task_auction.cancel();
            assert_eq!(get_balance(accounts.charlie), charlie_balance + pay);
            assert_eq!(task_auction.get_current_bid(), 500);
            assert_eq!(task_auction.get_contractor(), contract_id());
        }

        #[ink::test]
        fn cancel_contractor_hard() {
            let mut task_auction = on_going_auction();
            advance_block();
            assert!(!task_auction.accepting_bids());
            let accounts = default_accounts();
            let charlie_balance = get_balance(accounts.charlie);
            set_sender(accounts.charlie);
            task_auction.cancel();
            assert_eq!(get_balance(accounts.charlie), charlie_balance);
            assert_eq!(task_auction.get_current_bid(), 700);
            assert_eq!(task_auction.get_contractor(), contract_id());
        }

        #[ink::test]
        #[should_panic(expected = "unrelated caller")]
        fn confirm_unrelated_caller() {
            let mut task_auction = on_going_auction();
            assert!(task_auction.accepting_bids());
            advance_block();
            assert!(!task_auction.accepting_bids());
            // jury is ignored until dispute
            set_sender(default_accounts().bob);
            task_auction.confirm(true);
        }

        #[ink::test]
        #[should_panic(expected = "unresolved dispute")]
        fn confirm_unresolved_dispute() {
            let mut task_auction = disputed_auction();
            // confirm from client doesn't resolve dispute
            task_auction.confirm(false);
        }

        #[ink::test]
        fn dispute_verdict_client() {
            let mut task_auction = disputed_auction();
            let client = task_auction.get_client();
            let contractor = task_auction.get_contractor();
            let jury = task_auction.get_jury();
            let contractor_balance = get_balance(contractor);
            let client_balance = get_balance(client);
            let jury_balance = get_balance(jury);
            let contract_balance = get_balance(contract_id());
            let commission = task_auction.get_current_bid();
            set_sender(task_auction.get_jury());
            ink_env::test::assert_contract_termination::<ink_env::DefaultEnvironment, _>(
                move || task_auction.confirm(false),
                client,
                contract_balance - commission,
            );
            assert_eq!(
                get_balance(client),
                client_balance + contract_balance - commission
            );
            assert_eq!(get_balance(contractor), contractor_balance);
            assert_eq!(get_balance(jury), jury_balance + commission);
        }

        #[ink::test]
        fn dispute_verdict_contractor() {
            let mut task_auction = disputed_auction();
            let client = task_auction.get_client();
            let contractor = task_auction.get_contractor();
            let jury = task_auction.get_jury();
            let contractor_balance = get_balance(contractor);
            let client_balance = get_balance(client);
            let jury_balance = get_balance(jury);
            let contract_balance = get_balance(contract_id());
            let commission = task_auction.get_current_bid();
            set_sender(task_auction.get_jury());
            ink_env::test::assert_contract_termination::<ink_env::DefaultEnvironment, _>(
                move || task_auction.confirm(true),
                client,
                contract_balance - 3 * commission,
            );
            assert_eq!(
                get_balance(client),
                client_balance + contract_balance - (3 * commission)
            );
            assert_eq!(
                get_balance(contractor),
                contractor_balance + (2 * commission)
            );
            assert_eq!(get_balance(jury), jury_balance + commission);
        }

        #[ink::test]
        fn successful_auction() {
            let mut task_auction = on_going_auction();
            assert!(task_auction.accepting_bids());
            advance_block();
            assert!(!task_auction.accepting_bids());
            let client = task_auction.get_client();
            let contractor = task_auction.get_contractor();
            let bid = task_auction.get_current_bid();
            let returned_funds = get_balance(contract_id())
                - ((1 + task_auction.get_pay_multiplier()) as Balance * bid);
            set_sender(contractor);
            task_auction.confirm(true);
            set_sender(client);
            ink_env::test::assert_contract_termination::<ink_env::DefaultEnvironment, _>(
                move || task_auction.confirm(true),
                client,
                returned_funds,
            );
        }

        #[ink::test]
        fn no_bidders() {
            // create auction
            let endowment = 1000;
            let mut task_auction = new_task_auction(endowment, 1, BLOCK_DURATION, 0);
            // check that auction is closed before confirm
            assert!(task_auction.accepting_bids());
            advance_block();
            assert!(!task_auction.accepting_bids());
            // if client terminate only if true
            let accounts = default_accounts();
            set_sender(accounts.alice);
            task_auction.confirm(false);
            let alice_balance = get_balance(accounts.alice);
            assert_eq!(task_auction.get_current_bid(), 500);
            assert_eq!(get_balance(contract_id()), endowment);
            // check that contract terminated after confirmation
            ink_env::test::assert_contract_termination::<ink_env::DefaultEnvironment, _>(
                move || task_auction.confirm(true),
                accounts.alice,
                endowment,
            );
            // ensure that original owner received full funds
            assert_eq!(alice_balance + endowment, get_balance(accounts.alice));
            // one confirm event and one transfer event in termination
            let emitted_events = ink_env::test::recorded_events().collect::<Vec<_>>();
            assert_eq!(2, emitted_events.len());
        }

        // helper functions

        fn new_task_auction(
            endowment: Balance,
            pay_multiplier: u8,
            duration: Timestamp,
            extension: Timestamp,
        ) -> TaskAuction {
            // given
            let accounts = default_accounts();
            set_sender(accounts.alice);
            set_balance(contract_id(), endowment);
            TaskAuction::new(
                "task descripton".into(),
                pay_multiplier,
                accounts.bob,
                duration,
                extension,
            )
        }

        fn on_going_auction() -> TaskAuction {
            let mut task_auction = new_task_auction(1000, 1, BLOCK_DURATION, 0);
            let accounts = default_accounts();
            // HACK: compensate for extra pay accumulation, due contract self transfer broken in off-chain tests
            set_balance(
                contract_id(),
                get_balance(contract_id()) - task_auction.get_current_bid(),
            );
            call_payable(400, accounts.charlie, [0xCA, 0xFE, 0xBA, 0xBE], || {
                task_auction.bid();
                ()
            });
            assert_eq!(get_balance(contract_id()), 1400);
            assert_eq!(task_auction.get_current_bid(), 400);
            assert_eq!(task_auction.get_contractor(), accounts.charlie);
            task_auction
        }

        fn disputed_auction() -> TaskAuction {
            let mut task_auction = on_going_auction();
            advance_block();
            assert!(!task_auction.accepting_bids());
            assert!(!task_auction.in_dispute());
            task_auction.confirm(true);
            let accounts = default_accounts();
            set_sender(accounts.alice);
            task_auction.confirm(false);
            assert!(task_auction.in_dispute());
            task_auction
        }

        fn advance_block() {
            ink_env::test::advance_block::<ink_env::DefaultEnvironment>()
                .expect("Cannot advance block");
        }

        fn contract_id() -> AccountId {
            ink_env::test::get_current_contract_account_id::<ink_env::DefaultEnvironment>()
                .expect("Cannot get contract id")
        }

        fn set_sender(sender: AccountId) {
            let callee =
                ink_env::account_id::<ink_env::DefaultEnvironment>().unwrap_or([0x0; 32].into());
            test::push_execution_context::<Environment>(
                sender,
                callee,
                1000000,
                1000000,
                test::CallData::new(call::Selector::new([0x00; 4])), // dummy
            );
        }

        fn default_accounts() -> ink_env::test::DefaultAccounts<ink_env::DefaultEnvironment> {
            ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
                .expect("Off-chain environment should have been initialized already")
        }

        fn set_balance(account_id: AccountId, balance: Balance) {
            ink_env::test::set_account_balance::<ink_env::DefaultEnvironment>(account_id, balance)
                .expect("Cannot set account balance");
        }

        fn get_balance(account_id: AccountId) -> Balance {
            ink_env::test::get_account_balance::<ink_env::DefaultEnvironment>(account_id)
                .expect("Cannot set account balance")
        }

        /// Calls a payable message, increases the contract balance before
        /// invoking `f`.
        fn call_payable<F>(amount: Balance, from: AccountId, selector: [u8; 4], f: F)
        where
            F: FnOnce() -> (),
        {
            let contract_id = contract_id();
            set_sender(from);

            let mut data = ink_env::test::CallData::new(ink_env::call::Selector::new(selector));
            data.push_arg(&from);

            // Push the new execution context which sets `from` as caller and
            // the `amount` as the value which the contract  will see as transferred
            // to it.
            ink_env::test::push_execution_context::<ink_env::DefaultEnvironment>(
                from,
                contract_id,
                1000000,
                amount,
                data,
            );

            set_balance(contract_id, get_balance(contract_id) + amount);
            f();
        }
    }
}
