#!/usr/bin/env python3
"""
Check NIFTY price records for today
"""
import sys
sys.path.append('.')

from app import create_app
from app.models.nifty_price import NiftyPrice
from app import db
from datetime import date
import pytz

def check_todays_records():
    app = create_app()
    with app.app_context():
        today = date.today()
        records = db.session.query(NiftyPrice).filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp).all()
        
        print(f'Total NIFTY records for today ({today}): {len(records)}')
        
        if records:
            print('\nFirst 10 records:')
            for i, record in enumerate(records[:10]):
                ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                print(f'  {i+1:2d}. {ist_time.strftime("%H:%M:%S")}: Price={record.price}, High={record.high}, Low={record.low}')
                
            if len(records) > 10:
                print(f'\n... ({len(records)-10} more records) ...')
                
                print(f'\nLast 5 records:')
                for i, record in enumerate(records[-5:]):
                    ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                    print(f'  {len(records)-4+i:2d}. {ist_time.strftime("%H:%M:%S")}: Price={record.price}, High={record.high}, Low={record.low}')
                    
            # Check specifically for 9:12-9:33 AM range
            print(f'\nChecking 9:12-9:33 AM range:')
            morning_records = [r for r in records 
                             if 9 <= r.timestamp.astimezone(pytz.timezone('Asia/Kolkata')).hour <= 9 
                             and 12 <= r.timestamp.astimezone(pytz.timezone('Asia/Kolkata')).minute <= 33]
            
            if morning_records:
                print(f'Found {len(morning_records)} records in 9:12-9:33 AM:')
                for record in morning_records:
                    ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                    print(f'  {ist_time.strftime("%H:%M:%S")}: Price={record.price}, High={record.high}, Low={record.low}')
                    
                # Calculate range
                highs = [r.high or r.price for r in morning_records]
                lows = [r.low or r.price for r in morning_records]
                range_high = max(highs)
                range_low = min(lows)
                print(f'\nCalculated range: High={range_high}, Low={range_low}')
            else:
                print('No records found in 9:12-9:33 AM range')
                
        else:
            print('No records found for today!')

if __name__ == "__main__":
    check_todays_records()
