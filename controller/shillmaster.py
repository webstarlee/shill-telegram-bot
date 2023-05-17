import logging
from operator import attrgetter
from datetime import datetime
from models import Project, Pair, Leaderboard, Warn
from apis import get_token_pairs, cryptocurrency_info, hoeny_check_api
from config import dex_ids
from helpers import (
    format_number_string,
    get_percent,
    user_rug_check,
    add_warn
)

async def user_shillmaster(user_id, username, chat_id, token):
    try:
        pairs = await get_token_pairs(token)
        filtered_pairs = []
        if len(pairs) > 0:
            filtered_pairs = [pair for pair in pairs if pair.base_token.address.lower() == token.lower()]

        chain_filters = []
        if len(filtered_pairs) > 0:
            for filtered_pair in filtered_pairs:
                if filtered_pair.chain_id == "ethereum" or filtered_pair.chain_id == "bsc":
                    chain_filters.append(filtered_pair)

        if len(chain_filters)==0:
            return {"is_rug": True, "reason": "chain"}
        
        dex_filters = []
        if len(chain_filters) > 0:
            for chain_filtered_pair in chain_filters:
                if chain_filtered_pair.dex_id in dex_ids:
                    if chain_filtered_pair.labels != None and ("v3" in chain_filtered_pair.labels or "V3" in chain_filtered_pair.labels):
                        print("V3")
                    else:
                        dex_filters.append(chain_filtered_pair)
        
        if len(dex_filters)==0:
            return {"is_rug": True, "reason": "dex"}

        final_filtered_pairs = []
        if len(dex_filters) > 0:
            for filtered_pair in dex_filters:
                if filtered_pair.liquidity != None and (filtered_pair.chain_id == "ethereum" or filtered_pair.chain_id == "bsc"):
                    final_filtered_pairs.append(filtered_pair)
                    
        pair = None
        if len(final_filtered_pairs)>0:
            pair = max(final_filtered_pairs, key=attrgetter('liquidity.usd'))

        if pair == None:
            return {"is_rug": True, "reason": "liquidity", "text": "There is no Liquidity for this Token"}
        
        if int(pair.liquidity.usd) < 100:
            text = "There is no Liquidity for "+pair.base_token.symbol+" Token"
            return {"is_rug": True, "reason": "liquidity", "text": text}

        honey_result = await hoeny_check_api(token, pair)

        if honey_result['is_honeypot']:
            project = {
                "username": username,
                "user_id":user_id,
                "chat_id": chat_id,
                "chain_id": pair.chain_id,
                "pair_address": pair.pair_address,
                "url":pair.url,
                "token":token,
                "token_symbol":pair.base_token.symbol,
                "marketcap":"0",
                "ath_value":"0",
                "status":"honeypot",
                "created_at": datetime.utcnow()
            }
            Project.insert_one(project)
            text = pair.base_token.symbol+" Token look like honeypot"
            return {"is_rug": True, "reason": "honeypot", "text": text}

        bot_txt = ''
        is_new = True
        # marketcap_info = await cryptocurrency_info(token)
        # circulating_supply = 0
        marketcap = pair.fdv
        # coin_marketcap_id = None
        # if marketcap_info != None:
        #     for key in marketcap_info:
        #         currency_info = marketcap_info[key]
        #         coin_marketcap_id=currency_info['id']
        #         if currency_info['self_reported_circulating_supply'] != None:
        #             circulating_supply = currency_info['self_reported_circulating_supply']

        # if circulating_supply != 0:
        #     marketcap = circulating_supply*pair.price_usd

        pair_project = Project.find_one({"username": username, "pair_address": pair.pair_address})
        pair_token = Pair.find_one({"pair_address": pair.pair_address})
        if pair_token != None:
            Pair.update_one({"_id": pair_token['_id']},{"$set":{"marketcap": marketcap}})
        else:
            pair_token = {
                "token":token,
                "symbol":pair.base_token.symbol,
                "chain_id": pair.chain_id,
                "pair_address": pair.pair_address,
                "url":pair.url,
                "marketcap":str(marketcap),
                "coin_market_id": "",
                "circulating_supply": "",
                "status": "active",
                "updated_at": datetime.utcnow()
            }
            Pair.insert_one(pair_token)

        if pair_project != None:
            is_new = False
            if float(marketcap)>float(pair_project['ath_value']):
                Project.update_one({"_id": pair_project['_id']},{"$set":{"ath_value": marketcap}})
            marketcap_percent = marketcap/float(pair_project['marketcap'])
            bot_txt = f"💰 <a href='{pair.url}' >{pair_project['token_symbol']}</a> Already Shared marketcap: ${format_number_string(pair_project['marketcap'])}\n"
            bot_txt += f"👉 Currently: ${format_number_string(marketcap)} ({str(round(marketcap_percent, 2))}x)\n"
            if float(marketcap)< float(pair_project['ath_value']):
                bot_txt += f"🏆 ATH: ${format_number_string(pair_project['ath_value'])} ({get_percent(pair_project['ath_value'], pair_project['marketcap'])}x)\n"
            bot_txt += "\n"
        else:
            project = {
                "username": username,
                "user_id": user_id,
                "chat_id": chat_id,
                "chain_id": pair.chain_id,
                "pair_address": pair.pair_address,
                "url": pair.url,
                "token": token,
                "token_symbol": pair.base_token.symbol,
                "marketcap": marketcap,
                "ath_value": marketcap,
                "status": "active",
                "created_at": datetime.utcnow()
            }
            Project.insert_one(project)
            bot_txt = f"🎉 @{username} shilled\n"
            bot_txt += f"👉 <code>{token}</code>\n💰 <a href='{pair.url}' >{pair.base_token.symbol}</a>- Current marketcap: ${format_number_string(marketcap)}"

        return {"is_rug": False, "text": bot_txt, "is_new": is_new}

    except:

        text="There is no liquidity for this token"
        return {"is_rug": True, "reason": "liquidity", "text": text}

