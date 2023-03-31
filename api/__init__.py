import json
import aiohttp
from config import cmc_key
from helper.tokenPair import TokenPair

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
        headers = {
            'Accepts': 'application/json',
            'Accept-Encoding': 'deflate, gzip',
            'X-CMC_PRO_API_KEY': cmc_key
        }
        coinmarketcap_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?address="+token
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(coinmarketcap_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                return result_array['data']
    except:
        return None