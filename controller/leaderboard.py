from operator import attrgetter
from datetime import datetime, timedelta
from sqlalchemy import desc
from config import Session
from model.tables import Project
from helper.shill import Shill
from helper import (
    format_number_string,
    current_marketcap,
    return_percent
)
import asyncio
import time
from helper.emoji import emojis

db = Session()
user_shills_status = []

emoji_array = {1: "🚀", 2: "✈", 3: "🚁", 4: "🏎", 5: "🚗", 6: "🏍", 7: "🚲", 8: "🏃‍♂️", 9: "🚶‍♂️", 10: "👨‍🦽"}

async def all_time():
    global user_shills_status
    all_shills = db.query(Project).order_by(desc(Project.created_at)).all()
    user_lists = []
    timestamp = time.time()
    updated_time = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M')
    result_text = "TOP 10 SHILLS OF ALL TIME\n\n"
    for project in all_shills:
        if not project.username in user_lists:
            user_lists.append(project.username)
        
        current_info = await current_marketcap(project)
        if float(current_info['marketcap'])>float(project.ath_value):
            project.ath_value = current_info['marketcap']
            db.commit()
        if current_info['is_liquidity']:
            shill_detail = {
                "username": project.username,
                "token": project.token,
                "url": project.url,
                "symbol": project.token_symbol,
                "marketcap": str(project.marketcap),
                "ath": str(project.ath_value),
                "created_at": str(project.created_at),
                "current_marketcap": current_info['marketcap'],
                "percent": current_info['percent']
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
    timestamp = time.time()
    now_time = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
    now_time_strp = datetime.strptime(now_time, "%d/%m/%Y %H:%M:%S")
    past_two_week_date = now_time_strp - timedelta(days=week)
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