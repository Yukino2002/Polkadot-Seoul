#![cfg_attr(not(feature = "mock"), no_std)]
#![feature(proc_macro_hygiene)]
extern crate ontio_std as ostd;
use core::option::Option;
use ontio_std::abi::EventBuilder;
use ostd::abi::Error::IrregularData;
use ostd::abi::{Decoder, Encoder, Error, Sink, Source};
use ostd::prelude::*;
use ostd::runtime::{check_witness, contract_delete, contract_migrate};

#[cfg(test)]
mod test;

#[derive(Encoder, Decoder)]
pub struct OrderId {
    pub item_id: Vec<u8>,
    pub tx_hash: H256,
}

impl OrderId {
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut sink = Sink::new(64);
        sink.write(self);
        sink.into()
    }

    pub fn from_bytes(data: &[u8]) -> OrderId {
        let mut source = Source::new(data);
        source.read().unwrap()
    }
}

#[derive(Clone, Encoder, Decoder)]
pub struct TokenTemplate {
    pub data_id: Option<Vec<u8>>,
    pub token_hash: Vec<Vec<u8>>,
    pub endpoint: Vec<u8>,
    pub token_name: Vec<u8>,
    pub token_symbol: Vec<u8>,
}

impl TokenTemplate {
    pub fn from_bytes(data: &[u8]) -> Self {
        let mut source = Source::new(data);
        source.read().unwrap()
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut sink = Sink::new(16);
        sink.write(self);
        sink.bytes().to_vec()
    }
}

impl TokenTemplate {
    pub fn new(
        token_name: Vec<u8>,
        token_symbol: Vec<u8>,
        data_id: Option<Vec<u8>>,
        token_hash: Vec<Vec<u8>>,
        endpoint: Vec<u8>,
    ) -> Self {
        TokenTemplate {
            data_id,
            token_hash,
            endpoint,
            token_name,
            token_symbol,
        }
    }
}

#[derive(Encoder, Decoder, Clone)]
pub struct Fee {
    pub contract_addr: Address,
    pub contract_type: TokenType,
    pub count: u64,
}

impl Fee {
    pub fn default() -> Self {
        Fee {
            contract_addr: Address::new([0u8; 20]),
            contract_type: TokenType::ONG,
            count: 0,
        }
    }
}

#[derive(Clone, Copy)]
pub enum TokenType {
    ONT = 0,
    ONG = 1,
    OEP4 = 2,
}

impl Encoder for TokenType {
    fn encode(&self, sink: &mut Sink) {
        sink.write(*self as u8);
    }
}

impl<'a> Decoder<'a> for TokenType {
    fn decode(source: &mut Source<'a>) -> Result<Self, Error> {
        let ty: u8 = source.read().unwrap();
        match ty {
            0u8 => Ok(TokenType::ONT),
            1u8 => Ok(TokenType::ONG),
            2u8 => Ok(TokenType::OEP4),
            _ => Err(IrregularData),
        }
    }
}

pub struct ContractCommon {
    admin: Address,
}

impl ContractCommon {
    const fn new(admin: Address) -> ContractCommon {
        ContractCommon { admin: admin }
    }

    pub fn admin(&self) -> &Address {
        return &self.admin;
    }

    pub fn destroy(&self) {
        assert!(check_witness(&self.admin));
        contract_delete();
    }

    pub fn migrate(
        &self,
        code: &[u8],
        vm_type: U128,
        name: &str,
        version: &str,
        author: &str,
        email: &str,
        desc: &str,
    ) -> bool {
        assert!(check_witness(&self.admin));
        let new_addr = contract_migrate(code, vm_type as u32, name, version, author, email, desc);
        let empty_addr = Address::new([0u8; 20]);
        assert_ne!(new_addr, empty_addr);
        EventBuilder::new()
            .string("migrate")
            .address(&new_addr)
            .notify();
        true
    }
}

pub const CONTRACT_COMMON: ContractCommon =
    ContractCommon::new(ostd::macros::base58!("Aejfo7ZX5PVpenRj23yChnyH64nf8T1zbu"));

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
