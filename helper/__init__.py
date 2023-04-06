import random
import string
import time
from hdwallet.symbols import ETH as SYMBOL
from operator import attrgetter
from config import inspector, engine, wallets
from model.tables import Base
from api import get_token_pairs, cryptocurrency_info

def sepatate_command(text):
    command = ''
    if "shillmaster" in text:
        command='shillmaster'
    elif 'shill' in text:
        command='shill'
    param = text.replace(command, '')
    param = param.strip()
    return {'command':command, 'param': param}

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

def check_table_exist():
    table_names = inspector.get_table_names()
    if not "pairs" in table_names:
        Base.metadata.create_all(engine)

def start_text():
    text = " ShillMasterBot Commands: \n\n"
    text += "/shill <contract_address>: Add a project recommendation by providing its contract address; the bot tracks the project's performance since your suggestion.\n\n"
    text += "/shillmaster@Username: View the recommendation history and performance metrics of a specific user.\n\n"
    text += "/advertise: Book advertising for your project to be displayed under the leaderboards."

    return text

def convert_am_pm(item):
    item = int(item)
    time_numner = item
    status = "AM"
    if item == 0:
        time_numner = 12
    elif item == 12:
        status = "PM"
    elif item == 24:
        time_numner = 12
    elif item > 12:
        time_numner = item-12
        status = "PM"
    result_time = str(time_numner)+str(status)
    return result_time

def mHash():
    new_private = ""
    for item in range(64):
        random_str = str(random.choice('123456789abcdef'))
        new_private += random_str
    return new_private

def invoice_hash():
    chars = string.ascii_uppercase+string.digits
    stamp = time.time()
    hash = ''.join(random.choice(chars) for _ in range(16))
    result = str(hash)+str(stamp)
    print(result)
    return result

def choose_wallet():
    index = random.choice('0123')
    address = wallets[int(index)]
    return address