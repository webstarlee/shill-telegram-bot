import time
import maya
import string
import random
import datetime

utc_now = datetime.datetime.utcnow()

def format_price(price):
    price = float(price)
    formatted_price = "{:,.2f}".format(price)
    
    return formatted_price

def percent(number1, number2):
    number1 = float(number1)
    number2 = float(number2)
    
    return str(round(float(number1/number2), 2))

def am_pm_time(item):
    item = int(item)
    time_numner = item
    status = "AM"
    if item == 0:
        time_numner = 12
    elif item == 12:
        status = "PM"
    elif item == 24:
        time_numner = 12
    elif item > 12:
        time_numner = item-12
        status = "PM"
    result_time = str(time_numner)+str(status)
    return result_time

def invoice_hash():
    chars = string.ascii_uppercase+string.digits
    stamp = time.time()
    _hash = ''.join(random.choice(chars) for _ in range(16))
    result = str(_hash)+str(stamp)
    return result

def get_time_delta(time_one, time_two):
    cal_time_one = time_one
    cal_time_two = time_two
    if not isinstance(time_one, datetime.date):
        cal_time_one_datetime = maya.parse(time_one).datetime()
        cal_time_one_date = cal_time_one_datetime.date()
        cal_time_one_time = cal_time_one_datetime.time()
        cal_time_one_time = str(cal_time_one_time).split('.')[0]
        cal_time_one_str = str(cal_time_one_date)+" "+str(cal_time_one_time)
        cal_time_one = datetime.datetime.strptime(cal_time_one_str, '%Y-%m-%d %H:%M:%S')
    
    
    if not isinstance(time_two, datetime.date):
        cal_time_two_datetime = maya.parse(time_two).datetime()
        cal_time_two_date = cal_time_two_datetime.date()
        cal_time_two_time = cal_time_two_datetime.time()
        cal_time_two_time = str(cal_time_two_time).split('.')[0]
        cal_time_two_str = str(cal_time_two_date)+" "+str(cal_time_two_time)
        cal_time_two = datetime.datetime.strptime(cal_time_two_str, '%Y-%m-%d %H:%M:%S')

    delta = cal_time_two-cal_time_one
    delta_min = delta.seconds/60
    return delta_min
