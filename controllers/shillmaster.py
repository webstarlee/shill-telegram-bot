import db
import logging
import threading
from datetime import datetime
from operator import attrgetter
from helpers.text import shillmaster_text, shillmaster_status_text
from .apis import get_pairs_by_token, check_honey_by_contract
from .database import db_pair_marketcap_update, db_project_ath_update, db_warn_select
from helpers.contract import filter_by_chain, filter_by_dex, filter_by_v3

async def shillmaster(user_id, username, group_id, token):
    pairs = await get_pairs_by_token(token)
    
    if len(pairs) == 0:
        return {"is_new": False, "is_rug": True, "reason": "no_pool", "text": "There is no Liquidity for this token"}
    
    chain_filtered_pairs = filter_by_chain(pairs)
    
    if len(chain_filtered_pairs) == 0:
        return {"is_new": False, "is_rug": True, "reason": "chain", "text": "Network not supported"}

    dex_filtered_pairs = filter_by_dex(chain_filtered_pairs)
    
    if len(dex_filtered_pairs) == 0:
        return {"is_new": False, "is_rug": True, "reason": "dex", "text": "Dexrouter not supported"}
    
    v3_filtered_pairs = filter_by_v3(dex_filtered_pairs)
    
    if len(v3_filtered_pairs) == 0:
        return {"is_new": False, "is_rug": True, "reason": "v3", "text": "Uniswap V3 not supported"}
    
    pair = max(v3_filtered_pairs, key=attrgetter('liquidity.usd'))
    
    if int(pair.liquidity.usd) < 100:
        return {"is_new": False, "is_rug": True, "reason": "low_liquidity", "text": "There is very low Liquidity for this token"}
    
    honey_result = check_honey_by_contract(token, pair)
    
    if honey_result['honeypot']:
        return {"is_new": False, "is_rug": True, "reason": "honeypot", "text": f"{pair.base_token.symbol} token look like Hoenypot!"}
    
    pair_marketcap_update = threading.Thread(target=db_pair_marketcap_update, args=(pair,))
    pair_marketcap_update.start()
    
    db_project = db.Project.find_one({"user_id": user_id, "group_id": group_id, "pair_address": pair.pair_address})
    new_user_token = True
    is_new = True
    if db_project != None:
        is_new = False
        new_user_token = False
        if float(pair.fdv)>float(db_project['ath']):
            project_ath_update = threading.Thread(target=db_project_ath_update, args=(db_project, pair.fdv,))
            project_ath_update.start()
    else:
        db_project = {
            "user_id": int(user_id),
            "group_id": int(group_id),
            "chain": pair.chain_id,
            "token": pair.base_token.address,
            "symbol": pair.base_token.symbol,
            "pair_address": pair.pair_address,
            "pair_url": pair.url,
            "marketcap": pair.fdv,
            "ath": pair.fdv,
            "status": "active",
            "created_at": datetime.utcnow()
        }
        db.Project.insert_one(db_project)
    
    text = shillmaster_text(new_user_token, username, pair.fdv, db_project)
    
    return {"is_rug": False, "reason": "good", "text": text, "is_new": is_new}

def shillmaster_status(username, group_id):
    user = db.User.find_one({"username": {'$regex' : f'^{username}$', '$options' : 'i'}})

    text = f"❗ There is not any shills yet for @{username}"
    if user != None:
        if group_id == "master":
            project_cursor = db.Project.find({"user_id": user['user_id']}).sort("created_at", -1).limit(5)
            projects = list(project_cursor)
            if len(projects)>0:
                text = shillmaster_status_text(user, projects)
                
                warn = db_warn_select(user['user_id'], group_id)
                if warn['is_warn']:
                    text += f"\n⚠️ Has {warn['count']} Warning ⚠️"
        else:
            logging.info(group_id)
            logging.info(user['user_id'])
            project_cursor = db.Project.find({"user_id": user['user_id'], "group_id": group_id}).sort("created_at", -1).limit(5)
            projects = list(project_cursor)
            logging.info(projects)
            if len(projects)>0:
                text = shillmaster_status_text(user, projects)
                
                warn = db_warn_select(user['user_id'], group_id)
                if warn['is_warn']:
                    text += f"\n⚠️ Has {warn['count']} Warning ⚠️"
        
    return text