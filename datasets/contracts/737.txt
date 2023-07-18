//
// Copyright (c) 2021 Murilo Ijanc' <mbsd@m0x.ru>
//
// Permission to use, copy, modify, and distribute this software for any
// purpose with or without fee is hereby granted, provided that the above
// copyright notice and this permission notice appear in all copies.
//
// THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
// WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
// MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
// ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
// WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
// ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
// OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
//
use anyhow::{anyhow, Result};
use chrono::{
    serde::ts_milliseconds, DateTime, Datelike, Local, NaiveDate, Utc,
};
use log::debug;
use rust_decimal::prelude::*;
use rust_decimal::Decimal;
use serde::{de, Deserialize, Deserializer, Serialize};
use std::{convert::AsRef, fmt};
use strum_macros::AsRefStr;
use thiserror::Error;

const MB_URL: &str = "https://www.mercadobitcoin.net/api/";

static APP_USER_AGENT: &str =
    concat!(env!("CARGO_PKG_NAME"), "/", env!("CARGO_PKG_VERSION"),);

/// Acrônimo da moeda digital.
#[derive(AsRefStr, Debug, Clone)]
pub enum Coin {
    #[strum(serialize = "AAVE")]
    Aave,
    #[strum(serialize = "ACMFT")]
    Acmft,
    #[strum(serialize = "ACORDO01")]
    Acordo01,
    #[strum(serialize = "ASRFT")]
    Asrft,
    #[strum(serialize = "ATMFT")]
    Atmft,
    #[strum(serialize = "AXS")]
    Axs,
    #[strum(serialize = "BAL")]
    Bal,
    #[strum(serialize = "BARFT")]
    Barft,
    #[strum(serialize = "BAT")]
    Bat,
    #[strum(serialize = "BCH")]
    Bch,
    #[strum(serialize = "BTC")]
    Btc,
    #[strum(serialize = "CAIFT")]
    Caift,
    #[strum(serialize = "CHZ")]
    Chz,
    #[strum(serialize = "COMP")]
    Comp,
    #[strum(serialize = "CRV")]
    Crv,
    #[strum(serialize = "DAI")]
    Dai,
    #[strum(serialize = "DAL")]
    Dal,
    #[strum(serialize = "ENJ")]
    Enj,
    #[strum(serialize = "ETH")]
    Eth,
    #[strum(serialize = "GALFT")]
    Galft,
    #[strum(serialize = "GRT")]
    Grt,
    #[strum(serialize = "IMOB01")]
    Imob01,
    #[strum(serialize = "JUVFT")]
    Juvft,
    #[strum(serialize = "KNC")]
    Knc,
    #[strum(serialize = "LINK")]
    Link,
    #[strum(serialize = "LTC")]
    Ltc,
    #[strum(serialize = "MANA")]
    Mana,
    #[strum(serialize = "MBCONS01")]
    Mbcons01,
    #[strum(serialize = "MBCONS02")]
    Mbcons02,
    #[strum(serialize = "MBFP01")]
    Mbfp01,
    #[strum(serialize = "MBFP02")]
    Mbfp02,
    #[strum(serialize = "MBFP03")]
    Mbfp03,
    #[strum(serialize = "MBFP04")]
    Mbfp04,
    #[strum(serialize = "MBPRK01")]
    Mbprk01,
    #[strum(serialize = "MBPRK02")]
    Mbprk02,
    #[strum(serialize = "MBPRK03")]
    Mbprk03,
    #[strum(serialize = "MBPRK04")]
    Mbprk04,
    #[strum(serialize = "MBVASCO01")]
    Mbvasco01,
    #[strum(serialize = "MCO2")]
    Mco2,
    #[strum(serialize = "MKR")]
    Mkr,
    #[strum(serialize = "OGFT")]
    Ogft,
    #[strum(serialize = "PAXG")]
    Paxg,
    #[strum(serialize = "PSGFT")]
    Psgft,
    #[strum(serialize = "REI")]
    Rei,
    #[strum(serialize = "REN")]
    Ren,
    #[strum(serialize = "SNX")]
    Snx,
    #[strum(serialize = "UMA")]
    Uma,
    #[strum(serialize = "UNI")]
    Uni,
    #[strum(serialize = "USDC")]
    Usdc,
    #[strum(serialize = "WBX")]
    Wbx,
    #[strum(serialize = "XRP")]
    Xrp,
    #[strum(serialize = "YFI")]
    Yfi,
    #[strum(serialize = "ZRX")]
    Zrx,
}

/// Parametros que podem ser usados em alguns endpoints.
pub trait Parameter: fmt::Display {
    fn to_query(&self, base_url: &str) -> String {
        format!("{}{}", base_url, self)
    }

    fn is_valid(&self) -> bool;
}

