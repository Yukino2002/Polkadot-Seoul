#![cfg_attr(not(feature = "std"), no_std)]
extern crate alloc;

use ink_lang as ink;
use pink_extension as pink;

#[ink::contract]
mod fat_p2fa {
    use super::pink;
    use alloc::{
        string::{String, ToString},
        vec::Vec,
    };
    use ink_storage::{traits::SpreadAllocate, Mapping};
    use pink::derive_sr25519_key;
    use scale::{Decode, Encode};
    use ink_env::hash::{Blake2x128, HashOutput};
    use hmac::Mac;
    use data_encoding::BASE32_NOPAD;

    type HmacSha1 = hmac::Hmac<sha1::Sha1>;

    #[ink(storage)]
    #[derive(SpreadAllocate)]
    pub struct FatP2FA {
        digits: u8,
        skew: u8,
        duration: u64,
        salt: Vec<u8>,
        secret: Mapping<AccountId, Vec<u8>>,
        verified: Mapping<AccountId, bool>,
    }

    #[derive(Encode, Decode, Debug, PartialEq, Eq, Copy, Clone)]
    #[cfg_attr(feature = "std", derive(scale_info::TypeInfo))]
    pub enum Error {
        AccountNotInitialized,
        NotVerified,
        InvalidToken,
    }

    impl FatP2FA {
        #[ink(constructor)]
        pub fn new(salt: Vec<u8>, digits: u8, skew: u8, duration: u64) -> Self {
            let salt = derive_sr25519_key!(salt);
            ink_lang::codegen::initialize_contract(|contract: &mut Self| {
                contract.digits = digits;
                contract.skew = skew;
                contract.duration = duration;
                contract.salt = salt;
            })
        }

        #[ink(constructor)]
        pub fn default() -> Self {
            let salt = derive_sr25519_key!(b"p2fa-salt");
            ink_lang::codegen::initialize_contract(|contract: &mut Self| {
                contract.digits = 6;
                contract.skew = 1;
                contract.duration = 30 * 1000;
                contract.salt = salt;
            })
        }

        #[ink(message)]
        pub fn init_2fa(&mut self) -> Result<(), Error> {
            let caller = self.env().caller();
            self.secret.remove(caller.clone());
            self.verified.remove(caller.clone());

            let secret = self.rand_secret();

            self.secret.insert(&caller, &secret);

            Ok(())
        }

        #[ink(message)]
        pub fn get_2fa_url(&self) -> Option<String> {
            let caller = self.env().caller();
            let secret = self.secret.get(&caller)?;

            Some(self.get_url(&secret, "Phala2FA", "PhalaNetwork"))
        }

        #[ink(message)]
        pub fn verify_bind(&mut self, token: String) -> Result<(), Error> {
            let caller = self.env().caller();
            let secret = self.secret.get(&caller)
                .ok_or(Error::AccountNotInitialized)?;
            return if self.check(&token, secret) {
                self.verified.insert(&caller, &true);
                Ok(())
            } else {
                Err(Error::InvalidToken)
            }
        }

        #[ink(message)]
        pub fn verify_token(&self, token: String) -> Result<bool, Error> {
            let caller = self.env().caller();
            let secret = self.secret.get(&caller)
                .ok_or(Error::AccountNotInitialized)?;
            let verified = self.verified.get(&caller)
                .ok_or(Error::NotVerified)?;
            if !verified {
                return Err(Error::NotVerified);
            }
            Ok(self.check(&token, secret))
        }

        #[ink(message)]
        pub fn enabled_2fa(&self) -> bool {
            let caller = self.env().caller();
            return match self.verified.get(&caller) {
                Some(verified) => verified,
                None => false,
            }
        }

        #[ink(message)]
        pub fn unbind_2fa(&mut self, token: String) -> Result<(), Error> {
            let caller = self.env().caller();
            let secret = self.secret.get(&caller)
                .ok_or(Error::AccountNotInitialized)?;
            let verified = self.verified.get(&caller)
                .ok_or(Error::NotVerified)?;
            if !verified {
                return Err(Error::NotVerified);
            }

            if self.check(&token, secret) {
                self.secret.remove(caller.clone());
                self.verified.remove(caller.clone());
            } else {
                return Err(Error::InvalidToken);
            }

            Ok(())
        }

