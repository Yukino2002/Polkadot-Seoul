from flask import Flask
from flask_socketio import SocketIO, emit
import time
import json
from datetime import datetime, timedelta
import pytz
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType
import os
from getpass import getpass
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import DeepLake
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import re
import requests
import ast
from langchain.schema import (AIMessage, HumanMessage, SystemMessage)
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.contracts import ContractCode, ContractInstance
from substrateinterface.exceptions import SubstrateRequestException

substrate_relay = SubstrateInterface(url="wss://shibuya-rpc.dwellir.com")
base_url = "https://shibuya.api.subscan.io"

menemonic = ''
openai = ''
api_key = os.getenv("API_KEY")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


def format_balance(amount: int):
    amount = format(
        amount / 10**substrate_relay.properties.get('tokenDecimals', 0),
        ".15g")
    return f"{amount} {substrate_relay.properties.get('tokenSymbol', 'UNIT')}"


def get_account_balance(account_address):
    result = substrate_relay.query("System", "Account", [account_address])
    balance = (result.value["data"]["free"] + result.value["data"]["reserved"])

    return format_balance(balance)


def get_polkadot_account_balance(account_address):
    result = substrate_relay.query("System", "Account", [account_address])
    balance = (result.value["data"]["free"] + result.value["data"]["reserved"])

    return format_balance(balance)


def send_balance(recipient_address, amount):
    call = substrate_relay.compose_call(call_module='Balances',
                                        call_function='transfer',
                                        call_params={
                                            'dest': recipient_address,
                                            'value': amount * 10**15
                                        })

    extrinsic = substrate_relay.create_signed_extrinsic(
        call=call,
        keypair=Keypair.create_from_mnemonic(menemonic),
        era={'period': 64})

    try:
        receipt = substrate_relay.submit_extrinsic(extrinsic,
                                                   wait_for_inclusion=True)

        print('Extrinsic "{}" included in block "{}"'.format(
            receipt.extrinsic_hash, receipt.block_hash))

        print(receipt)

        if receipt.is_success:
            print('✅ Success, triggered events:')
            for event in receipt.triggered_events:
                print(f'* {event.value}')
        else:
            print('⚠️ Extrinsic Failed: ', receipt.error_message)

        return receipt

    except Substrate_relayRequestException as e:
        print(e)
        return False


def get_transfer_details(extrinsic_index):
    url = base_url + "/api/scan/extrinsic"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    payload = {"extrinsic_index": extrinsic_index}

    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def get_erc20_total_supply(contract_address):
    contract = ContractInstance.create_from_address(
        contract_address=contract_address,
        metadata_file=os.path.join(os.getcwd(), '../assets', 'erc20.json'),
        substrate=substrate_relay)
    result = contract.read(Keypair.create_from_mnemonic(menemonic),
                           'total_supply')

    return str(result['result'])


def get_erc20_of_user(contract_address, user_address):
    contract = ContractInstance.create_from_address(
        contract_address=contract_address,
        metadata_file=os.path.join(os.getcwd(), '../assets', 'erc20.json'),
        substrate=substrate_relay)
    result = contract.read(Keypair.create_from_mnemonic(menemonic),
                           'balance_of',
                           args={'owner': user_address})
    return str(result['result'])


def transfer_erc20_to_user(contract_address, user_address, value):
    contract = ContractInstance.create_from_address(
        contract_address=contract_address,
        metadata_file=os.path.join(os.getcwd(), '../assets', 'erc20.json'),
        substrate=substrate_relay)

    gas_predit_result = contract.read(
        Keypair.create_from_mnemonic(menemonic),
        'transfer',
        args={
            'to': user_address,
            'value': value
        },
    )

    result = contract.exec(Keypair.create_from_mnemonic(menemonic),
                           'transfer',
                           args={
                               'to': user_address,
                               'value': value
                           },
                           gas_limit=gas_predit_result.gas_required)

    return f"Transaction Hash: {result.extrinsic_hash}"


@socketio.on('query')
def handle_query(data):
    print(data)
    weather_data = {"type": "weather", "content": "It's sunny today!"}
    emit('response', weather_data)
    time.sleep(10)

    news_data = {"type": "news", "content": "Latest news update here!"}
    emit('response', news_data)
    time.sleep(10)

    other_data = {"type": "other", "content": "Other type of data!"}
    emit('response', other_data)


@socketio.on('print')
def handle_query(data):
    # check if data is a json
    try:
        data = json.loads(data)
    except:
        return
    print(data)
    # check if it open ai key is not null
    if data['openAIKey'] is None or data['openAIKey'] == "":
        print("no open ai key")
        return
    if data['mnenonic'] is None or data['mnenonic'] == "":
        print("no memonic")
        return

    payload = dict()
    payload['prompt'] = data['prompt'] + "nisoo"
    menemonic = data['mnenonic']
    openai = data['openAIKey']
    session = {
        'user': {
            'name': 'Sybil AI',
            'email': data['session']['user']['email'],
            'image': 'https://i.imgur.com/usI3OTw.png'
        }
    }
    payload['session'] = session
    payload['chatId'] = data['chatId']

    now_utc = datetime.now(pytz.timezone('UTC')) + timedelta(seconds=2)
    payload['createdAt'] = now_utc.isoformat()
    emit('response', payload)


if __name__ == '__main__':
    socketio.run(app)
