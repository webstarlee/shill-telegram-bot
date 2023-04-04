from operator import attrgetter
from datetime import datetime, timedelta
from sqlalchemy import desc
from config import Session, leaderboard_id
from model.tables import Project, Pair, Leaderboard
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

async def token_update():
    black_list=[]
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
            if projects != None:
                for project in projects:
                    black_list.append({"user_id": project.user_id, "group_id": project.chat_id})
                    db.delete(project)
                    db.commit()
            db.delete(pair)
            db.commit()
    
    return black_list

def broadcast():
    two_week_ago = datetime.utcnow() - timedelta(days=14)
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    projects_all = db.query(Project).order_by(desc(Project.created_at)).all()
    projects_two = db.query(Project).filter(Project.created_at >= two_week_ago).order_by(desc(Project.created_at)).all()
    projects_one = db.query(Project).filter(Project.created_at >= one_week_ago).order_by(desc(Project.created_at)).all()

    all_results = order(projects_all)
    two_results = order(projects_two)
    one_results = order(projects_one)

    all_text = "TOP 10 SHILLERS OF ALL TIME\n\n" + broadcast_text(all_results)
    two_text = "TOP 10 SHILLERS PAST 2 WEEKS\n\n" + broadcast_text(two_results)
    one_text = "TOP 10 SHILLERS PAST WEEK\n\n" + broadcast_text(one_results)

    broadcasting_leaderboards = []
    all_time_leaderbard = db.query(Leaderboard).filter(Leaderboard.type == 'all').first()
    if all_time_leaderbard != None:
        if all_time_leaderbard.text != all_text:
            all_time_leaderbard.text = all_text
            db.commit()
            broadcasting_leaderboards.append(all_time_leaderbard)
    else:
        all_time_leaderbard = Leaderboard(type="all", chat_id=leaderboard_id, text=all_text)
        db.add(all_time_leaderbard)
        db.commit()

        broadcasting_leaderboards.append(all_time_leaderbard)
    
    two_week_leaderbard = db.query(Leaderboard).filter(Leaderboard.type == 'two').first()
    if two_week_leaderbard != None:
        if two_week_leaderbard.text != two_text:
            two_week_leaderbard.text = two_text
            db.commit()
            broadcasting_leaderboards.append(two_week_leaderbard)
    else:
        two_week_leaderbard = Leaderboard(type="two", chat_id=leaderboard_id, text=two_text)
        db.add(two_week_leaderbard)
        db.commit()

        broadcasting_leaderboards.append(two_week_leaderbard)
    

    one_week_leaderbard = db.query(Leaderboard).filter(Leaderboard.type == 'one').first()
    if one_week_leaderbard != None:
        if one_week_leaderbard.text != one_text:
            one_week_leaderbard.text = one_text
            db.commit()
            broadcasting_leaderboards.append(one_week_leaderbard)
    else:
        one_week_leaderbard = Leaderboard(type="one", chat_id=leaderboard_id, text=one_text)
        db.add(one_week_leaderbard)
        db.commit()

        broadcasting_leaderboards.append(one_week_leaderbard)

    
    return broadcasting_leaderboards

def order(projects):
    users = []
    shills = []
    shill_details = []
    result = []
    for project in projects:
        if not project.username in users:
            users.append(project.username)
        
        information = db.query(Pair).filter(Pair.token == project.token).first()
        
        if information != None:
            if float(information.marketcap)>float(project.ath_value):
                project.ath_value = information.marketcap
                db.commit()

            user_shill = {
                "username": project.username,
                "token": project.token,
                "url": project.url,
                "symbol": project.token_symbol,
                "marketcap": str(project.marketcap),
                "ath": str(project.ath_value),
                "created_at": str(project.created_at),
                "current_marketcap": information.marketcap,
                "percent": return_percent(information.marketcap, project.marketcap)
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
                result_text += "#**"+str(index)+"**: @"+result['username']+" Total "+str(round(result['percent'], 2))+"x.\n"
                result_text += emojis['point_right']+" ["+result['example'].symbol+"]("+result['example'].url+") Shared marketcap: $"+format_number_string(result['example'].marketcap)+"\n"
                result_text += emojis['point_right']+" Currently: $"+format_number_string(result['example'].current_marketcap)+" ("+str(round(float(result['example'].percent), 2))+"x)\n"
                if float(result['example'].current_marketcap)<float(result['example'].ath):
                    result_text += emojis['point_right']+" ATH: $"+format_number_string(result['example'].ath)+" ("+return_percent(result['example'].ath, result['example'].marketcap)+"x)\n"
                result_text += "\n"
                index +=1

    return result_text