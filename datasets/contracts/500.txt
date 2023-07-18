#![deny(clippy::dbg_macro)]

use std::{collections::HashMap, sync::Arc, time::Duration};

use anyhow::{Context, Result};
pub use everscale_jrpc_client::{JrpcClient, JrpcClientOptions};
use futures::{channel::oneshot, SinkExt, Stream, StreamExt};
use nekoton::transport::models::ExistingContract;
use rdkafka::topic_partition_list::TopicPartitionListElem;
use rdkafka::{
    config::FromClientConfig,
    consumer::{CommitMode, Consumer, ConsumerContext, StreamConsumer},
    ClientConfig, Message, Offset, TopicPartitionList,
};
use ton_block::{Deserializable, MsgAddressInt};
use ton_block_compressor::ZstdWrapper;
use ton_types::UInt256;
use url::Url;

macro_rules! try_res {
    ($some:expr, $msg:literal) => {
        match $some {
            Ok(a) => a,
            Err(e) => {
                ::log::error!("{}:{:?}", $msg, e);
                continue;
            }
        }
    };
}

macro_rules! try_opt {
    ($some:expr, $msg:literal) => {
        match $some {
            Some(a) => a,
            None => {
                ::log::error!("{}", $msg);
                continue;
            }
        }
    };
}

pub struct TransactionConsumer {
    states_client: Option<JrpcClient>,
    topic: String,
    config: ClientConfig,
    skip_0_partition: bool,
}

pub struct ConsumerOptions<'opts> {
    pub kafka_options: HashMap<&'opts str, &'opts str>,
    /// read from masterchain or not
    pub skip_0_partition: bool,
}

impl TransactionConsumer {
    /// [states_rpc_endpoint] - list of endpoints of states rpcs with /rpc suffix
    pub async fn new<I>(
        group_id: &str,
        topic: &str,
        states_rpc_endpoints: I,
        rpc_options: Option<JrpcClientOptions>,
        options: ConsumerOptions<'_>,
    ) -> Result<Arc<Self>>
    where
        I: IntoIterator<Item = Url>,
    {
        let client = JrpcClient::new(states_rpc_endpoints, rpc_options.unwrap_or_default()).await?;
        Self::with_jrpc_client(group_id, topic, client, options).await
    }

    pub async fn with_jrpc_client(
        group_id: &str,
        topic: &str,
        states_client: JrpcClient,
        options: ConsumerOptions<'_>,
    ) -> Result<Arc<Self>> {
        Ok(Arc::new(
            Self::new_inner(group_id, topic, Some(states_client), options).await,
        ))
    }

    pub async fn without_jrpc_client(
        group_id: &str,
        topic: &str,
        options: ConsumerOptions<'_>,
    ) -> Result<Arc<Self>> {
        Ok(Arc::new(
            Self::new_inner(group_id, topic, None, options).await,
        ))
    }

    async fn new_inner(
        group_id: &str,
        topic: &str,
        states_client: Option<JrpcClient>,
        options: ConsumerOptions<'_>,
    ) -> Self {
        let mut config = ClientConfig::default();
        config
            .set("group.id", group_id)
            .set("enable.auto.commit", "true")
            .set("auto.commit.interval.ms", "5000")
            .set("enable.auto.offset.store", "false")
            .set("auto.offset.reset", "earliest");

        for (k, v) in options.kafka_options {
            config.set(k, v);
        }

        Self {
            states_client,
            topic: topic.to_string(),
            config,
            skip_0_partition: options.skip_0_partition,
        }
    }

    fn subscribe(&self, stream_from: &StreamFrom) -> Result<Arc<StreamConsumer>> {
        let consumer = StreamConsumer::from_config(&self.config)?;
        let mut assignment = TopicPartitionList::new();

        let num_partitions = get_topic_partition_count(&consumer, &self.topic)?;
        let start = if self.skip_0_partition { 1 } else { 0 };
        for x in start..num_partitions {
            assignment.add_partition_offset(
                &self.topic,
                x as i32,
                stream_from
                    .get_offset(x as i32)
                    .with_context(|| format!("No offset for {x} partition"))?,
            )?;
        }

        log::info!("Assigning: {:?}", assignment);
        consumer.assign(&assignment)?;
        Ok(Arc::new(consumer))
    }

    pub async fn stream_transactions(
        &self,
        from: StreamFrom,
    ) -> Result<impl Stream<Item = ConsumedTransaction>> {
        let consumer = self.subscribe(&from)?;

        let (mut tx, rx) = futures::channel::mpsc::channel(1);

        log::info!("Starting streaming");
        tokio::spawn(async move {
            let mut decompressor = ZstdWrapper::new();
            let stream = consumer.stream();
            tokio::pin!(stream);
            while let Some(message) = stream.next().await {
                let message = try_res!(message, "Failed to get message");
                let payload = try_opt!(message.payload(), "no payload");
                let payload_decompressed = try_res!(
                    decompressor.decompress(payload),
                    "Failed decompressing block data"
                );

                tokio::task::yield_now().await;

                let transaction = try_res!(
                    ton_block::Transaction::construct_from_bytes(payload_decompressed),
                    "Failed constructing block"
                );
                let key = try_opt!(message.key(), "No key");
                let key = UInt256::from_slice(key);

                let (block, rx) = ConsumedTransaction::new(
                    key,
                    transaction,
                    message.offset(),
                    message.partition(),
                );
                if let Err(e) = tx.send(block).await {
                    log::error!("Failed sending via channel: {:?}", e); //todo panic?
                    return;
                }

                if rx.await.is_err() {
                    continue;
                }

                try_res!(
                    consumer.store_offset_from_message(&message),
                    "Failed committing"
                );
                log::debug!("Stored offsets");
            }
        });

        Ok(rx)
    }