def token_shillmaster(token):
    pair = Pair.find_one({"token": token})
    if pair != None:
        project_cursor = Project.find({"token": token})
        projects = list(project_cursor)
        user_list = []
        for project in projects:
            if not project['username'] in user_list:
                user_list.append(project['username'])
        
        return {"user_list": user_list, "marketcap": pair['marketcap'] }
    return None

async def get_user_shillmaster(user):
    return_txt = "❗ There is not any shill yet for @"+user
    username = user.replace("@", "")
    project_cursor = Project.find({"username": {'$regex' : f'^{username}$', '$options' : 'i'}}).sort("created_at", -1).limit(5)
    projects = list(project_cursor)
    if len(projects) > 0:
        return_txt = "📊 Shillmaster stats for @"+user+" 📊\n\n"
        index = 1
        for project in projects:
            pair = Pair.find_one({"pair_address": project['pair_address']})
            if pair != None:
                if index > 1:
                        return_txt  += "=======================\n"
                if project['status'] == "active":
                    return_txt += "💰 <a href='"+project['url']+"' >"+project['token_symbol']+"</a> Shared marketcap: $"+format_number_string(project['marketcap'])+"\n"
                    return_txt += f"👉 Currently: ${format_number_string(pair['marketcap'])} ({get_percent(pair['marketcap'], project['marketcap'])}x)\n"
                    if float(pair['marketcap'])< float(project['ath_value']):
                        return_txt += f"🏆 ATH: ${format_number_string(project['ath_value'])} ({get_percent(project['ath_value'], project['marketcap'])}x)\n"
                
                if project['status'] == "removed":
                    return_txt += f"💰 <a href='{project['url']}' >{project['token_symbol']}</a> Shared marketcap: ${format_number_string(project['marketcap'])}\n"
                    return_txt += "⚠️ Currently: Liquidity removed\n"
                
                if project['status'] == "no_liquidity":
                    return_txt += f"💰 <a href='{project['url']}' >{project['token_symbol']}</a> has no Liquidity\n"
                    return_txt += "⚠️ Got Warn with this token\n"
                
                if project['status'] == "honeypot":
                    return_txt += f"💰 <a href='{project['url']}' >{project['token_symbol']}</a> look like Honeypot\n"
                    return_txt += "⚠️ Got Warn with this token\n"
            
            index += 1

    return return_txt

async def current_status(project):
    try:
        pair = Pair.find_one({"pair_address": project['pair_address']})

        if pair == None:
            is_warn = user_rug_check(project, 'removed')
            return {"is_liquidity": False, "is_warn": is_warn}
        
        if pair['status'] <= 100:
            is_warn = user_rug_check(project, 'removed')
            return {"is_liquidity": False, "is_warn": is_warn}
        
        marketcap_info = await cryptocurrency_info(project['token'])
        circulating_supply = 0
        marketcap = pair.fdv
        if marketcap_info != None:
            for key in marketcap_info:
                currency_info = marketcap_info[key]
                if currency_info['self_reported_circulating_supply'] != None:
                    circulating_supply = currency_info['self_reported_circulating_supply']
        if circulating_supply != 0:
            marketcap = circulating_supply*pair.price_usd

        print(project['token'], ": ",circulating_supply)
        marketcap_percent = marketcap/float(project['marketcap'])
        return {"is_liquidity": True, "marketcap": marketcap, "percent": marketcap_percent}
    except:
        return {"is_liquidity":False, "is_warn": False}