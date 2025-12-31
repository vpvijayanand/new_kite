#!/usr/bin/env python3
"""
Debug UTC time conversion for range calculation
"""
import sys
sys.path.append('.')

from app import create_app
from app.models.nifty_price import NiftyPrice
from app import db
from datetime import date, time, datetime, timezone, timedelta
import pytz

def debug_time_conversion():
    print("=== UTC Time Conversion Debug ===")
    
    today = date.today()
    start_time = time(9, 12)
    end_time = time(9, 33)
    
    print(f"Today: {today}")
    print(f"Target IST range: {start_time} - {end_time}")
    
    # Create IST timezone
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    
    # Convert IST times to UTC datetime objects for today
    start_datetime_ist = datetime.combine(today, start_time, tzinfo=ist_tz)
    end_datetime_ist = datetime.combine(today, end_time, tzinfo=ist_tz)
    
    # Convert to UTC
    start_datetime_utc = start_datetime_ist.astimezone(timezone.utc)
    end_datetime_utc = end_datetime_ist.astimezone(timezone.utc)
    
    print(f"IST start: {start_datetime_ist}")
    print(f"IST end: {end_datetime_ist}")
    print(f"UTC start: {start_datetime_utc}")
    print(f"UTC end: {end_datetime_utc}")
    
    # Check database records in this range
    app = create_app()
    with app.app_context():
        records = db.session.query(NiftyPrice).filter(
            NiftyPrice.timestamp >= start_datetime_utc,
            NiftyPrice.timestamp <= end_datetime_utc
        ).order_by(NiftyPrice.timestamp).all()
        
        print(f"\nRecords found in UTC range: {len(records)}")
        
        if records:
            for record in records:
                ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
                print(f"  {record.timestamp} UTC -> {ist_time} IST: Price={record.price}")
        
        # Also check what records exist around this time
        print(f"\nAll records around this time:")
        all_records = db.session.query(NiftyPrice).filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp).all()
        
        for record in all_records:
            ist_time = record.timestamp.astimezone(pytz.timezone('Asia/Kolkata'))
            if ist_time.time() >= time(9, 10) and ist_time.time() <= time(9, 35):
                print(f"  {record.timestamp} UTC -> {ist_time.strftime('%H:%M:%S')} IST: Price={record.price}")

if __name__ == "__main__":
    debug_time_conversion()