#[derive(Debug, Clone, Deserialize, Serialize)]
/// Ticker
pub struct Ticker {
    /// Maior preço unitário de negociação das últimas 24 horas.
    #[serde(deserialize_with = "decimal_from_str")]
    pub high: Decimal,
    /// Menor preço unitário de negociação das últimas 24 horas.
    #[serde(deserialize_with = "decimal_from_str")]
    pub low: Decimal,
    /// Quantidade negociada nas últimas 24 horas.
    #[serde(deserialize_with = "decimal_from_str")]
    pub vol: Decimal,
    /// Preço unitário da última negociação.
    #[serde(deserialize_with = "decimal_from_str")]
    pub last: Decimal,
    /// Maior preço de oferta de compra das últimas 24 horas.
    #[serde(deserialize_with = "decimal_from_str")]
    pub buy: Decimal,

    /// Menor preço de oferta de venda das últimas 24 horas.
    #[serde(deserialize_with = "decimal_from_str")]
    pub sell: Decimal,

    /// Data e hora da informação em Era Unix.
    #[serde(with = "ts_milliseconds")]
    pub date: DateTime<Utc>,
}

fn decimal_from_str<'de, D>(deserializer: D) -> Result<Decimal, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;
    Decimal::from_str(&s).map_err(de::Error::custom)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
/// Resposta do método Ticker
struct TickerResp {
    ticker: Ticker,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct OrderBook {
    /// Lista de ofertas de venda, ordenadas do menor para o maior preço.
    ///
    /// Índice 0 preço unitário da oferta de compra.
    /// Índice 1 quantidade da oferta de compra.
    pub asks: Vec<Vec<Decimal>>,
    ///  Lista de ofertas de compras, ordenadas do maior para o menor preço.
    ///
    /// Índice 0 preço unitário da oferta de compra.
    /// Índice 1 quantidade da oferta de compra.
    pub bids: Vec<Vec<Decimal>>,
}

/// Tipo de negociação
#[derive(AsRefStr, Debug, Clone, Serialize, Deserialize)]
pub enum TradeType {
    /// Compra
    #[serde(rename = "sell")]
    Sell,
    /// Venda
    #[serde(rename = "buy")]
    Buy,
}

// Estrutura que representa a negociação
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Trade {
    /// Data e hora da negociação....
    #[serde(with = "ts_milliseconds")]
    pub date: DateTime<Utc>,

    /// Preço unitário da negociação.
    pub price: Decimal,

    /// Quantidade da negociação.
    pub amount: Decimal,

    /// Quantidade da negociação.
    pub tid: usize,

    /// [Indica a ponta executora da negociação.](https://www.mercadobitcoin.com.br/info/execucao-ordem)
    #[serde(rename = "type")]
    pub tp: TradeType,
}

#[derive(Debug, Clone)]
pub struct TradesParameterTid(pub usize);

impl fmt::Display for TradesParameterTid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "?tid={}", self.0)
    }
}

impl Parameter for TradesParameterTid {
    fn is_valid(&self) -> bool {
        if self.0 > 0 {
            true
        } else {
            false
        }
    }
}

impl TradesParameterTid {
    pub fn new(tid: usize) -> Self {
        Self(tid)
    }
}

#[derive(Debug, Clone)]
pub struct TradesParameterSince(pub usize);

impl fmt::Display for TradesParameterSince {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "?since={}", self.0)
    }
}

impl Parameter for TradesParameterSince {
    fn is_valid(&self) -> bool {
        if self.0 > 0 {
            true
        } else {
            false
        }
    }
}

impl TradesParameterSince {
    pub fn new(since: usize) -> Self {
        Self(since)
    }
}

#[derive(Debug, Clone)]
pub struct TradesParameterPeriod(pub DateTime<Utc>, pub DateTime<Utc>);

impl fmt::Display for TradesParameterPeriod {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}/{}/", self.0, self.1)
    }
}

impl Parameter for TradesParameterPeriod {
    // XXX: improve this
    fn is_valid(&self) -> bool {
        let now: DateTime<Local> = Local::now();

        // check both dates
        if self.1 < self.0 {
            return false;
        }

        // check self.0 date
        if self.0.year() == now.year()
            && self.0.month() <= now.month()
            && self.0.day() < now.day()
        {
            return true;
        } else if self.0.year() < now.year() {
            return true;
        } else {
            return false;
        }

        // check self.1 date
        if self.1.year() == now.year()
            && self.1.month() <= now.month()
            && self.1.day() < now.day()
        {
            return true;
        } else if self.1.year() < now.year() {
            return true;
        } else {
            return false;
        }
    }

}

impl TradesParameterPeriod {
    pub fn new(from: DateTime<Utc>, to: DateTime<Utc>) -> Self {
        Self(from, to)
    }

}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DaySummary {
    /// Data do resumo diário
    #[serde(deserialize_with = "naive_date_from_str")]
    pub date: NaiveDate,
    /// Preço unitário de abertura de negociação no dia.
    pub opening: Decimal,
    /// Preço unitário de fechamento de negociação no dia.
    pub closing: Decimal,
    /// Menor preço unitário de negociação no dia.
    pub lowest: Decimal,
    /// Maior preço unitário de negociação no dia.
    pub highest: Decimal,
    /// Volume de Reais (BRL) negociados no dia.
    pub volume: Decimal,
    /// Quantidade da moeda digital negociada no dia.
    pub quantity: Decimal,
    /// Número de negociações realizadas no dia.
    pub amount: usize,
    /// Preço unitário médio das negociações no dia.
    pub avg_price: Decimal,
}

