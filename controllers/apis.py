import json
import aiohttp
import logging
import requests
from web3 import Web3
from modules.tokenPair import TokenPair
from config import rpc_urls, honeypot_abi, honey_check_contracts, eth_routers

async def get_pairs_by_token(token):
    try:
        dex_url = "https://api.dexscreener.io/latest/dex/tokens/"+token
        async with aiohttp.ClientSession() as session:
            async with session.get(dex_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                if result_array["pairs"] == None:
                    return []

                return [TokenPair.parse_obj(pair) for pair in result_array["pairs"]]
    except Exception:
        return []

async def get_pairs_by_pair_address(chain, addresses):
    try:
        stringed_addresses = ','.join([str(elem) for elem in addresses])
        dex_url = "https://api.dexscreener.com/latest/dex/pairs/"+chain+"/"+stringed_addresses
        async with aiohttp.ClientSession() as session:
            async with session.get(dex_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                if result_array["pairs"] == None:
                    return []

                return [TokenPair.parse_obj(pair) for pair in result_array["pairs"]]
    except Exception:
        return []

def check_honey_by_contract(token, pair):
    logging.info("honey check start")
    target_token_address = Web3.to_checksum_address(token)
    weth_token = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    if token.lower() == weth_token.lower():
        return {"is_honeypot": False, "reason": "weth"}
    
    from_address = Web3.to_checksum_address("0xE556B7494C8809d66494CD23C48bff02e4391dCB")
    router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    
    if pair.chain_id == "bsc":
        router_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    else:
        router_address = eth_routers[pair.dex_id]

    final_router = Web3.to_checksum_address(router_address)
    honey_contract_address = Web3.to_checksum_address(honey_check_contracts[pair.chain_id])
    rpc_url = rpc_urls[pair.chain_id]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = web3.eth.contract(address=honey_contract_address, abi=honeypot_abi)
    buy_path = []
    if pair.chain_id == "bsc":
        if pair.quote_token.symbol == "WBNB":
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
        else:
            buy_path.append(Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"))
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
    else:
        if pair.quote_token.symbol == "WETH":
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
        else:
            buy_path.append(Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"))
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
    
    sell_path = list(reversed(buy_path))
    
    logging.info(f"buy path: {buy_path}")
    logging.info(f"sell path: {sell_path}")
    
    try:
        response = contract.functions.honeyCheck(target_token_address, buy_path, sell_path, final_router).call({'from': from_address, 'value': 10000000000000000})
        logging.info(response)
        return {"honeypot": False, "reason": "pass"}
    except Exception:
        logging.info("Honeypot !!!!")
        return {"honeypot": True, "reason": "fail"}