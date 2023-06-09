import db
import logging
from datetime import datetime

def db_setting_select(group_id):
    db_setting = db.Setting.find_one({"group_id": group_id})
    if db_setting == None:
        db_setting = {
            "group_id": int(group_id),
            "top_users": [],
            "shill_mode": False,
            "ban_mode": False,
        }
        db.Setting.insert_one(db_setting)
    
    return db_setting

def db_ban_insert(warn):
    user_ban = db.Ban.find_one({"user_id": warn['user_id'], "group_id": warn['group_id']})
    if user_ban == None:
        user_ban = {
            "user_id": int(warn['user_id']),
            "group_id": int(warn['group_id'])
        }
        db.Ban.insert_one(user_ban)
    
    logging.info("User Banned")

def db_ban_remove(user):
    db.Ban.find_one_and_delete({"user_id": user['user_id'], "group_id": user['group_id']})

    logging.info("Ban Removed")

def db_warn_remove(warn):
    db.Warn.find_one_and_delete({"user_id": warn['user_id'], "group_id": warn['group_id']})

    logging.info("Warn Removed")

def db_user_insert(user_id, username, first_name, last_name):
    fullname = str(first_name)+" "+str(last_name)
    
    db_user = db.User.find_one({"user_id": user_id})
    if db_user == None:
        db_user = {
            "user_id": int(user_id),
            "fullname": fullname,
            "username": username
        }
        db.User.insert_one(db_user)
    
        logging.info(f"User Inserted {fullname}")

def db_group_insert(group_id, title):
    db_group = db.Group.find_one({"group_id": group_id})
    if db_group == None:
        db_group = {
            "group_id": int(group_id),
            "title": title
        }
        db.Group.insert_one(db_group)
    
        logging.info(f"Group Inserted {title}")

def db_group_user_insert(group_id, user_id):
    db_group_user = db.GroupUser.find_one({"group_id": group_id, "user_id": user_id})
    if db_group_user == None:
        db_group_user = {
            "group_id": int(group_id),
            "user_id": int(user_id)
        }
        db.GroupUser.insert_one(db_group_user)
    
        logging.info("Group user Inserted")

def db_warn_update(user_id, group_id):
    warn_user = db.Warn.find_one({"user_id": user_id, "group_id": group_id})
    if warn_user != None:
        current_count = warn_user['count']
        increase_count = int(current_count)+1
        db.Warn.update_one({"_id": warn_user['_id']},{"$set":{"count": increase_count}})
    else:
        warn_user = {
            "user_id": int(user_id),
            "group_id": int(group_id),
            "count": 1
        }
        db.Warn.insert_one(warn_user)
    
    return warn_user

def db_warn_select(user_id, group_id):
    
    if group_id == "master":
        user_warns_cursor = db.Warn.find({"user_id": user_id})
        user_warns = list(user_warns_cursor)
        warn_count = 0
        for user_warn in user_warns:
            if user_warn != None:
                warn_count =warn_count + int(user_warn['count'])
        
        return {"is_warn": True, "count": warn_count}
    else:
        user_warn = db.Warn.find_one({"user_id": user_id, "group_id": group_id})
        warn_count = 0
        if user_warn != None:
            warn_count = user_warn['count']
            return {"is_warn": True, "count": warn_count}

    return {"is_warn": False}

def db_project_ath_update(project, new_ath):
    db.Project.update_one({"_id": project['_id']},{"$set":{"ath": new_ath}})
    logging.info(f"Project Token - {project['symbol']} ATH updated: {new_ath}")

def db_pair_marketcap_update(pair):
    db_pair = db.Pair.find_one({"pair_address": pair.pair_address})

    if db_pair != None:
        db.Pair.update_one({"_id": db_pair['_id']},{"$set":{"marketcap": pair.fdv, "status": "active"}})
    else:
        db_pair = {
            "chain": pair.chain_id,
            "token": pair.base_token.address,
            "symbol": pair.base_token.symbol,
            "pair_address": pair.pair_address,
            "pair_url": pair.url,
            "marketcap": pair.fdv,
            "status": "active",
            "updated_at": datetime.utcnow()
        }
        db.Pair.insert_one(db_pair)
    
def is_admin(user_id):
    admin = db.Admin.find_one({"user_id": user_id})
    if admin != None:
        return True
    return False

def db_setting_update(group_id, params):
    setting = db.Setting.find_one({"group_id": group_id})
    if setting != None:
        db.Setting.find_one_and_update({"_id": setting['_id']}, {"$set": params})
    else:
        setting = {"group_id": group_id, "top_users": [], "shill_mode": False, "ban_mode": False}
        setting.update(params)
        db.Setting.insert_one(setting)
        
def db_user_warn_remove(username, group_id):
    user = db.User.find_one({"username": {'$regex' : f'^{username}$', '$options' : 'i'}})
    if user != None:
        db.Warn.find_one_and_delete({"user_id": user['user_id'], "group_id": group_id})
        
def db_banned_user_select(username, group_id):
    user = db.User.find_one({"username": {'$regex' : f'^{username}$', '$options' : 'i'}})
    if user != None:
        db.Ban.find_one({"user_id": user['user_id'], "group_id": group_id})
        
def db_task_select():
    task_cursor = db.Task.find({})
    tasks = list(task_cursor)
    
    return tasks

def db_group_select():
    group_cursor = db.Group.find({})
    groups = list(group_cursor)
    
    return groups

def db_group_update(group_id, title):
    group = db.Group.find_one({"group_id": group_id})
    if group != None:
        db.Group.update_one({"_id": group['_id']}, {'$set': {"title": title}})
        logging.info(f"Group updated with {title}")

def db_group_user_select():
    group_user_cursor = db.GroupUser.find({})
    group_users = list(group_user_cursor)
    
    return group_users

def db_user_update(user):
    db_user = db.User.find_one({"user_id": user.id})
    if db_user != None:
        fullname = user.first_name
        if user.last_name != None:
            fullname = fullname+" "+user.last_name
            
        db.User.find_one_and_update({"_id": db_user['_id']}, {"$set": {"fullname": fullname}})
        logging.info(f"User updated with {fullname}")