    pub async fn stream_until_highest_offsets(
        &self,
        from: StreamFrom,
    ) -> Result<(impl Stream<Item = ConsumedTransaction>, Offsets)> {
        let consumer: StreamConsumer = StreamConsumer::from_config(&self.config)?;

        let (tx, rx) = futures::channel::mpsc::channel(1);

        let this = self;

        let highest_offsets = get_latest_offsets(&consumer, &this.topic, self.skip_0_partition)?;
        let mut tpl = TopicPartitionList::new();
        for (part, _) in &highest_offsets {
            if let Err(e) = tpl.add_partition_offset(&this.topic, *part as i32, Offset::Stored) {
                log::warn!("Failed to get stored offset for {}: {:?}", part, e);
                continue;
            }
        }
        let stored = consumer.committed_offsets(tpl, None)?;
        let stored: Vec<TopicPartitionListElem> = stored.elements_for_topic(&this.topic);

        let offsets = Offsets(HashMap::from_iter(
            highest_offsets
                .iter()
                .copied()
                .map(|(k, v)| (k, v.checked_sub(1).unwrap_or(0))),
        ));

        drop(consumer);
        for (part, highest_offset) in offsets.0.iter().map(|(k, v)| (*k, *v)) {
            let commited_offset = if let &StreamFrom::Stored = &from {
                stored
                    .iter()
                    .find(|p| p.partition() == part)
                    .map(|x| x.offset())
            } else {
                None
            };

            // check if we have to skip this partition
            if let Some(Offset::Offset(of)) = commited_offset {
                if of >= highest_offset {
                    log::warn!(
                        "Stored offset is equal to highest offset: {} == {}. Part: {}",
                        of,
                        highest_offset,
                        part
                    );
                    continue;
                }
            }

            if highest_offset == 0 {
                log::warn!(
                    "Skipping partition {}. Highest offset: {}",
                    part,
                    highest_offset
                );
                continue;
            } else {
                log::warn!(
                    "Starting stream for partition {}. Highest offset: {}",
                    part,
                    highest_offset
                );
            }

            let consumer: StreamConsumer = StreamConsumer::from_config(&this.config)?;
            let mut tx = tx.clone();
            let mut tpl = TopicPartitionList::new();
            let ofset = match from.get_offset(part) {
                Some(of) => of,
                None => {
                    log::warn!("No offset for partition {}", part);
                    continue;
                }
            };

            tpl.add_partition_offset(&this.topic, part, ofset)?;
            consumer.assign(&tpl)?;

            tokio::spawn(async move {
                let stream = consumer.stream();
                tokio::pin!(stream);

                let mut decompressor = ZstdWrapper::new();

                while let Some(message) = stream.next().await {
                    let message = try_res!(message, "Failed to get message");

                    let payload = try_opt!(message.payload(), "no payload");
                    let payload_decompressed = try_res!(
                        decompressor.decompress(payload),
                        "Failed decompressing block data"
                    );

                    tokio::task::yield_now().await;

                    let transaction = try_res!(
                        ton_block::Transaction::construct_from_bytes(payload_decompressed),
                        "Failed constructing block"
                    );
                    let key = try_opt!(message.key(), "No key");
                    let key = UInt256::from_slice(key);

                    let (block, rx) = ConsumedTransaction::new(
                        key,
                        transaction,
                        message.offset(),
                        message.partition(),
                    );
                    if let Err(e) = tx.send(block).await {
                        log::error!("Failed sending via channel: {:?}", e); //todo panic?
                        return;
                    }

                    let offset = message.offset();
                    if offset >= highest_offset {
                        log::info!(
                            "Received message with higher offset than highest: {} >= {}. Partition: {}",
                            offset,
                            highest_offset,
                            part
                        );
                        if let Err(e) = consumer.commit_message(&message, CommitMode::Sync) {
                            log::error!("Failed committing final message: {:?}", e);
                        }
                        break;
                    }

                    if rx.await.is_err() {
                        continue;
                    }

                    try_res!(
                        consumer.store_offset_from_message(&message),
                        "Failed committing"
                    );
                    log::debug!("Stored offsets");
                }
            });
        }
        Ok((rx, offsets))
    }

    pub async fn get_contract_state(
        &self,
        contract_address: &MsgAddressInt,
    ) -> Result<Option<ExistingContract>> {
        if let Some(states_client) = &self.states_client {
            states_client.get_contract_state(contract_address).await
        } else {
            anyhow::bail!("Missing states client")
        }
    }

