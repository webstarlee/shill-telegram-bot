import db
from web3 import Web3
from config import wallet, rpc_urls
from datetime import datetime, timedelta
from helpers.format import invoice_hash

def check_available_time():
    current_hour_str = datetime.utcnow().strftime('%d/%m/%Y %H')
    current_date_str = datetime.utcnow().strftime('%d/%m/%Y')
    current_hour = datetime.strptime(current_hour_str, "%d/%m/%Y %H")
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")
    start_time = current_hour+timedelta(hours=1)
    end_time = current_date+timedelta(hours=24)
    number_start = int(start_time.strftime('%H'))
    number_array = []
    for time_number in range(number_start, 25):
        number_array.append(time_number)

    advertises = db.Advertise.find({"start": { "$lte": end_time }, "end": {"$gte": start_time}, "paid": {"$eq": True}})

    db_number_array = []
    if advertises != None:
        for advertise in advertises:
            db_number_start = int(advertise['start'].strftime('%H'))
            if db_number_start == 0:
                db_number_start = 24
            delta = advertise['end']-advertise['start']
            delta_hour = delta.seconds/3600
            db_number_end = db_number_start+int(delta_hour)
            if db_number_end > 24:
                db_number_end = 25
            for time_number in range(db_number_start-1, db_number_end):
                if time_number not in db_number_array:
                    db_number_array.append(time_number)

    if len(db_number_array) > 0:
        for item in db_number_array:
            if item in number_array:
                number_array.remove(item)

    return number_array

def check_available_hour(time):
    current_date_str = datetime.utcnow().strftime('%d/%m/%Y')
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")
    end_time = current_date+timedelta(hours=time)
    advertises = db.Advertise.find({"start": { "$gte": end_time }, "paid": {"$eq": True}})
    origin_array = [2,4,8,12,24]
    if advertises != None:
        for advertise in advertises:
            db_number_start = int(advertise['start'].strftime('%H'))
            if int(time)+2 > db_number_start and 2 in origin_array:
                origin_array.remove(2)
            if int(time)+4 > db_number_start and 4 in origin_array:
                origin_array.remove(4)
            if int(time)+8 > db_number_start and 8 in origin_array:
                origin_array.remove(8)
            if int(time)+12 > db_number_start and 12 in origin_array:
                origin_array.remove(12)
            if int(time)+24 > db_number_start and 24 in origin_array:
                origin_array.remove(24)

    return origin_array

def new_advertise(data):
    selected_time = int(data['time'])
    selected_hours = int(data['hours'])
    today_time = datetime.utcnow().strftime('%d/%m/%Y')
    today = datetime.strptime(today_time, "%d/%m/%Y")
    start_time = today + timedelta(hours=selected_time)
    end_time = start_time + timedelta(hours=selected_hours)
    advertise = {
        "user_id":int(data['user_id']),
        "start":start_time,
        "end":end_time,
        "paid": False,
        "created_at": datetime.utcnow()
    }
    db.Advertise.insert_one(advertise)

    return advertise

def create_invoice(advertise, symbol, quantity):
    address = wallet
    _hash=invoice_hash()
    invoice = {
        "user_id": int(advertise['user_id']),
        "hash": _hash,
        "advertise_id": advertise['_id'],
        "address": address,
        "symbol": symbol,
        "quantity": quantity,
        "paid": False,
        "created_at": datetime.utcnow()
    }
    db.Invoice.insert_one(invoice)

    return invoice

def get_invoice(hash, user_id):
    return db.Invoice.find_one({"hash": hash, "user_id": user_id, "paid": False})

def complete_invoice(data):
    try:
        invoice = db.Invoice.find_one({"_id": data['invoice_id']})
        if invoice != None:
            chain = "ethereum"
            if invoice['symbol'] == "BNB": chain = "bsc"

            rpc_url = rpc_urls[chain]
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            transaction = web3.eth.get_transaction(data['transaction'])
            value = int(transaction['value'])
            final_value = value/10**18
            if str(transaction['to_address']).lower() == str(invoice['address']).lower() and float(invoice['quantity']) <= float(final_value):
                db.Invoice.update_one({"_id", invoice['_id']}, {"$set": {"paid": True}})
                return True

        return False
    except Exception:
        return False

def edit_advertise(data):
    invoice = db.Invoice.find_one({"_id": data['invoice_id']})
    if invoice != None:
        if invoice['paid']:
            advertise = db.Advertise.find_one_and_update({"_id": invoice['advertise_id']}, {"$set": {"text": data['text'], "url": data['url'], "paid": True}})
            return advertise
            
    return None

def get_advertise():
    now_time = datetime.utcnow()
    advertise = db.Advertise.find_one({"start": {"$lte": now_time}, "end": {"$gte": now_time}, "paid": {"$eq": True}})

    return advertise