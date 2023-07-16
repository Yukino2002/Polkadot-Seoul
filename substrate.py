from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from dotenv import load_dotenv
import os
import requests

load_dotenv()

base_url = "https://rococo.api.subscan.io"
substrate_relay = SubstrateInterface(url="wss://rococo-rpc.polkadot.io")
substrate_contract = SubstrateInterface(
    url='wss://rococo-contracts-rpc.polkadot.io')
api_key = os.getenv("API_KEY")


def format_balance(amount: int):
    amount = format(
        amount / 10**substrate_relay.properties.get('tokenDecimals', 0),
        ".15g")
    return f"{amount} {substrate_relay.properties.get('tokenSymbol', 'UNIT')}"


def get_account_transfers(account_address):
    url = base_url + "/api/scan/transfers"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    payload = {"address": account_address, "row": 100}

    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def get_account_balance(account_address):
    result = substrate_relay.query(
        "System", "Account",
        ["5DvyRvNq5jpvjat2qkGhiKjJQdz5cwreJW5yxvLBLRpHnoGo"])
    balance = (result.value["data"]["free"] + result.value["data"]["reserved"])

    return format_balance(balance)


def get_transfer_details(extrinsic_index):
    url = base_url + "/api/scan/extrinsic"
    headers = {"Content-Type": "application/json", "X-API-Key": api_key}
    payload = {"extrinsic_index": extrinsic_index}

    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def send_balance(recipient_address, amount):
    call = substrate_relay.compose_call(call_module='Balances',
                                        call_function='transfer',
                                        call_params={
                                            'dest': recipient_address,
                                            'value': amount * 10**15
                                        })

    extrinsic = substrate_relay.create_signed_extrinsic(
        call=call,
        keypair=Keypair.create_from_mnemonic(os.getenv("MNEMONIC")),
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


print(get_account_balance("5DvyRvNq5jpvjat2qkGhiKjJQdz5cwreJW5yxvLBLRpHnoGo"))
# print(get_account_transfers("5DvyRvNq5jpvjat2qkGhiKjJQdz5cwreJW5yxvLBLRpHnoGo"))
# print(get_transfer_details("6245445-2"))
# send_balance("5Fe4G8vypjGHPkwwBSF1nbnyX6ZKTMMNVQDhaZJ1u6tafcpF", 0.01)