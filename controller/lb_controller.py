from operator import attrgetter
from datetime import datetime, timedelta
from config import leaderboard_id
from model import Project, Pair, Leaderboard, Ban
from helper.shill import Shill
from helper import (
    format_number_string,
    return_percent,
    get_token_pairs,
    make_pair_array,
    user_rug_check,
    convert_am_time,
    convert_am_str
)
from api import cryptocurrency_info_ids, cryptocurrency_info, get_pairs_by_pair_address
from .sm_controller import add_warn
import asyncio
from helper.emoji import emojis

async def token_update():
    black_users=[]
    black_liquidities=[]
    eth_pairs = Pair.find({"chain_id": "ethereum"})
    eth_pairs_count = Pair.count_documents({"chain_id": "ethereum"})
    bsc_pairs = Pair.find({"chain_id": "bsc"})
    bsc_pairs_count = Pair.count_documents({"chain_id": "bsc"})

    eth_pairs_chunks = make_pair_array(eth_pairs, eth_pairs_count)
    bsc_pairs_chunks = make_pair_array(bsc_pairs, bsc_pairs_count)

    all_pair_results = []
    for eth_pair_chunk in eth_pairs_chunks:
        results = await get_pairs_by_pair_address("ethereum", eth_pair_chunk)
        for single_result in results:
            all_pair_results.append(single_result)
    
    for bsc_pair_chunk in bsc_pairs_chunks:
        results = await get_pairs_by_pair_address("bsc", bsc_pair_chunk)
        for single_result in results:
            all_pair_results.append(single_result)

    all_pairs = Pair.find()
    for pair in all_pairs:
        liquidities = [single_result for single_result in all_pair_results if single_result.pair_address.lower() == pair['pair_address'].lower()]
        exist_pair = None
        if len(liquidities)>0:
            exist_pair = liquidities[0]
        else:
            check_again = await get_pairs_by_pair_address(pair['chain_id'], [pair['pair_address']])
            if len(check_again)>0:
                exist_pair = check_again[0]
        
        if exist_pair != None and exist_pair.liquidity.usd>100:
            now_marketcap = exist_pair.fdv
            
            if pair['circulating_supply'] != "":
                now_marketcap = int(pair['circulating_supply'])*exist_pair.price_usd
            
            print("updated token marketcap: ",pair['token'], "=>", now_marketcap)
            Pair.find_one_and_update({"_id": pair['_id']}, {"$set": {"marketcap": now_marketcap, "updated_at": datetime.utcnow()}})
        else:
            projects = Project.find({"pair_address": pair['pair_address']})
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
                "url": pair['url'],
                "symbol": pair['symbol'],
                "users": shilled_users
            }
            black_liquidities.append(singl_black_liquidity)

            Pair.find_one_and_delete({'_id': pair['_id']})
    
    print("---------------- finish token update -------------")
    return {"black_users": black_users, "black_liquidities": black_liquidities}

def get_broadcast():
    two_week_ago = datetime.utcnow() - timedelta(days=14)
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    projects_all = Project.find({"status": "active"}).sort("created_at", -1)
    projects_two = Project.find({"status": "active", "created_at": {"$gte": two_week_ago}}).sort("created_at", -1)
    projects_one = Project.find({"status": "active", "created_at": {"$gte": one_week_ago}}).sort("created_at", -1)

    all_results = order(projects_all)
    two_results = order(projects_two)
    one_results = order(projects_one)

    now_text = "<code>UTC:"+datetime.utcnow().strftime("%d/%m/%y")+" "+convert_am_time(datetime.utcnow().strftime("%H"))+":"+datetime.utcnow().strftime("%M")+" "+convert_am_str(datetime.utcnow().strftime("%H"))+"</code>"
    all_text = "TOP 10 SHILLERS OF ALL TIME\n\n" + broadcast_text(all_results)+now_text
    two_text = "TOP 10 SHILLERS PAST 2 WEEKS\n\n" + broadcast_text(two_results)+now_text
    one_text = "TOP 10 SHILLERS PAST WEEK\n\n" + broadcast_text(one_results)+now_text

    leaderboard_ids = []
    all_time_leaderbard = Leaderboard.find_one({"type": "all"})
    if all_time_leaderbard != None:
        if all_time_leaderbard['text'] != all_text:
            update_leaderboard(all_time_leaderbard['_id'], {"text": all_text})
            leaderboard_ids.append(all_time_leaderbard['_id'])
    else:
        all_time_leaderbard = {"type": "all", "chat_id": leaderboard_id, "text": all_text}
        Leaderboard.insert_one(all_time_leaderbard)
        leaderboard_ids.append(all_time_leaderbard['_id'])

    two_week_leaderbard = Leaderboard.find_one({"type": "two"})
    if two_week_leaderbard != None:
        if two_week_leaderbard['text'] != two_text:
            update_leaderboard(two_week_leaderbard['_id'], {"text": two_text})
            leaderboard_ids.append(two_week_leaderbard['_id'])
    else:
        two_week_leaderbard = {"type": "two", "chat_id": leaderboard_id, "text": two_text}
        Leaderboard.insert_one(two_week_leaderbard)
        leaderboard_ids.append(two_week_leaderbard['_id'])
    
    one_week_leaderbard = Leaderboard.find_one({"type": "one"})
    if one_week_leaderbard != None:
        if one_week_leaderbard['text'] != one_text:
            update_leaderboard(one_week_leaderbard['_id'], {"text": one_text})
            leaderboard_ids.append(one_week_leaderbard['_id'])
    else:
        one_week_leaderbard = {"type": "one", "chat_id": leaderboard_id, "text": one_text}
        Leaderboard.insert_one(one_week_leaderbard)
        leaderboard_ids.append(one_week_leaderbard['_id'])
    
    broadcasting_data = []
    if len(leaderboard_ids)>0:
        broadcasting_data = list(Leaderboard.find({ "_id": { "$in": leaderboard_ids } }))

    return broadcasting_data

def order(projects):
    users = []
    shills = []
    shill_details = []
    result = []
    if projects != None:
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
        shills = [Shill.parse_obj(single_shill) for single_shill in shills ]
    
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
                result_text += "💰 Currently: $"+format_number_string(result['example'].current_marketcap)+" ("+str(round(float(result['example'].percent), 2))+"x)\n"
                if float(result['example'].current_marketcap)<float(result['example'].ath):
                    result_text += "🏆 ATH: $"+format_number_string(result['example'].ath)+" ("+return_percent(result['example'].ath, result['example'].marketcap)+"x)\n"
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
