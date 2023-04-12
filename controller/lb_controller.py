from operator import attrgetter
from datetime import datetime, timedelta
from config import leaderboard_id
from model import Project, Pair, Leaderboard, Ban
from helper.shill import Shill
from helper import (
    format_number_string,
    return_percent,
    get_token_pairs,
    dex_coin_array,
    user_rug_check
)
from api import cryptocurrency_info_ids
from .sm_controller import add_warn
import asyncio
from helper.emoji import emojis

async def token_update():
    black_users=[]
    black_liquidities=[]
    all_pairs = Pair.find()
    count = Pair.count_documents({})
    dex_coin_results = dex_coin_array(all_pairs, count)
    dex_array = dex_coin_results['dex_array']
    coin_array = dex_coin_results['coin_array']

    dex_results = []
    marketcap_results = []

    for token_list in dex_array:
        list_result = await get_token_pairs(token_list)
        dex_results += list_result

    for coin_market_id in coin_array:
        cap_result = await cryptocurrency_info_ids(coin_market_id)
        if cap_result != None:
            for single_key in cap_result:
                marketcap_results.append(cap_result[single_key])

    for pair in all_pairs:
        liquidities = [single_dex for single_dex in dex_results if single_dex.base_token.address.lower() == pair['token'].lower()]
        market_info = [single_cap for single_cap in marketcap_results if single_cap['id'] == pair['coin_market_id']]
        final_pair = None
        if len(liquidities)>0:
            final_pair = max(liquidities, key=attrgetter('liquidity.usd'))
        
        if final_pair != None and final_pair.liquidity.usd>100:
            circulating_supply = None
            now_marketcap = final_pair.fdv
            if len(market_info)>0:
                circulating_supply = market_info[0]['self_reported_circulating_supply']
            
            if circulating_supply != None:
                now_marketcap = circulating_supply*final_pair.price_usd
            
            Pair.find_one_and_update({"_id": pair['_id']}, {"$set": {"marketcap": now_marketcap, "updated_at": datetime.utcnow()}})
        else:
            projects = Project.find({"token": pair['token']})
            shilled_users = []
            if projects != None:
                for project in projects:
                    shilled_users.append(project['username'])
                    is_warn = user_rug_check(project, 'removed')
                    if is_warn:
                        warn_user = add_warn(project['username'], project['user_id'], project['chat_id'])
                        if warn_user['count'] > 1:
                            black_users.append(warn_user)
            
            singl_black_liquidity = {
                "token": pair['token'],
                "url": pair['pair_url'],
                "symbol": pair['symbol'],
                "users": shilled_users
            }
            black_liquidities.append(singl_black_liquidity)
            Pair.find_one_and_delete({'_id': pair['_id']})
    
    return {"black_users": black_users, "black_liquidities": black_liquidities }

def get_broadcast():
    two_week_ago = datetime.utcnow() - timedelta(days=14)
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    projects_all = Project.find({"status": "active"}).sort("created_at", -1)
    projects_two = Project.find({"status": "active", "created_at": {"$gte": two_week_ago}}).sort("created_at", -1)
    projects_one = Project.find({"status": "active", "created_at": {"$gte": one_week_ago}}).sort("created_at", -1)

    all_results = order(projects_all)
    two_results = order(projects_two)
    one_results = order(projects_one)

    all_text = "TOP 10 SHILLERS OF ALL TIME\n\n" + broadcast_text(all_results)
    two_text = "TOP 10 SHILLERS PAST 2 WEEKS\n\n" + broadcast_text(two_results)
    one_text = "TOP 10 SHILLERS PAST WEEK\n\n" + broadcast_text(one_results)

    leaderboard_dbs = []
    all_time_leaderbard = Leaderboard.find_one({"type": "all"})
    if all_time_leaderbard != None:
        if all_time_leaderbard['text'] != all_text:
            update_leaderboard(all_time_leaderbard['_id'], {"text": all_text})
    else:
        all_time_leaderbard = {"type": "all", "chat_id": leaderboard_id, "text": all_text}
        leaderboard_dbs.append(all_time_leaderbard)

    two_week_leaderbard = Leaderboard.find_one({"type": "two"})
    if two_week_leaderbard != None:
        if two_week_leaderbard['text'] != two_text:
            update_leaderboard(two_week_leaderbard['_id'], {"text": two_text})
    else:
        two_week_leaderbard = {"type": "two", "chat_id": leaderboard_id, "text": two_text}
        leaderboard_dbs.append(two_week_leaderbard)
    
    one_week_leaderbard = Leaderboard.find_one({"type": "one"})
    if one_week_leaderbard != None:
        if one_week_leaderbard['text'] != one_text:
            update_leaderboard(one_week_leaderbard['_id'], {"text": one_text})
    else:
        one_week_leaderbard = {"type": "one", "chat_id": leaderboard_id, "text": one_text}
        leaderboard_dbs.append(one_week_leaderbard)

    if len(leaderboard_dbs) > 0:
        Leaderboard.insert_many(leaderboard_dbs)

    broadcasting_data = Leaderboard.find()

    return broadcasting_data

