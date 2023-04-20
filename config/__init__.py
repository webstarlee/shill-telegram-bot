from pymongo import MongoClient
import os
from pathlib import Path
from .routers import eth_routers

config_path = Path(os.path.dirname(__file__))
ROOT_PATH = config_path.parent.absolute()
mongo_url = "mongodb://mongo:0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app:6725"
mongo_client = MongoClient(mongo_url)

# mongo_db = mongo_client['shill_test']
# bot_token = "5980518310:AAH59J2CU_roxuHRfArHzq3HTuB_Dlymp-4"
# leaderboard_id = "-1001894150735"

mongo_db = mongo_client['shillmaster']
bot_token = "6127801894:AAExOYxc_EHywwg664RmWGg2myVRThN9mL4"
leaderboard_id = "-1001964784230"

#coinmarketcap api
cmc_key = "8d44a2eb-52eb-4718-8bed-5b21a1eb5747"
# moralis key
api_key = 'zr1lLilY41uO0MTVJOOMNIzMrAnbVVSqn4tRUyeicZycPR6LUVMLH2WG71sYkJNt'
# main wallet
wallet="0x2089b6C05D70EAB5c73721377e3Ad8993e05Ed5A"
# crypto chains
chains = {"ethereum": 1, "bsc": 56}
rpc_urls = {
    "ethereum": "https://mainnet.infura.io/v3/ea784836f0d34fd08a7484151071686d",
    "bsc": "https://polished-blissful-friday.bsc.discover.quiknode.pro/0d08b1a25f11c4e0ea1ecce9bd4fc5cf5a4caa43"
}
contract_abi_path = os.path.join(ROOT_PATH, "abis/erc20_abi.json")
with open(contract_abi_path) as contract_abi_file:
    contract_abi = contract_abi_file.read()

hoenypot_abi_path = os.path.join(ROOT_PATH, "abis/honeypot_abi.json")
with open(hoenypot_abi_path) as honeypot_abi_file:
    honeypot_abi = honeypot_abi_file.read()

honey_check_contracts = {
    "ethereum": "0xbF7B21D5529b4B019f1f7Ce5465Ff147463d604D",
    "bsc": "0x2d36BB090231DD6F327D6B4a7c08E5bED0030B3e"
}