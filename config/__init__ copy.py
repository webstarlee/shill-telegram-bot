import os
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient

basedir = os.path.abspath(os.path.dirname(__file__))
path = Path(basedir).parent.absolute()
parent_path = path.parent.absolute()
db_url = "mysql+pymysql://root:KH6b22RFlJotPAUgqxFg@containers-us-west-33.railway.app:6576/railway"
mongo_url = "mongodb://mongo:0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app:6725"
# db_url = "mysql+pymysql://root:52b1wqBLweYfvvRIndEY@containers-us-west-83.railway.app:6949/railway"
engine = create_engine(db_url, echo=True)
# Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client['shill_test']
advertise_collection = mongo_db['advertises']
# engine = create_engine("mongodb:///?Server=0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app&Port=6725&Database=shills&User=mongo&Password=0vAcYlPN44ugKCNqFXNc")
Session = sessionmaker(bind=engine)
# bot_token = "6127801894:AAExOYxc_EHywwg664RmWGg2myVRThN9mL4"
bot_token = "5980518310:AAH59J2CU_roxuHRfArHzq3HTuB_Dlymp-4"
# leaderboard_id = "-1001964784230"
leaderboard_id = "-1001894150735"
cmc_key = "e8456919-e960-45bf-865c-96d04f767c7c"
# moralis key
api_key = 'zr1lLilY41uO0MTVJOOMNIzMrAnbVVSqn4tRUyeicZycPR6LUVMLH2WG71sYkJNt'
inspector = inspect(engine)
wallet="0x2089b6C05D70EAB5c73721377e3Ad8993e05Ed5A"
chains = {"ethereum": 1, "bsc": 56}