        pub fn rand_secret(&self) -> Vec<u8> {
            let now = self.env().block_number();
            let caller = self.env().caller();

            let mut secret = <Blake2x128 as HashOutput>::Type::default(); // 256-bit buffer
            ink_env::hash_encoded::<Blake2x128, _>(&now.to_be_bytes(), &mut secret);
            ink_env::hash_encoded::<Blake2x128, _>(&caller, &mut secret);
            ink_env::hash_encoded::<Blake2x128, _>(&self.salt.as_slice(), &mut secret);

            secret.to_vec()
        }

        pub fn sign(&self, secret: Vec<u8>, now_ts: u64) -> Vec<u8> {
            hash(
                HmacSha1::new_from_slice(secret.as_ref()).unwrap(),
                (now_ts / self.duration).to_be_bytes().as_ref()
            )
        }

        pub fn generate(&self, secret: Vec<u8>, now_ts: u64) -> String {
            let result: &[u8] = &self.sign(secret, now_ts);
            let offset = (result.last().unwrap() & 15) as usize;
            let result =
                u32::from_be_bytes(
                    result[offset..offset + 4]
                        .try_into()
                        .unwrap()
                ) & 0x7fff_ffff;
            ink_env::format!(
                "{1:00$}",
                self.digits as usize,
                result % (10 as u32).pow(self.digits as u32)
            )
        }

        pub fn check(&self, token: &str, secret: Vec<u8>) -> bool {
            let now_ts = self.env().block_timestamp();
            let base_step = match now_ts == 0 {
                true => 0,
                false => now_ts / self.duration - (self.skew as u64),
            };
            for i in 0..self.skew * 2 + 1 {
                let step_time = (base_step + (i as u64)) * (self.duration as u64);

                // TODO: need a constant time comparing
                if self.generate(secret.clone(), step_time) == token {
                    return true;
                }
            }
            false
        }

        pub fn get_url(&self, secret: &Vec<u8>, label: &str, issuer: &str) -> String {
            ink_env::format!(
                "otpauth://totp/{}?secret={}&issuer={}&digits={}&algorithm={}",
                label.to_string(),
                base32_secret(secret),
                issuer.to_string(),
                self.digits.to_string(),
                "SHA1",
            )
        }
    }

    fn base32_secret(secret: &Vec<u8>) -> String {
        BASE32_NOPAD.encode(secret)
    }

    fn hash<D>(mut digest: D, data: &[u8]) -> Vec<u8>
        where
            D: hmac::Mac,
    {
        digest.update(data);
        digest.finalize().into_bytes().to_vec()
    }
}

#[cfg(test)]
mod tests {
    use ink_lang as ink;

    #[ink::test]
    fn can_init_2fa() {
        use super::fat_p2fa::FatP2FA;
        use pink_extension::chain_extension::mock;
        // Mock derive key call (a pregenerated key pair)
        mock::mock_derive_sr25519_key(|_| {
            hex::decode("78003ee90ff2544789399de83c60fa50b3b24ca86c7512d0680f64119207c80ab240b41344968b3e3a71a02c0e8b454658e00e9310f443935ecadbdd1674c683").unwrap()
        });

        // Test accounts
        let accounts = ink_env::test::default_accounts::<ink_env::DefaultEnvironment>();

        let mut contract = FatP2FA::default();
        assert!(contract.init_2fa().is_ok());
        let init_2fa_ret = contract.get_2fa_url();
        assert_eq!(init_2fa_ret.expect(""), "otpauth://totp/Phala2FA?secret=ZGOCQ4H53ZLIPXHMDAF4HQPP4I&issuer=PhalaNetwork&digits=6&algorithm=SHA1");
    }

    #[ink::test]
    fn can_verify_token() {
        use super::fat_p2fa::FatP2FA;
        use pink_extension::chain_extension::mock;
        // Mock derive key call (a pregenerated key pair)
        mock::mock_derive_sr25519_key(|_| {
            hex::decode("78003ee90ff2544789399de83c60fa50b3b24ca86c7512d0680f64119207c80ab240b41344968b3e3a71a02c0e8b454658e00e9310f443935ecadbdd1674c683").unwrap()
        });

        // Test accounts
        let accounts = ink_env::test::default_accounts::<ink_env::DefaultEnvironment>();

        let mut contract = FatP2FA::default();
        contract.init_2fa();
        assert!(contract.verify_bind("017446".to_string()).is_ok());
    }
}
