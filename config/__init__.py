import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

basedir = os.path.abspath(os.path.dirname(__file__))
engine = create_engine("sqlite:///" + os.path.join(basedir, "database.db"), echo=True)
Session = sessionmaker(bind=engine)
# bot_token = "6127801894:AAExOYxc_EHywwg664RmWGg2myVRThN9mL4"
bot_token = "5980518310:AAH59J2CU_roxuHRfArHzq3HTuB_Dlymp-4"
# leaderboard_id = "-1001964784230"
leaderboard_id = "-1001894150735"
cmc_key = "e8456919-e960-45bf-865c-96d04f767c7c"
# moralis key
api_key = 'zr1lLilY41uO0MTVJOOMNIzMrAnbVVSqn4tRUyeicZycPR6LUVMLH2WG71sYkJNt'
inspector = inspect(engine)
eth_url = 'https://goerli.infura.io/v3/ea784836f0d34fd08a7484151071686d'
bsc_url='https://data-seed-prebsc-1-s1.binance.org:8545'
wallet="0x2089b6C05D70EAB5c73721377e3Ad8993e05Ed5A"
chains = {"ethereum": 1, "bsc": 56}