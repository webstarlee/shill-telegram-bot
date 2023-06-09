import db
import asyncio
import logging
import threading
from config import LEADERBOARD_ID
from datetime import datetime
from helpers.format import get_time_delta, percent, format_price
from .database import db_setting_update, db_pair_marketcap_update
from .apis import get_pairs_by_pair_address

def user_rug_check(pair):
    logging.info("Rug check function working")
    projects = db.Project.find({"pair_address": pair['pair_address']})
    if projects != None:
        for project in projects:
            logging.info(f"Project status to remove for {project['_id']}")
            db.Project.find_one_and_update({"_id": project['_id']}, {"$set": {"status": "removed"}})
            current_time = datetime.utcnow()
            delta = get_time_delta(current_time, project['created_at'])
            if delta <= 30:
                warn_user = db.Warn.find_one({"user_id": project['user_id'], "group_id": project['group_id']})
                if warn_user != None:
                    current_count = warn_user['count']
                    current_count = int(current_count)+1
                    db.Warn.update_one({"_id": warn_user['_id']}, {"$set": {"count": current_count}})
                else:
                    warn_user =  {
                        "user_id": int(project['user_id']),
                        "group_id": int(project['group_id']),
                        "count": 1
                    }
                    db.Warn.insert_one(warn_user)
                    logging.info(f"Insert warnning for {project['user_id']}")

    db.Pair.find_one_and_update({"_id": pair['_id']}, {"$set" : {"status": "removed", "removed_at": datetime.utcnow()}})
    removed_pair = db.RemovedPair.find_one({"pair_address": pair['pair_address']})
    if removed_pair == None:
        removed_pair = {
            "chain": pair['chain'],
            "pair_address": pair['pair_address']
        }
        db.RemovedPair.insert_one(removed_pair)

async def token_update():
    pairs_cursor = db.Pair.find({"status": "active"})
    pairs = list(pairs_cursor)
    index = 0
    for pair in pairs:
        index += 1
        logging.info(f"{index}: Checking: {pair['pair_address']}")
        result = await get_pairs_by_pair_address(pair['chain'], [pair['pair_address']])
        exist_pair = None
        if len(result)>0:
            exist_pair = result[0]

        if exist_pair != None and exist_pair.liquidity != None and exist_pair.liquidity.usd>100:
            now_marketcap = exist_pair.fdv
            logging.info(f"updated token marketcap: {pair['token']} => {now_marketcap}")
            db_insert = threading.Thread(target=db_pair_marketcap_update, args=(exist_pair,))
            db_insert.start()
        else:
            logging.info(f"token Rugged: {pair['chain']} -> {pair['token']}")
            rug_check = threading.Thread(target=user_rug_check, args=(pair,))
            rug_check.start()
        await asyncio.sleep(0.3)
    
    logging.info("Token update Completed")
    return True

def get_broadcasts():
    projects_cursor = db.Project.find({"status": "active"}).sort("created_at", -1)
    projects = list(projects_cursor)

    two_week_projects = []
    one_week_projects = []
    current_time = datetime.utcnow()
    for project in projects:
        delta = get_time_delta(current_time, project['created_at'])
        if delta <= 20160:
            two_week_projects.append(project)
            if delta <= 10080:
                one_week_projects.append(project)
            
    all_results = calculate_order(projects)
    two_results = calculate_order(two_week_projects)
    one_results = calculate_order(one_week_projects)

    db_insert = threading.Thread(target=top_ten_update, args=(all_results,))
    db_insert.start()

    now_text = f"<code>UTC:{datetime.utcnow().strftime('%d/%m/%y')} {str(datetime.utcnow().strftime('%H'))}:{str(datetime.utcnow().strftime('%M'))}</code>"
    all_text = f"TOP 10 SHILLERS OF ALL TIME\n\n{broadcast_text(all_results)}{now_text}"
    two_text = f"TOP 10 SHILLERS PAST 2 WEEKS\n\n{broadcast_text(two_results)}{now_text}"
    one_text = f"TOP 10 SHILLERS PAST WEEK\n\n{broadcast_text(one_results)}{now_text}"

    search_data = [
        {"type": "all", "text": all_text},
        {"type": "two", "text": two_text},
        {"type": "one", "text": one_text},
    ]
    broadcast_data = []
    for single_leader_data in search_data:
        leaderboard = db.Leaderboard.find_one({"type": single_leader_data['type']})
        if leaderboard != None:
            leaderboard_item = {
                "_id": leaderboard['_id'],
                "type": single_leader_data['type'],
                "chat_id": LEADERBOARD_ID,
                "message_id": leaderboard['message_id'],
                "text": single_leader_data['text']
            }
            broadcast_data.append(leaderboard_item)
            leaderboard_update = threading.Thread(target=leaderboard_db_update, args=(leaderboard, single_leader_data['text'],))
            leaderboard_update.start()
        else:
            leaderboard = {
                "type": single_leader_data['type'],
                "chat_id": int(LEADERBOARD_ID),
                "message_id": "",
                "text": single_leader_data['text']
            }
            db.Leaderboard.insert_one(leaderboard)
            broadcast_data.append(leaderboard)

    return broadcast_data

