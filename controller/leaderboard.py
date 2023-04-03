from operator import attrgetter
from datetime import datetime, timedelta
from sqlalchemy import desc
from config import Session
from model.tables import Project, Pair
from helper.shill import Shill
from helper import (
    format_number_string,
    current_marketcap,
    return_percent,
    get_token_pairs,
    dex_coin_array
)
from api import cryptocurrency_info_ids
import asyncio
from helper.emoji import emojis

db = Session()
user_shills_status = []

async def update_token():
    black_list=[] #user list for block from group
    all_pairs = db.query(Pair).all()
    dex_coin_results = dex_coin_array(all_pairs)
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
        liquidities = [single_dex for single_dex in dex_results if single_dex.base_token.address.lower() == pair.token.lower()]
        market_info = [single_cap for single_cap in marketcap_results if single_cap['id'] == pair.coin_market_id]

        if len(liquidities)>0:
            liquidity = max(liquidities, key=attrgetter('liquidity.usd'))
            circulating_supply = None
            now_marketcap = liquidity.fdv
            if len(market_info)>0:
                circulating_supply = market_info[0]['self_reported_circulating_supply']
            
            if circulating_supply != None:
                now_marketcap = circulating_supply*liquidity.price_usd
            
            pair.marketcap = str(now_marketcap)
            pair.updated_at = datetime.now()
            db.commit()
        else:
            # Get User list to kick from Group
            past_thirty_min = datetime.utcnow() - timedelta(minutes=30)
            projects = db.query(Project).filter(Project.token == pair.token).filter(Project.created_at >= past_thirty_min).all()
            black_list = []
            if projects != None:
                for project in projects:
                    black_list.append(project.user_id)
                    db.delete(project)
                    db.commit()
            db.delete(pair)
            db.commit()
    
    return black_list

def all_time():
    global user_shills_status
    all_shills = db.query(Project).order_by(desc(Project.created_at)).all()
    user_lists = []
    result_text = "TOP 10 SHILLS OF ALL TIME\n\n"
    for project in all_shills:
        if not project.username in user_lists:
            user_lists.append(project.username)
        
        current_info = db.query(Pair).filter(Pair.token == project.token).first()
        
        if current_info != None:
            if float(current_info.marketcap)>float(project.ath_value):
                project.ath_value = current_info.marketcap
                db.commit()

            shill_detail = {
                "username": project.username,
                "token": project.token,
                "url": project.url,
                "symbol": project.token_symbol,
                "marketcap": str(project.marketcap),
                "ath": str(project.ath_value),
                "created_at": str(project.created_at),
                "current_marketcap": current_info.marketcap,
                "percent": return_percent(current_info.marketcap, project.marketcap)
            }
            user_shills_status.append(shill_detail)

    user_shills_status = [Shill.parse_obj(single_user_shill) for single_user_shill in user_shills_status]
    
    shill_details = []

    for username in user_lists:
        users_shills = [info for info in user_shills_status if info.username == username]
        if len(users_shills)>0:
            total_percent = 0
            shill_count = 0
            for single_shill in users_shills:
                shill_count +=1
                total_percent += float(single_shill.percent)
            
            average_percent =  total_percent/shill_count
            max_shill = max(users_shills, key=attrgetter('percent'))
            user_shill_detail = {
                'username': username,
                'percent': average_percent,
                'example': max_shill
            }
            shill_details.append(user_shill_detail)

    if len(shill_details)>0:
        sorted_shill_details = sorted(shill_details, key=lambda d: d['percent'], reverse=True)
        index = 1
        for result in sorted_shill_details:
            if index <= 10:
                result_text += "#**"+str(index)+"**: @"+result['username']+" Total "+str(round(result['percent'], 2))+"x.\n"
                result_text += emojis['point_right']+" ["+result['example'].symbol+"]("+result['example'].url+") Shared marketcap: $"+format_number_string(result['example'].marketcap)+"\n"
                result_text += emojis['point_right']+" Currently: $"+format_number_string(result['example'].current_marketcap)+" ("+str(round(float(result['example'].percent), 2))+"x)\n"
                if float(result['example'].current_marketcap)<float(result['example'].ath):
                    result_text += emojis['point_right']+" ATH: $"+format_number_string(result['example'].ath)+" ("+return_percent(result['example'].ath, result['example'].marketcap)+"x)\n"
                result_text += "\n"
                index +=1
    return result_text

def past_week(week):
    past_two_week_date = datetime.utcnow() - timedelta(days=week)
    all_shills = db.query(Project).filter(Project.created_at >= past_two_week_date).order_by(desc(Project.created_at)).all()
    past_user_shills_status = []
    user_lists = []
    week_num = week/7
    week_string = "WEEK"
    if week_num == 2:
        week_string = "2 WEEKS"
    result_text = "TOP 10 SHILLERS PAST "+week_string+"\n\n"
    for project in all_shills:
        if not project.username in user_lists:
            user_lists.append(project.username)
        exist_status = [info for info in user_shills_status if info.username == project.username and info.token == project.token]
        if len(exist_status)>0:
            past_user_shills_status.append(exist_status[0])
    
    shill_details = []

    for username in user_lists:
        users_shills = [info for info in past_user_shills_status if info.username == username]
        if len(users_shills)>0:
            total_percent = 0
            shill_count = 0
            for single_shill in users_shills:
                shill_count +=1
                total_percent += float(single_shill.percent)
            
            average_percent =  total_percent/shill_count
            max_shill = max(users_shills, key=attrgetter('percent'))
            user_shill_detail = {
                'username': username,
                'percent': average_percent,
                'example': max_shill
            }
            shill_details.append(user_shill_detail)

    if len(shill_details)>0:
        sorted_shill_details = sorted(shill_details, key=lambda d: d['percent'], reverse=True)
        index = 1
        for result in sorted_shill_details:
            result_text += "#"+str(index)+": @"+result['username']+" Total "+str(round(result['percent'], 2))+"x.\n"
            result_text += emojis['point_right']+" ["+result['example'].symbol+"]("+result['example'].url+") Shared marketcap: $"+format_number_string(result['example'].marketcap)+"\n"
            result_text += emojis['point_right']+" Currently: $"+format_number_string(result['example'].current_marketcap)+" ("+str(round(float(result['example'].percent), 2))+"x)\n"
            if float(result['example'].current_marketcap)<float(result['example'].ath):
                result_text += emojis['point_right']+" ATH: $"+format_number_string(result['example'].ath)+" ("+return_percent(result['example'].ath, result['example'].marketcap)+"x)\n"
            result_text += "\n"
            index +=1

    return result_text

def global_reset():
    global user_shills_status
    user_shills_status = []
    print("reset first: ", user_shills_status)
    return "reset"