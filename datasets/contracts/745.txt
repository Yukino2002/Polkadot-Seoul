#![cfg_attr(not(feature = "std"), no_std)]

use ink_lang as ink;

#[ink::contract]
mod verify_signature {

    #[ink(storage)]
    pub struct VerifySignature {
        signer: AccountId,
    }

    impl VerifySignature {
        #[ink(constructor)]
        pub fn new() -> Self {
            Self { signer: Self::env().caller() }
        }

        #[ink(message)]
        pub fn verify_signature(&self, data: u64, signature: [u8; 65]){
            let encodable = (self.env().account_id(), data);
            let mut message = <ink_env::hash::Sha2x256 as ink_env::hash::HashOutput>::Type::default();
            ink_env::hash_encoded::<ink_env::hash::Sha2x256, _>(&encodable, &mut message);

            let mut output = [0; 33];
            ink_env::ecdsa_recover(&signature, &message, &mut output).expect("recover failed");
            let pub_key = eth::ECDSAPublicKey::from(output);
            let signature_account_id = pub_key.to_default_account_id();
            
            assert!(self.signer == signature_account_id, "invalid signature");
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        use ink_lang as ink;
        use hex_literal;
        use sp_core::Pair;
        use scale::Encode;

        fn default_accounts(
        ) -> ink_env::test::DefaultAccounts<ink_env::DefaultEnvironment> {
            ink_env::test::default_accounts::<ink_env::DefaultEnvironment>()
        }

        fn set_next_caller(caller: AccountId) {
            ink_env::test::set_caller::<ink_env::DefaultEnvironment>(caller);
        }

        fn contract_id() -> AccountId {
            let accounts = default_accounts();
            let contract_id = accounts.bob;
            ink_env::test::set_callee::<ink_env::DefaultEnvironment>(contract_id);
            contract_id
        }

        fn sign(contract_id: AccountId, data: u64) -> [u8; 65] {
            let encodable = (contract_id, data);
            let mut message = <ink_env::hash::Sha2x256 as ink_env::hash::HashOutput>::Type::default(); // 256-bit buffer
            ink_env::hash_encoded::<ink_env::hash::Sha2x256, _>(&encodable, &mut message);

            // Use Alice's seed
            // subkey inspect //Alice --scheme Ecdsa
            let seed = hex_literal::hex!("cb6df9de1efca7a3998a8ead4e02159d5fa99c3e0d4fd6432667390bb4726854");
            let pair = sp_core::ecdsa::Pair::from_seed(&seed);
            let signature = pair.sign(&message).encode();
            let formatted : [u8; 65] = signature[..].try_into().expect("slice with incorrect length");
            formatted
        }

        #[ink::test]
        fn test_verify_signature() {
            let accounts = default_accounts();
            set_next_caller(accounts.alice);
            let verify_signature = VerifySignature::new();

            let contract_id = contract_id();

            set_next_caller(accounts.alice);
            let signature = sign(contract_id, 100);

            verify_signature.verify_signature(100, signature);
        }

        #[ink::test]
        fn test_signature() {
            let accounts = default_accounts();

            // Use Charlie's seed
            // subkey inspect //Charlie --scheme Ecdsa
            let encodable = ("0x6672035dd6010e55e08eb707d171b5ec790bfea44f93ea8b1d22503033de45cd", 500);
            let mut message = <ink_env::hash::Sha2x256 as ink_env::hash::HashOutput>::Type::default(); // 256-bit buffer
            ink_env::hash_encoded::<ink_env::hash::Sha2x256, _>(&encodable, &mut message);

            let seed = hex_literal::hex!("79c3b7fc0b7697b9414cb87adcb37317d1cab32818ae18c0e97ad76395d1fdcf");
            let pair = sp_core::ecdsa::Pair::from_seed(&seed);
            let signature = pair.sign(&message).encode();
            let formatted : [u8; 65] = signature[..].try_into().expect("slice with incorrect length");

            // assert_eq!(sp_core::ecdsa::Pair::verify(&signature, message, &pair.public()), true);

            let mut output = [0; 33];
            ink_env::ecdsa_recover(&formatted, &message, &mut output).expect("recover");
            let pub_key = eth::ECDSAPublicKey::from(output);
            let signature_account_id = pub_key.to_default_account_id();

            ink_env::debug_println!("{:?}", signature_account_id);
            ink_env::debug_println!("{:?}", accounts.charlie);
            
            assert!(accounts.charlie == AccountId::from(signature_account_id), "invalid signature");
            
        }
    }
}