def calculate_order(projects):
    user_lists = []
    for project in projects:
        exist_list = [user_list for user_list in user_lists if user_list['user_id'] == project['user_id']]
        if len(exist_list)>0:
            count = int(exist_list[0]['count'])+1
            total_percent = float(exist_list[0]['total_percent'])+float(percent(project['ath'], project['marketcap']))
            origin_percent = float(exist_list[0]['project']['ath'])/float(exist_list[0]['project']['marketcap'])
            new_percent = float(project['ath'])/float(project['marketcap'])
            if new_percent > origin_percent:
                exist_list[0]['project'] = project
            exist_list[0]['count'] = count
            exist_list[0]['total_percent'] = total_percent
            exist_list[0]['average_percent'] = total_percent/count
        else:
            new_list = {
                "user_id": project['user_id'],
                "project": project,
                "count": 1,
                "total_percent": percent(project['ath'], project['marketcap']),
                "average_percent": percent(project['ath'], project['marketcap'])
            }
            user_lists.append(new_list)

    results = sorted(user_lists, key=lambda d: float(d['total_percent']), reverse=True)

    final_result = results[:10]

    return final_result

def top_ten_update(all_results):
    user_id_array = []
    for all_result in all_results:
        if all_result['user_id'] not in user_id_array:
                user_id_array.append(all_result['user_id'])
    
    group_id = "master"
            
    params = {"top_users": user_id_array}
    setting_update = threading.Thread(target=db_setting_update, args=(group_id, params,))
    setting_update.start()

def broadcast_text(results):
    result_text=""
    index = 1
    for result in results:
        current_marketcap = result['project']['marketcap']
        pair = db.Pair.find_one({"pair_address": result['project']['pair_address']})
        if pair != None:
            current_marketcap = pair['marketcap']
        user = db.User.find_one({"user_id": result['user_id']})
        
        username = user['username'] if user else ""
        result_text += f"#{str(index)}: @{username}\nTotal <b>{str(round(float(result['total_percent']), 2))}x</b>, AVG: <b>{str(round(float(result['average_percent']), 2))}x</b>.\n"
        result_text += f"👉 <a href='{result['project']['pair_url']}'>{result['project']['symbol']}</a> Shared marketcap: ${format_price(result['project']['marketcap'])}\n"
        result_text += f"💰 Currently: ${format_price(current_marketcap)} ({round(float(current_marketcap)/float(result['project']['marketcap']), 2)}x)\n"
        if float(current_marketcap)<float(result['project']['ath']):
            result_text += f"🏆 ATH: ${format_price(result['project']['ath'])} ({percent(result['project']['ath'], result['project']['marketcap'])}x)\n"
        result_text += "\n"
        index +=1

    return result_text

def leaderboard_db_update(leaderboard, text):
    db.Leaderboard.find_one_and_update({"_id": leaderboard['_id']}, {"$set": {"text": text}})

def get_removed_pairs():
    removed_pairs_cursor = db.RemovedPair.find()
    removed_pairs = list(removed_pairs_cursor)
    if len(removed_pairs) > 0:
        removed_pair_details = []
        for removed_pair in removed_pairs:
            pair = db.Pair.find_one({"pair_address": removed_pair['pair_address']})
            project_cursor = db.Project.find({"pair_address": pair['pair_address']})
            projects = list(project_cursor)
            shilled_user_ids = []
            if len(projects) > 0:
                for project in projects:
                    if project['user_id'] not in shilled_user_ids:
                        shilled_user_ids.append(project['user_id'])
            shilled_usernames = []
            for user_id in shilled_user_ids:
                user = db.User.find_one({"user_id": user_id})
                if user != None:
                    shilled_usernames.append(user['username'])
            
            single_removed_pair = {
                "token": pair['token'],
                "symbol": pair['symbol'],
                "url": pair['pair_url'],
                "users": shilled_usernames
            }
            
            logging.info(f"Prepare the broadcast for {pair['pair_url']}")
            
            removed_pair_details.append(single_removed_pair)
            
        removed_pairs_details_text = []
        if len(removed_pair_details)> 0:
            for removed_pair_detail in removed_pair_details:
                text = f"<a href='{removed_pair_detail['url']}' >{removed_pair_detail['symbol']}</a> Liquidity removed\n"
                text += f"❌ <code>{removed_pair_detail['token']}</code>\n"
                if len(removed_pair_detail['users'])>0:
                    text += "\nShilled by: "
                    for black_username in removed_pair_detail['users']:
                        text += "@"+black_username+", "
                removed_pairs_details_text.append(text)
        
        db.RemovedPair.delete_many({})
        
        return removed_pairs_details_text
    
    return []