fn naive_date_from_str<'de, D>(deserializer: D) -> Result<NaiveDate, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;
    NaiveDate::parse_from_str(&s, "%Y-%m-%d").map_err(de::Error::custom)
}

#[derive(Debug, Error)]
pub enum MercadoBitcoinError {
    #[error("we don't predict the future: {0}.")]
    InvalidPeriod(String),
    #[error("failed request")]
    Request(#[from] reqwest::Error),
    #[error("parameter is invalid: {0}.")]
    Parameter(String),
    #[error("unknown error")]
    Unknown,
}

#[derive(Debug, Clone)]
pub struct MercadoBitcoin {
    client: reqwest::Client,
}

impl Default for MercadoBitcoin {
    fn default() -> Self {
        Self::new()
    }
}

impl MercadoBitcoin {
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .user_agent(APP_USER_AGENT)
            .build()
            .unwrap();
        Self { client }
    }

    /// Retorna informações com o resumo das últimas 24 horas de negociações.
    pub async fn ticker(
        &self,
        coin: Coin,
    ) -> Result<Ticker> {
        let coin_str = coin.as_ref();
        let method_str = "ticker";
        let url = format!("{}{}/{}/", MB_URL, coin_str, method_str);

        let resp = self.call::<TickerResp>(&url).await?;

        Ok(resp.ticker)
    }

    /// Livro de negociações, ordens abertas de compra e venda.
    ///
    /// Livro de ofertas é composto por duas listas: (1) uma lista com as
    /// ofertas de compras ordenadas pelo maior valor; (2) uma lista com as
    /// ofertas de venda ordenadas pelo menor valor. O livro mostra até 1000
    /// ofertas de compra e até 1000 ofertas de venda.
    ///
    /// Uma oferta é constituída por uma ou mais ordens, sendo assim, a
    /// quantidade da oferta é o resultado da soma das quantidades das ordens
    /// de mesmo preço unitário. Caso uma oferta represente mais de uma ordem,
    /// a prioridade de execução se dá com base na data de criação da ordem, da
    /// mais antiga para a mais nova.
    pub async fn order_book(
        &self,
        coin: Coin,
    ) -> Result<OrderBook> {
        let coin_str = coin.as_ref();
        let method_str = "orderbook";
        let url = format!("{}{}/{}/", MB_URL, coin_str, method_str);

        let resp = self.call::<OrderBook>(&url).await?;

        Ok(resp)
    }

    /// Histórico de negociações realizadas.
    pub async fn trades(
        &self,
        coin: Coin,
        parameter: Option<Box<dyn Parameter>>,
    ) -> Result<Vec<Trade>> {
        let coin_str = coin.as_ref();
        let method_str = "trades";
        let base_url = format!("{}{}/{}/", MB_URL, coin_str, method_str);
        let resp = match parameter {
            Some(parameter) => {
                if parameter.is_valid() {
                    let url = parameter.to_query(&base_url);
                    self.call::<Vec<Trade>>(&url).await?
                } else {
                    let msg = String::from("please check date");
                    return Err(anyhow!(MercadoBitcoinError::Parameter(msg)));
                }
            }
            None => self.call::<Vec<Trade>>(&base_url).await?,
        };

        Ok(resp)
    }

    /// Retorna resumo diário de negociações realizadas.
    pub async fn day_summary(
        &self,
        coin: Coin,
        date: &NaiveDate,
    ) -> Result<DaySummary> {
        let coin_str = coin.as_ref();
        let method_str = "day-summary";
        let now: DateTime<Local> = Local::now();
        let url = format!(
            "{}{}/{}/{}/{}/{}/",
            MB_URL,
            coin_str,
            method_str,
            date.year(),
            date.month(),
            date.day()
        );

        if date.year() == now.year()
            && date.month() <= now.month()
            && date.day() < now.day()
        {
            let resp = self.call::<DaySummary>(&url).await?;
            Ok(resp)
        } else if date.year() < now.year() {
            let resp = self.call::<DaySummary>(&url).await?;
            Ok(resp)
        } else {
            let date_str = format!("{}", date);
            Err(anyhow!(MercadoBitcoinError::InvalidPeriod(date_str)))
        }
    }

    async fn call<T>(&self, url: &str) -> Result<T>
    where
        T: Serialize + for<'de> Deserialize<'de>,
    {
        debug!("Request: {}", url);

        let resp = self.client.get(url).send().await?;

        let obj: T = resp.json().await?;

        Ok(obj)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn btc_coin() {
        let coin = Coin::Btc;
        assert_eq!("BTC", coin.as_ref());
    }
}