    pub async fn run_local(
        &self,
        contract_address: &MsgAddressInt,
        function: &ton_abi::Function,
        input: &[ton_abi::Token],
    ) -> Result<Option<nekoton_abi::ExecutionOutput>> {
        if let Some(states_client) = &self.states_client {
            states_client
                .run_local(contract_address, function, input)
                .await
        } else {
            anyhow::bail!("Missing states client")
        }
    }

    pub fn get_client(&self) -> &Option<JrpcClient> {
        &self.states_client
    }
}

#[derive(Debug, Clone)]
pub enum StreamFrom {
    Beginning,
    Stored,
    End,
    Offsets(Offsets),
}

impl StreamFrom {
    pub fn get_offset(&self, part: i32) -> Option<Offset> {
        match &self {
            StreamFrom::Beginning => Some(Offset::Beginning),
            StreamFrom::Stored => Some(Offset::Stored),
            StreamFrom::End => Some(Offset::End),
            StreamFrom::Offsets(offsets) => offsets.0.get(&part).map(|x| Offset::Offset(*x)),
        }
    }
}

#[derive(Debug, Clone)]
pub struct Offsets(pub HashMap<i32, i64>);

pub struct ConsumedTransaction {
    pub id: UInt256,
    pub transaction: ton_block::Transaction,

    pub offset: i64,
    pub partition: i32,
    commit_channel: Option<oneshot::Sender<()>>,
}

impl ConsumedTransaction {
    fn new(
        id: UInt256,
        transaction: ton_block::Transaction,
        offset: i64,
        partition: i32,
    ) -> (Self, oneshot::Receiver<()>) {
        let (tx, rx) = oneshot::channel();
        (
            Self {
                id,
                transaction,
                offset,
                partition,
                commit_channel: Some(tx),
            },
            rx,
        )
    }

    pub fn commit(mut self) -> Result<()> {
        let committer = self.commit_channel.take().context("Already committed")?;
        committer
            .send(())
            .map_err(|_| anyhow::anyhow!("Failed committing"))?;
        Ok(())
    }

    pub fn into_inner(self) -> (UInt256, ton_block::Transaction) {
        (self.id, self.transaction)
    }
}

fn get_topic_partition_count<X: ConsumerContext, C: Consumer<X>>(
    consumer: &C,
    topic_name: &str,
) -> Result<usize> {
    let metadata = consumer
        .fetch_metadata(Some(topic_name), Duration::from_secs(30))
        .context("Failed to fetch metadata")?;

    if metadata.topics().is_empty() {
        anyhow::bail!("Topics is empty")
    }

    let partitions = metadata
        .topics()
        .iter()
        .find(|x| x.name() == topic_name)
        .map(|x| x.partitions().iter().count())
        .context("No such topic")?;
    Ok(partitions)
}

fn get_latest_offsets<X: ConsumerContext, C: Consumer<X>>(
    consumer: &C,
    topic_name: &str,
    skip_0_partition: bool,
) -> Result<Vec<(i32, i64)>> {
    let topic_partition_count = get_topic_partition_count(consumer, topic_name)?;
    let mut parts_info = Vec::with_capacity(topic_partition_count);
    let start = if skip_0_partition { 1 } else { 0 };

    for part in start..topic_partition_count {
        let offset = consumer
            .fetch_watermarks(topic_name, part as i32, Duration::from_secs(30))
            .with_context(|| format!("Failed to fetch offset {}", part))?
            .1;
        parts_info.push((part as i32, offset));
    }

    Ok(parts_info)
}

#[cfg(test)]
mod test {
    use std::str::FromStr;

    use ton_block::MsgAddressInt;

    use crate::{ConsumerOptions, TransactionConsumer};

    #[tokio::test]
    async fn test_get() {
        let pr = TransactionConsumer::new(
            "some_group",
            "some_topic",
            vec!["https://jrpc.everwallet.net/rpc".parse().unwrap()],
            None,
            ConsumerOptions {
                kafka_options: Default::default(),
                skip_0_partition: false,
            },
        )
        .await
        .unwrap();

        pr.get_contract_state(
            &MsgAddressInt::from_str(
                "0:8e2586602513e99a55fa2be08561469c7ce51a7d5a25977558e77ef2bc9387b4",
            )
            .unwrap(),
        )
        .await
        .unwrap()
        .unwrap();

        pr.get_contract_state(
            &MsgAddressInt::from_str(
                "-1:efd5a14409a8a129686114fc092525fddd508f1ea56d1b649a3a695d3a5b188c",
            )
            .unwrap(),
        )
        .await
        .unwrap()
        .unwrap();
        assert!(pr
            .get_contract_state(
                &MsgAddressInt::from_str(
                    "-1:aaa5a14409a8a129686114fc092525fddd508f1ea56d1b649a3a695d3a5b188c",
                )
                .unwrap(),
            )
            .await
            .unwrap()
            .is_none());
    }
}
