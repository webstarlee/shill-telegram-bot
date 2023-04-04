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
inspector = inspect(engine)