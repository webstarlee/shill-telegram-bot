from pymongo import MongoClient

mongo_url = "mongodb://mongo:L3mgF7RCFIHcq3HjfgUM@containers-us-west-54.railway.app:6647"
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client['shillmaster']

Ban = mongo_db['bans']
Warn = mongo_db['warns']
Task = mongo_db['tasks']
User = mongo_db['users']
Pair = mongo_db['pairs']
Group = mongo_db['groups']
Admin = mongo_db['admins']
Project = mongo_db['projects']
Invoice = mongo_db['invoices']
Setting = mongo_db['settings']
Advertise = mongo_db['advertises']
GroupUser = mongo_db['group_users']
Leaderboard = mongo_db['leaderboards']
RemovedPair = mongo_db['removed_pairs']