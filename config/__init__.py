from pymongo import MongoClient



from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient

mongo_url = "mongodb://mongo:0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app:6725"
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client['shill_test']
advertise_collection = mongo_db['advertises']
# bot_token = "6127801894:AAExOYxc_EHywwg664RmWGg2myVRThN9mL4"
bot_token = "5980518310:AAH59J2CU_roxuHRfArHzq3HTuB_Dlymp-4"
# leaderboard_id = "-1001964784230"
leaderboard_id = "-1001894150735"
cmc_key = "e8456919-e960-45bf-865c-96d04f767c7c"
# moralis key
api_key = 'zr1lLilY41uO0MTVJOOMNIzMrAnbVVSqn4tRUyeicZycPR6LUVMLH2WG71sYkJNt'
wallet="0x2089b6C05D70EAB5c73721377e3Ad8993e05Ed5A"
chains = {"ethereum": 1, "bsc": 56}




db_url = "mysql+pymysql://root:KH6b22RFlJotPAUgqxFg@containers-us-west-33.railway.app:6576/railway"
engine = create_engine(db_url, echo=True)
Session = sessionmaker(bind=engine)
inspector = inspect(engine)