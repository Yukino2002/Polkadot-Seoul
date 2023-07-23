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
import subprocess
from langchain.schema import (AIMessage, HumanMessage, SystemMessage)
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.contracts import ContractCode, ContractInstance
from substrateinterface.exceptions import SubstrateRequestException

substrate_relay = SubstrateInterface(url="wss://shibuya-rpc.dwellir.com")
base_url = "https://shibuya.api.subscan.io"

mnemonic = ''
openai = ''
api_key = os.getenv("API_KEY")

embeddings = OpenAIEmbeddings()
db = DeepLake(
    dataset_path=f"hub://commanderastern/polka-code-3",
    read_only=True,
    embedding_function=embeddings,
)

retriever = db.as_retriever()
retriever.search_kwargs["distance_metric"] = "cos"
retriever.search_kwargs["fetch_k"] = 20
retriever.search_kwargs["maximal_marginal_relevance"] = True
retriever.search_kwargs["k"] = 20

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
        keypair=Keypair.create_from_mnemonic(mnemonic),
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
    result = contract.read(Keypair.create_from_mnemonic(mnemonic),
                           'total_supply')

    return str(result['result'])


def get_erc20_of_user(contract_address, user_address):
    contract = ContractInstance.create_from_address(
        contract_address=contract_address,
        metadata_file=os.path.join(os.getcwd(), '../assets', 'erc20.json'),
        substrate=substrate_relay)
    result = contract.read(Keypair.create_from_mnemonic(mnemonic),
                           'balance_of',
                           args={'owner': user_address})
    return str(result['result'])


def transfer_erc20_to_user(contract_address, user_address, value):
    contract = ContractInstance.create_from_address(
        contract_address=contract_address,
        metadata_file=os.path.join(os.getcwd(), '../assets', 'erc20.json'),
        substrate=substrate_relay)
    gas_predit_result = contract.read(
        Keypair.create_from_mnemonic(mnemonic),
        'transfer',
        args={
            'to': user_address,
            'value': value
        },
    )
    result = contract.exec(Keypair.create_from_mnemonic(mnemonic),
                           'transfer',
                           args={
                               'to': user_address,
                               'value': value
                           },
                           gas_limit=gas_predit_result.gas_required)

    return f"Transaction Hash: {result.extrinsic_hash}"


def filter(x):
    # filter based on source code
    if "something" in x["text"].data()["value"]:
        return False

    # filter based on path e.g. extension
    metadata = x["metadata"].data()["value"]
    return "only_this" in metadata["source"] or "also_that" in metadata[
        "source"]


def run_command(command):
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"Error occurred: {error.decode().strip()}")
    else:
        print(f"Output: {output.decode().strip()}")


