import json
import logging
from dateutil.parser import parse
from datetime import datetime
import db

def project_json_to_mongo():
    f = open('projects.json', encoding="utf8")
    data = json.load(f)
    index = 1
    for i in data:
        created_at = i['created_at'].split(".")[0]
        create_at_time = datetime.strptime(created_at, "%d/%m/%Y %H:%M:%S")
        project_data = {
            "user_id": int(i['user_id']),
            "group_id": int(i['chat_id']),
            "chain": i['chain_id'],
            "token": i['token'],
            "symbol": i['token_symbol'],
            "pair_address": i['pair_address'],
            "pair_url": i['url'],
            "marketcap": i['marketcap'],
            "ath": i['ath_value'],
            "status": i['status'],
            "created_at": create_at_time,
        }
        db.Project.insert_one(project_data)
        logging.info(f"Project insert {index} -> {i['token']}")
        index += 1
    logging.info("Completed")
    f.close()

def pair_json_to_mongo():
    f = open('projects.json', encoding="utf8")
    data = json.load(f)
    index = 1
    pair_addresses = []
    for i in data:
        if i['pair_address'] not in pair_addresses:
            pair_addresses.append(i['pair_address'])
            created_at = i['created_at'].split(".")[0]
            create_at_time = datetime.strptime(created_at, "%d/%m/%Y %H:%M:%S")
            db_pair = {
                "chain": i['chain_id'],
                "token": i['token'],
                "symbol": i['token_symbol'],
                "pair_address": i['pair_address'],
                "pair_url": i['url'],
                "marketcap": i['marketcap'],
                "status": "active",
                "updated_at": create_at_time,
            }
            db.Pair.insert_one(db_pair)
            logging.info(f"Pair insert {index} -> {i['pair_address']}")
            index += 1
    logging.info("Completed")
    f.close()

def pair_update_status():
    pair_cursor = db.Pair.find()
    pairs = list(pair_cursor)
    for pair in pairs:
        logging.info(f"Update pair for : {pair['_id']}")
        db.Pair.find_one_and_update({"_id": pair['_id']}, {"$set": {"status": "active"}})
    
    logging.info("Done")

def user_json_to_mongo():
    f = open('projects.json', encoding="utf8")
    data = json.load(f)
    index = 1
    user_ids = []
    for i in data:
        if i['user_id'] not in user_ids:
            user_ids.append(i['user_id'])
            db_user = {
                "fullname": i['username'],
                "username": i['username'],
                "user_id": int(i['user_id']),
            }
            db.User.insert_one(db_user)
            logging.info(f"User insert {index} -> {i['username']}")
            index += 1
    logging.info("User Insert Completed")
    f.close()

def group_json_to_mongo():
    f = open('projects.json', encoding="utf8")
    data = json.load(f)
    index = 1
    group_ids = []
    for i in data:
        if "-100" in i['chat_id'] and i['chat_id'] not in group_ids:
            group_ids.append(i['chat_id'])
            db_group = {
                "title": "",
                "group_id": int(i['chat_id']),
            }
            db.Group.insert_one(db_group)
            logging.info(f"Group insert {index} -> {i['chat_id']}")
            index += 1
    logging.info("Group insert Completed")
    f.close()

def group_user_json_to_mongo():
    f = open('projects.json', encoding="utf8")
    data = json.load(f)
    index = 1
    group_users = []
    for i in data:
        if "-100" in i['chat_id']:
            exist = [group_user for group_user in group_users if group_user['group_id'] == int(i['chat_id']) and group_user['user_id'] == int(i['user_id'])]
            if len(exist)==0:
                db_group_user = {
                    "user_id": int(i['user_id']),
                    "group_id": int(i['chat_id']),
                }
                group_users.append(db_group_user)
                
                db.GroupUser.insert_one(db_group_user)
                logging.info(f"Group User insert {index} -> {i['chat_id']} : {i['user_id']}")
                index += 1
                
    logging.info("Group User insert Completed")
    f.close()

def ban_json_to_mongo():
    f = open('bans.json', encoding="utf8")
    data = json.load(f)
    index = 1
    for i in data:
        db_ban = {
            "user_id": int(i['user_id']),
            "group_id": int(i['chat_id']),
        }
        db.Ban.insert_one(db_ban)
        logging.info(f"Ban insert {index} -> {i['chat_id']}")
        index += 1
    logging.info("Ban insert Completed")
    f.close()
    
def warn_json_to_mongo():
    f = open('warns.json', encoding="utf8")
    data = json.load(f)
    index = 1
    for i in data:
        db_warn = {
            "user_id": int(i['user_id']),
            "group_id": int(i['chat_id']),
            "count": int(i['count'])
        }
        db.Warn.insert_one(db_warn)
        logging.info(f"Warn insert {index} -> {i['chat_id']}")
        index += 1
    logging.info("Warn insert Completed")
    f.close()

def admins_database():
    admin_dbs = []
    webstar = {"fullname": "Web Star", "username": "webstarlee", "user_id": 5887308508}
    aleek = {"fullname": "Aleekk | Dev of GrimaceCoin", "username": "aLeekk0", "user_id": 1533375074}
    kaan = {"fullname": "Kaan $GM ☕️ | Business Developer of GrimaceCoin", "username": "KaanApes", "user_id": 5191683494}
    admin_dbs.append(webstar)
    admin_dbs.append(aleek)
    admin_dbs.append(kaan)
    for single_data in admin_dbs:
        admin = db.Admin.find_one({'user_id': int(single_data['user_id'])})
        if admin == None:
            db.Admin.insert_one(single_data)

def all_project_to_active():
    project_cursor = db.Project.find({})
    projects = list(project_cursor)
    index = 1
    for project in projects:
        db.Project.find_one_and_update({'_id': project['_id']}, {"$set": {"status": "active"}})
        logging.info(f"Project Update {index} -> {project['token']}")
        index += 1
    
    logging.info("Project Update Completed")