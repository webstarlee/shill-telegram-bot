from operator import attrgetter
from api import get_token_pairs, cryptocurrency_info

def format_number_string(number):
    number = float(number)
    final_number = "{:,}".format(int(number))
    return str(final_number)

def return_percent(first, second):
    first = float(first)
    second = float(second)
    percent = first/second
    return str(round(percent, 2))

async def current_marketcap(project):
    try:
        pairs = await get_token_pairs(project.token)
        filtered_pairs = [pair for pair in pairs if pair.base_token.address.lower() == project.token.lower()]
        if len(filtered_pairs)>0:
            pair = max(filtered_pairs, key=attrgetter('liquidity.usd'))
            marketcap_info = await cryptocurrency_info(project.token)
            circulating_supply = 0
            marketcap = pair.fdv
            if marketcap_info != None:
                for key in marketcap_info:
                    currency_info = marketcap_info[key]
                    if currency_info['self_reported_circulating_supply'] != None:
                        circulating_supply = currency_info['self_reported_circulating_supply']
            if circulating_supply != 0:
                marketcap = circulating_supply*pair.price_usd

            marketcap_percent = marketcap/float(project.marketcap)
            return {"is_liquidity": True, "marketcap": marketcap, "percent": marketcap_percent}
        else:
            return {"is_liquidity":False}
    except:
        return {"is_liquidity":False}

def dex_coin_array(pairs):
    dex_part_array = []
    coin_market_ids = []
    dex_part = ''
    coin_market_part = []
    index = 1
    for pair in pairs:
        if dex_part == '':
            dex_part = pair.token
        else:
            dex_part += ","+pair.token

        if pair.coin_market_id != None:
            print(pair.coin_market_id)
            coin_market_part.append(pair.coin_market_id)
        
        if index%20 == 0:
            dex_part_array.append(dex_part)
            dex_part = ''
            coin_market_ids.append(coin_market_part)
            coin_market_part = []
        elif index == len(pairs):
            dex_part_array.append(dex_part)
            dex_part = ''
            coin_market_ids.append(coin_market_part)
            coin_market_part = None
        index+=1
    
    return {"dex_array": dex_part_array, "coin_array": coin_market_ids}