def genCompileDeployContract(description: str):
    '''
    Generate, compile and deploy a contract to Shibuya Testnet
    '''
    questions = [
        f"""
    Give me a basic ink contract code, 
    Description of code = {description}
    """ + """
    -- There should be no print statments in the contract return everything.
    -- enclose the contract content in #startContract# and #endContract#
    -- follow this basic format when generating the code

    #startContract#
    #[ink::contract]
    mod contract_name \{

    }
    #endContract#
    """
    ]

    chat_history = []

    # extrating the contract code from the result
    result = qa({"question": questions[0], "chat_history": chat_history})
    chat_history.append((questions[0], result["answer"]))

    pattern = r'#startContract#(.*?)#endContract#'
    pattern2 = r'```rust(.*?)```'
    contract_code = re.search(pattern, result["answer"], re.DOTALL)
    res = ""

    if contract_code:
        res = contract_code.group(1).strip()
    else:
        contract_code = re.search(pattern2, result["answer"], re.DOTALL)
        if contract_code:
            res = contract_code.group(1).strip()
    res = r"""#![cfg_attr(not(feature = "std"), no_std, no_main)]""" + '\n' + res
    post_process_code = re.sub(r'^\s*use.*\n?', '', res, flags=re.MULTILINE)

    post_process_code = re.sub(r'^\s*struct',
                               'pub struct',
                               post_process_code,
                               flags=re.MULTILINE)

    post_process_code = re.sub(r'^\s*#\s*\[derive\(.*\n?',
                               '',
                               post_process_code,
                               flags=re.MULTILINE)

    print(post_process_code)

    # generating the constructor args
    new_function_pattern = r'(pub fn new.*?\))'
    new_function_match = re.search(new_function_pattern, post_process_code,
                                   re.DOTALL)

    if new_function_match:
        res = new_function_match.group(0)
    print(res)
    chat = ChatOpenAI()
    messages = [
        SystemMessage(content=r"""
        give the argumentsvalues for "pub fn new(value1: i32, value2: i32)" in the form of a dictionary
        -- Just the dictionary
        -- No need fore explanation or additional code
        -- empty dictionary is also fine
        -- for invalid input empty dictionary will be returned
        example: 
        Input: pub fn new(coolVal: i32)
        Output: {"coolVal": 1}"""),
        HumanMessage(content=f"{res}")
    ]
    constructor_args = ast.literal_eval(chat(messages).content)

    with open('code/lib.rs', 'w') as file:
        file.write(post_process_code)

    # compiling contract
    print(run_command("cd code && cargo contract build"))

    # Upload WASM code
    code = ContractCode.create_from_contract_files(
        metadata_file=os.path.join(os.getcwd(), 'code/target/ink',
                                   'my_contract.json'),
        wasm_file=os.path.join(os.getcwd(), 'code/target/ink',
                               'my_contract.wasm'),
        substrate=substrate_relay)

    # Deploy contract
    print('Deploy contract...')
    contract = code.deploy(keypair=Keypair.create_from_mnemonic(menemonic),
                           constructor="new",
                           args=constructor_args,
                           value=0,
                           gas_limit={
                               'ref_time': 25990000000,
                               'proof_size': 1199000
                           },
                           upload_code=True)

    return contract.contract_address


class GetAccountBalanceInput(BaseModel):
    """Inputs for get_account_balance"""

    account_address: str = Field(
        description="the address of the account to get the balance of")


class GetAccountBalanceTool(BaseTool):
    name = "get_account_balance"
    description = """
        Useful when you want to get the balance of an polkadot account.
        The account address is the address of the account you want to get the balance of.
        The address format is ss58 encoded.
        """
    args_schema: Type[BaseModel] = GetAccountBalanceInput

    def _run(self, account_address: str):
        account_balance = get_account_balance(account_address)
        return account_balance

    def _arun(self, account_address: str):
        raise NotImplementedError(
            "get_current_stock_price does not support async")


class GenerateInkPolkadotContractInput(BaseModel):
    """Inputs for generate_ink_polkadot_contract"""

    contract_description: str = Field(
        description=
        "A description in simple english of what you would like the contract to do"
    )


class GenerateInkPolkadotContractTool(BaseTool):
    name = "generate_ink_polkadot_contract"
    description = """
        Useful when you want to generate a polkadot contract in ink or just an ink contract.
        The contract description is a description of what you would like the contract to do.
        
        This also deploys the code to Shibuya Testnet.

        returns the contract address
        """
    args_schema: Type[BaseModel] = GenerateInkPolkadotContractInput

    def _run(self, contract_description: str):
        address = genCompileDeployContract(contract_description)
        return address

    def _arun(self, account_address: str):
        raise NotImplementedError(
            "get_current_stock_price does not support async")


class SendSubstrateBalanceInput(BaseModel):
    """Inputs for send_substrate_balance"""

    recipient_address: str = Field(
        description="the address of the account to send the balance to")
    amount: float = Field(description="the amount to send.")


class SendSubstrateBalanceTool(BaseTool):
    name = "send_substrate_balance"
    description = """
        Useful when you want to send a balance to a polkadot account.
        If balance is not specified send 0.001
        We will be sending Shibuya Testnet tokens/SBY.
        returns the extrinsic hash if successful
        """
    args_schema: Type[BaseModel] = SendSubstrateBalanceInput

    def _run(self, recipient_address: str, amount: int):
        res = send_balance(recipient_address, amount)
        return res.extrinsic_hash

    def _arun(self, account_address: str):
        raise NotImplementedError(
            "get_current_stock_price does not support async")


class ListAllTransactionsInput(BaseModel):
    """Inputs for list_all_transactions"""

    account_address: str = Field(
        description="the address of the account to get the transactions of")


