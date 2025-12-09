import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from config.config import Config
from app.utils.datetime_utils import format_ist_time_only, utc_to_ist

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

try:
    with engine.connect() as connection:
        result = connection.execute(text('''
            SELECT underlying, futures_price, open_interest, timestamp 
            FROM futures_oi_data 
            ORDER BY timestamp DESC 
            LIMIT 5
        '''))
        
        print("Latest 5 futures records with IST time conversion:")
        print("="*60)
        for row in result:
            utc_time = row.timestamp
            ist_time = format_ist_time_only(utc_time)
            print(f"{row.underlying:8} | Price: {row.futures_price:8.1f} | OI: {row.open_interest:10,} | UTC: {utc_time.strftime('%H:%M:%S')} | IST: {ist_time}")
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
