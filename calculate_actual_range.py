#!/usr/bin/env python3
"""
Calculate range using the actual stored times (3:42-4:03 IST which should be 9:12-9:33)
"""
import sys
sys.path.append('.')

from app import create_app
from app.models.nifty_price import NiftyPrice
from app import db
from datetime import date, time
import pytz

def calculate_actual_range():
    app = create_app()
    with app.app_context():
        today = date.today()
        
        # The data is stored as 3:xx-4:xx IST but should be 9:xx IST
        # So 9:12-9:33 IST would be stored as 3:42-4:03 IST
        # Calculate: 9:12 - 5:30 = 3:42, 9:33 - 5:30 = 4:03
        
        records = db.session.query(NiftyPrice).filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp).all()
        
        # Find records between 3:42-4:03 in the stored IST times
        range_records = []
        for record in records:
            # The timestamps are stored with IST timezone but wrong time
            record_time = record.timestamp.time()
            
            # Check if time is between 3:42 and 4:03 (equivalent to 9:12-9:33 IST)
            if (record_time >= time(3, 42) and record_time <= time(4, 3)):
                range_records.append(record)
        
        print(f'Records found in 3:42-4:03 range (equivalent to 9:12-9:33 IST): {len(range_records)}')
        
        if range_records:
            for record in range_records[:5]:  # Show first 5
                # Add 5 hours 30 minutes to convert to actual IST
                hour_add = 5
                minute_add = 30
                new_minute = record.timestamp.minute + minute_add
                new_hour = record.timestamp.hour + hour_add
                
                if new_minute >= 60:
                    new_minute -= 60
                    new_hour += 1
                    
                print(f'  Stored: {record.timestamp.time()} -> Actual IST: {new_hour:02d}:{new_minute:02d}: Price={record.price}, High={record.high}, Low={record.low}')
            
            if len(range_records) > 5:
                print(f'  ... and {len(range_records) - 5} more records')
            
            # Calculate range
            highs = [r.high or r.price for r in range_records]
            lows = [r.low or r.price for r in range_records]
            range_high = max(highs)
            range_low = min(lows)
            
            print(f'\nCalculated Range:')
            print(f'  High: {range_high}')
            print(f'  Low: {range_low}')
            
            # Get current price
            latest = records[-1]
            current_price = latest.price
            
            print(f'\nBreakout Analysis:')
            print(f'  Current Price: {current_price}')
            
            if current_price > range_high:
                print(f'  ✅ BULLISH BREAKOUT: {current_price} > {range_high}')
            elif current_price < range_low:
                print(f'  ✅ BEARISH BREAKOUT: {current_price} < {range_low}')
            else:
                print(f'  ❌ No breakout - within range: {range_low} <= {current_price} <= {range_high}')
        else:
            print('No records found in the expected time range')

if __name__ == "__main__":
    calculate_actual_range()
