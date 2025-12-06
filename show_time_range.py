#!/usr/bin/env python3
"""
Show actual time range of all records
"""
import sys
sys.path.append('.')

from app import create_app
from app.models.nifty_price import NiftyPrice
from app import db
from datetime import date
import pytz

def show_actual_time_range():
    app = create_app()
    with app.app_context():
        today = date.today()
        records = db.session.query(NiftyPrice).filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp).all()
        
        if records:
            print(f'Total records for today: {len(records)}')
            
            # Show first and last record
            first = records[0]
            last = records[-1]
            
            first_ist = first.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
            last_ist = last.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
            
            print(f'\nFirst record:')
            print(f'  UTC: {first.timestamp}')
            print(f'  IST: {first_ist}')
            print(f'  Price: {first.price}')
            
            print(f'\nLast record:')
            print(f'  UTC: {last.timestamp}')
            print(f'  IST: {last_ist}')
            print(f'  Price: {last.price}')
            
            # Show all IST hours that have records
            ist_hours = set()
            for record in records:
                ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                ist_hours.add(ist_time.hour)
            
            print(f'\nIST Hours with records: {sorted(ist_hours)}')
            
            # Show records by hour
            for hour in sorted(ist_hours):
                hour_records = []
                for record in records:
                    ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                    if ist_time.hour == hour:
                        hour_records.append(record)
                print(f'  {hour:2d}:xx IST - {len(hour_records)} records')
                
                # Show a few records from each hour
                if len(hour_records) <= 5:
                    for record in hour_records:
                        ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                        print(f'    {ist_time.strftime("%H:%M:%S")}: {record.price}')
                else:
                    # Show first 2 and last 2
                    for record in hour_records[:2]:
                        ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                        print(f'    {ist_time.strftime("%H:%M:%S")}: {record.price}')
                    print(f'    ... ({len(hour_records)-4} more records) ...')
                    for record in hour_records[-2:]:
                        ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                        print(f'    {ist_time.strftime("%H:%M:%S")}: {record.price}')
        else:
            print('No records found for today!')

if __name__ == "__main__":
    show_actual_time_range()
