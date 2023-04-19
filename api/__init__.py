import os
import json
import aiohttp
from web3 import Web3
from config import cmc_key, chains, ROOT_PATH, rpc_urls, contract_abi, honeypot_abi, honey_check_contracts
from helper.tokenPair import TokenPair

headers = {
        'Accepts': 'application/json',
        'Accept-Encoding': 'deflate, gzip',
        'X-CMC_PRO_API_KEY': cmc_key
    }

tenderly_header = {
    'X-Access-Key': "vIaXKRwszFi8vNLOrXOqf6YDgH052LGP",
}

async def get_token_pairs(token):
    try:
        dex_url = "https://api.dexscreener.io/latest/dex/tokens/"+token
        async with aiohttp.ClientSession() as session:
            async with session.get(dex_url) as response:
                result = await response.text()
                result_array = json.loads(result)

                return [TokenPair.parse_obj(pair) for pair in result_array["pairs"]]
    except:
        return []

async def cryptocurrency_info(token):
    try:
        coinmarketcap_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?address="+token
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(coinmarketcap_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                return result_array['data']
    except:
        return None
    
async def cryptocurrency_info_ids(ids):
    try:
        ids = str(ids).replace("[", "").replace("]", "").replace(" ", "")
        coinmarketcap_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?id="+ids
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(coinmarketcap_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                return result_array['data']
    except:
        return None

async def go_plus_token_info(token, chain):
    try:
        chain_id = chains[chain]
        go_plus_url = "https://api.gopluslabs.io/api/v1/token_security/"+str(chain_id)+"?contract_addresses="+token
        async with aiohttp.ClientSession() as session:
            async with session.get(go_plus_url) as response:
                data = await response.text()
                data_array = json.loads(data)
                lower_token = token.lower()

                return data_array['result'][lower_token]
    except:
        return None

def get_token_holder_api(token, chain):
    rpc_url = rpc_urls[chain]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = Web3.to_checksum_address(token)
    contract = web3.eth.contract(address=token_address, abi=contract_abi)
    block_number = web3.eth.get_block_number()
    checked_transactions = []
    wallet_addresses = []
    final_wallet = None
    while True:
        from_block = int(block_number) - 5000
        filter = web3.eth.filter({"fromBlock": from_block, "toBlock": block_number, "address": token_address})
        for single_filter in filter.get_all_entries():
            if single_filter['transactionHash'] != None:
                transaction_hash = single_filter['transactionHash'].hex()
                if not transaction_hash in checked_transactions:
                    transaction = web3.eth.get_transaction(transaction_hash)
                    checked_transactions.append(transaction_hash)
                    if transaction != None:
                        if str(transaction['to']).lower() == token.lower():
                            if not transaction['from'] in wallet_addresses:
                                balance = contract.functions.balanceOf(transaction['from']).call()
                                if int(balance) > 1:
                                    final_wallet = transaction['from']
                                    break
                        elif str(transaction['from']).lower() == token.lower():
                            if not transaction['to'] in wallet_addresses:
                                balance = contract.functions.balanceOf(transaction['to']).call()
                                if int(balance) > 1:
                                    final_wallet = transaction['to']
                                    break
        
        if final_wallet != None:
            break
        else:
            block_number = block_number - 5000


    print(final_wallet)

    return final_wallet

def get_token_balance_of_api(token, chain, address):
    rpc_url = rpc_urls[chain]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = Web3.to_checksum_address(token)
    contract = web3.eth.contract(address=token_address, abi=contract_abi)
    balance = contract.functions.balanceOf(address).call()

    return int(balance)

async def run_hoeny_check_api(pair, token):
    target_token_address = Web3.to_checksum_address(token)
    from_address = Web3.to_checksum_address("0x94Db7Eb4f72A756d53cEAF244DEebDdAf78c92CE")
    router_address = Web3.to_checksum_address("0x10ED43C718714eb63d5aA57B78B54704E256024E")
    honey_contract_address = Web3.to_checksum_address("0x2d36BB090231DD6F327D6B4a7c08E5bED0030B3e")
    rpc_url = rpc_urls[pair.chain_id]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = web3.eth.contract(address=honey_contract_address, abi=honeypot_abi)
    buy_path = []
    if pair.quote_token.symbol == "WBNB":
        buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
        buy_path.append(target_token_address)
    else:
        buy_path.append(Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"))
        buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
        buy_path.append(target_token_address)
    
    # sell_path = buy_path.reverse()
    sell_path = list(reversed(buy_path))
    print("buy path: ", buy_path)
    print("sell path: ", sell_path)
    response = contract.functions.honeyCheck(target_token_address, buy_path, sell_path, router_address).call({'from': from_address, 'value': 5000000000000000})

    print(response)
    


async def run_hoeny_tenderly_check_api(from_address, chain, token, router):
    target_token_address = Web3.to_checksum_address(token)
    pair_address = Web3.to_checksum_address(router)
    rpc_url = rpc_urls[chain]
    chain_id = chains[chain]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = web3.eth.contract(address=target_token_address, abi=contract_abi)
    data = contract.encodeABI(fn_name="honeyCheck", args=[target_token_address, pair_address])

    params = {
        "save": False,
        "save_if_fails": False,
        "simulation_type": 'full',
        "network_id": chain_id,
        "from": from_address,
        "to": target_token_address,
        "input": data,
        "gas": 8000000,
        "gas_price": 0,
        "value": 0,
    }

    dex_url = "https://api.tenderly.co/api/v1/account/webstarlee/project/shillmaster/simulate"
    async with aiohttp.ClientSession(headers=tenderly_header) as session:
        async with session.post(dex_url, data=params) as response:
            result = await response.text()
            result_array = json.loads(result)

            print(result_array)

    print(data)