def order(projects):
    users = []
    shills = []
    shill_details = []
    result = []
    for project in projects:
        if not project['username'] in users:
            users.append(project['username'])

        information = Pair.find_one({"token": project['token']})
        
        if information != None:
            if float(information['marketcap'])>float(project['ath_value']):
                Project.find_one_and_update({"_id": project['_id']}, {"$set": {"ath_value": information['marketcap']}})

            user_shill = {
                "username": project['username'],
                "token": project['token'],
                "url": project['url'],
                "symbol": project['token_symbol'],
                "marketcap": str(project['marketcap']),
                "ath": str(project['ath_value']),
                "created_at": str(project['created_at']),
                "current_marketcap": information['marketcap'],
                "percent": return_percent(information['marketcap'], project['marketcap'])
            }
            shills.append(user_shill)
    
    if len(shills)>0:
        shills = [Shill.parse_obj(single_shill) for single_shill in shills]
    
    for username in users:
        user_shills = [shill for shill in shills if shill.username == username]
        if len(user_shills)>0:
            total_percent = 0
            total_count = 0
            for single_shill in user_shills:
                total_count +=1
                total_percent += float(single_shill.percent)
            
            average_percent =  total_percent/total_count
            max_shill = max(user_shills, key=attrgetter('percent'))
            user_shill_detail = {
                'username': username,
                'percent': average_percent,
                'example': max_shill
            }
            shill_details.append(user_shill_detail)
    
    if len(shill_details)>0:
        result = sorted(shill_details, key=lambda d: d['percent'], reverse=True)
    
    return result

def broadcast_text(results):
    result_text=""
    if len(results)>0:
        index = 1
        for result in results:
            if index <= 10:
                result_text += "#"+str(index)+": @"+result['username']+" Total "+str(round(result['percent'], 2))+"x.\n"
                result_text += emojis['point_right']+" <a href='"+result['example'].url+"'>"+result['example'].symbol+"</a> Shared marketcap: $"+format_number_string(result['example'].marketcap)+"\n"
                result_text += emojis['point_right']+" Currently: $"+format_number_string(result['example'].current_marketcap)+" ("+str(round(float(result['example'].percent), 2))+"x)\n"
                if float(result['example'].current_marketcap)<float(result['example'].ath):
                    result_text += emojis['point_right']+" ATH: $"+format_number_string(result['example'].ath)+" ("+return_percent(result['example'].ath, result['example'].marketcap)+"x)\n"
                result_text += "\n"
                index +=1

    return result_text

def get_baned_user(username):
    return Ban.find_one({'username': username})

def add_ban_user(user):
    ban_user = Ban.find_one({"username": user['username']})
    if ban_user == None:
        ban_user = {
            "username": user['username'],
            "user_id": user['user_id'],
            "chat_id": user['chat_id'],
        }
        Ban.insert_one(ban_user)

def remove_ban_user(user):
    Ban.find_one_and_delete({'username': user['username']})

def update_leaderboard(id, param):
    Leaderboard.find_one_and_update({"_id": id}, {"$set": param})