class ListAllTransactionsTool(BaseTool):
    name = "list_all_transactions"
    description = """
        Useful when you want to list all transactions of a polkadot account.
        Lists the last first 3 and last 3 transactions.
        """
    args_schema: Type[BaseModel] = ListAllTransactionsInput

    def _run(self, account_address: str):
        res = get_account_transfers(account_address)
        return res

    def _arun(self, account_address: str):
        raise NotImplementedError(
            "list_all_transactions does not support async")


class GetTransferDetailsInput(BaseModel):
    """Inputs for get_transfer_details"""

    extrinsic_hash: str = Field(
        description=
        "the extrinsic hash of the transaction to get the details of, starts with 0x"
    )


class GetTransferDetailsTool(BaseTool):
    name = "get_transfer_details"
    description = """
        Useful when you want to get the details of a transaction.
        returns code, if successful, block time and data if it exists.
        """
    args_schema: Type[BaseModel] = GetTransferDetailsInput

    def _run(self, extrinsic_hash: str):
        res = get_transfer_details(extrinsic_hash)
        return ["successfully retreived data. Data:", res]

    def _arun(self, account_address: str):
        raise NotImplementedError(
            "get_transfer_details does not support async")


class GetERC20TotalSupplyInput(BaseModel):
    """Inputs for get_erc20_total_supply"""

    contract_address: str = Field(
        description="the address of the contract to get the total supply of")


class GetERC20TotalSupplyTool(BaseTool):
    name = "get_erc20_total_supply"
    description = """
        Useful when you want to get the total supply of an ERC20 token.
        The address of the contract should be given
        returns the total supply of the ERC20 token.
        """
    args_schema: Type[BaseModel] = GetERC20TotalSupplyInput

    def _run(self, contract_address: str):
        res = get_erc20_total_supply(contract_address)
        return res

    def _arun(self, account_address: str):
        raise NotImplementedError(
            "get_erc20_total_supply does not support async")


class GetERC20OfUserInput(BaseModel):
    """Inputs for get_erc20_of_user"""

    contract_address: str = Field(
        description="the address of the contract to get the balance of")
    user_address: str = Field(
        description="the address of the user to get the balance of")


class GetERC20OfUserTool(BaseTool):
    name = "get_erc20_of_user"
    description = """
        Useful when you want to get the balance of an ERC20 token of a user when given user address.
        The address of the contract should be given
        returns the balance of the ERC20 token of the user.
        """
    args_schema: Type[BaseModel] = GetERC20OfUserInput

    def _run(self, contract_address: str, user_address: str):
        res = get_erc20_of_user(contract_address, user_address)
        return res

    def _arun(self, account_address: str):
        raise NotImplementedError("get_erc20_of_user does not support async")


class TransferERC20ToUserInput(BaseModel):
    """Inputs for transfer_erc20"""

    contract_address: str = Field(
        description="the address of the contract to transfer the balance of")
    user_address: str = Field(
        description="the address of the user to transfer the balance of")
    amount: int = Field(description="the amount to transfer")


class TransferERC20ToUserTool(BaseTool):
    name = "transfer_erc20_to_user"
    description = """
        Useful when you want to transfer an ERC20 token to a user for a given amount.
        The address of the contract and amount should be given
        returns the transaction hash.
        """
    args_schema: Type[BaseModel] = TransferERC20ToUserInput

    def _run(self, contract_address: str, user_address: str, amount: int):
        res = transfer_erc20_to_user(contract_address, user_address, amount)
        return res

    def _arun(self, account_address: str):
        raise NotImplementedError("transfer_erc20 does not support async")


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
    # reinitialize agent everytime a query is made
    llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)
    tools = [
        GetAccountBalanceTool(),
        GenerateInkPolkadotContractTool(),
        SendSubstrateBalanceTool(),
        ListAllTransactionsTool(),
        GetTransferDetailsTool(),
        GetERC20TotalSupplyTool(),
        GetERC20OfUserTool(),
        TransferERC20ToUserTool()
    ]
    agent = initialize_agent(tools,
                             llm,
                             agent=AgentType.OPENAI_FUNCTIONS,
                             verbose=True)

    model = ChatOpenAI(
        model_name="gpt-3.5-turbo-16k")  # 'ada' 'gpt-3.5-turbo' 'gpt-4',
    qa = ConversationalRetrievalChain.from_llm(model, retriever=retriever)

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
    mnemonic = data['mnenonic']
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
