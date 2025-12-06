#!/usr/bin/env python3
"""
Show all morning records with IST times
"""
import sys
sys.path.append('.')

from app import create_app
from app.models.nifty_price import NiftyPrice
from app import db
from datetime import date
import pytz

def show_morning_records():
    app = create_app()
    with app.app_context():
        today = date.today()
        records = db.session.query(NiftyPrice).filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp).all()
        
        print(f'Morning records (9-10 AM IST) for today:')
        morning_count = 0
        
        for i, record in enumerate(records):
            ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
            if 9 <= ist_time.hour <= 10:  # Show 9-10 AM IST
                morning_count += 1
                print(f'{i+1:3d}. UTC: {record.timestamp.strftime("%H:%M:%S")} -> IST: {ist_time.strftime("%H:%M:%S")} Price: {record.price}, High: {record.high}, Low: {record.low}')
                
        print(f'\nTotal morning records (9-10 AM IST): {morning_count}')
        
        if morning_count > 0:
            # Find range for 9:12-9:33 AM IST
            range_records = []
            for record in records:
                ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                if (ist_time.hour == 9 and 12 <= ist_time.minute <= 33):
                    range_records.append(record)
            
            print(f'\nRecords in 9:12-9:33 AM IST range: {len(range_records)}')
            if range_records:
                highs = [r.high or r.price for r in range_records]
                lows = [r.low or r.price for r in range_records]
                range_high = max(highs)
                range_low = min(lows)
                print(f'Calculated range: High={range_high}, Low={range_low}')
                
                # Show current price for comparison
                latest = records[-1]
                print(f'Current price: {latest.price}')
                
                if latest.price > range_high:
                    print(f'BULLISH BREAKOUT: {latest.price} > {range_high}')
                elif latest.price < range_low:
                    print(f'BEARISH BREAKOUT: {latest.price} < {range_low}')
                else:
                    print(f'No breakout - within range: {range_low} <= {latest.price} <= {range_high}')

if __name__ == "__main__":
    show_morning_records()
