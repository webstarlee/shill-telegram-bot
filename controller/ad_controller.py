from model.tables import Advertise, Invoice
from datetime import datetime, timedelta
from sqlalchemy import or_
from config import Session, eth_url, bsc_url, api_key
from helper import create_new_wallet
from web3 import Web3
from moralis import evm_api

db = Session()
eth_web3 = Web3(Web3.HTTPProvider(eth_url))
bsc_web3 = Web3(Web3.HTTPProvider(bsc_url))

def new_advertise(data):
    selected_time = int(data['time'])
    selected_hours = int(data['hours'])
    today_time = datetime.utcnow().strftime('%d/%m/%Y')
    today = datetime.strptime(today_time, "%d/%m/%Y")
    start_time = today + timedelta(hours=selected_time)
    end_time = start_time + timedelta(hours=selected_hours)
    advertise = Advertise(
        username=data['username'],
        start=start_time,
        end=end_time,
    )
    db.add(advertise)
    db.commit()

    return advertise

def create_invoice(advertise, symbol, quantity):
    new_wallet = create_new_wallet()
    invoice = Invoice(
        username=advertise.username,
        advertise_id=advertise.id,
        private=new_wallet['private'],
        address=new_wallet['address'],
        symbol=symbol,
        quantity=quantity,
    )
    db.add(invoice)
    db.commit()

    return invoice

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

    print(number_array)
    advertises = db.query(Advertise).filter(Advertise.start <= end_time).filter(Advertise.end >= start_time).all()

    db_number_array = []
    if advertises != None:
        for advertise in advertises:
            # db_start_time = datetime.strptime(advertise.start, "%d/%m/%Y %H")
            # db_end_time = datetime.strptime(advertise.end, "%d/%m/%Y %H")
            db_number_start = int(advertise.start.strftime('%H'))
            print(db_number_start)
            
            delta = advertise.end-advertise.start
            delta_hour = delta.seconds/3600
            db_number_end = db_number_start+int(delta_hour)
            if db_number_end > 24:
                db_number_end = 25
            for time_number in range(db_number_start-1, db_number_end):
                if not time_number in db_number_array:
                    db_number_array.append(time_number)

    if len(db_number_array) > 0:
        for item in db_number_array:
            if item in number_array:
                number_array.remove(item)

    print(number_array)
    return number_array

def check_available_hour(time):
    current_date_str = datetime.utcnow().strftime('%d/%m/%Y')
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")
    end_time = current_date+timedelta(hours=time)
    advertises = db.query(Advertise).filter(Advertise.start >= end_time).all()
    origin_array = [2,4,8,12,24]
    if advertises != None:
        for advertise in advertises:
            db_number_start = int(advertise.start.strftime('%H'))
            if int(time)+2 > db_number_start:
                if 2 in origin_array: origin_array.remove(2)
            if int(time)+4 > db_number_start:
                if 4 in origin_array: origin_array.remove(4)
            if int(time)+8 > db_number_start:
                if 8 in origin_array: origin_array.remove(8)
            if int(time)+12 > db_number_start:
                if 12 in origin_array: origin_array.remove(12)
            if int(time)+24 > db_number_start:
                if 24 in origin_array: origin_array.remove(24)
    
    print(origin_array)
    return origin_array

def complete_invoice(invoice):
    params = {}
    chain = "eth"
    if invoice.symbol == "BNB":
        chain = "bsc"
    params = {
        "address": invoice.address,
        "chain": chain,
    }

    response = evm_api.transaction.get_wallet_transactions(api_key=api_key, params=params)

    print("checking")
    if len(response['result'])>0:
        transactions = response['result']
        for transaction in transactions:
            print(transaction)
            value = int(transaction['value'])
            final_value = value/10**18
            if str(transaction['to_address']).lower() == str(invoice.address).lower() and float(invoice.quantity) <= float(final_value):
                ed_invoice = db.query(Invoice).filter(Invoice.id == invoice.id).first()
                if ed_invoice != None:
                    ed_invoice.paid = True
                    db.commit()
                return True
        return False
    else:
        return False

def edit_advertise(data):
    invoice = db.query(Invoice).filter(Invoice.id == data['invoice_id']).first()
    if invoice != None:
        if invoice.paid:
            advertise = db.query(Advertise).filter(Advertise.id == data['advertise_id']).first()
            if advertise != None:
                advertise.text = data['text']
                advertise.url = data['url']
                advertise.paid = True
                db.commit()

def get_active_advertise():
    now_time = datetime.utcnow()
    advertise = db.query(Advertise).filter(Advertise.start <= now_time).filter(Advertise.end >= now_time).filter(Advertise.paid == True).first()

    return advertise