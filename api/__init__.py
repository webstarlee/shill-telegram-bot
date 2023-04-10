import json
import aiohttp
from config import cmc_key, chains
from helper.tokenPair import TokenPair
headers = {
        'Accepts': 'application/json',
        'Accept-Encoding': 'deflate, gzip',
        'X-CMC_PRO_API_KEY': cmc_key
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
        return []