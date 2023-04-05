from model.tables import Advertise
from datetime import datetime, timedelta
from sqlalchemy import or_
from config import Session

db = Session()

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
        text=data['text'],
        url=data['url'],
    )
    db.add(advertise)
    db.commit()

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

    advertises = db.query(Advertise).filter(Advertise.start <= end_time).filter(Advertise.end >= start_time).all()

    db_number_array = []
    if advertises != None:
        for advertise in advertises:
            # db_start_time = datetime.strptime(advertise.start, "%d/%m/%Y %H")
            # db_end_time = datetime.strptime(advertise.end, "%d/%m/%Y %H")
            db_number_start = int(advertise.start.strftime('%H'))
            
            delta = advertise.end-advertise.start
            delta_hour = delta.seconds/3600
            db_number_end = db_number_start+int(delta_hour)
            if db_number_end > 24:
                db_number_end = 24
            for time_number in range(db_number_start-2, db_number_end+1):
                if not time_number in db_number_array:
                    db_number_array.append(time_number)

    if len(db_number_array) > 0:
        for item in db_number_array:
            if item in number_array:
                number_array.remove(item)

    print(number_array)
    return number_array