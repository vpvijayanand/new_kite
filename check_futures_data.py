import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from config.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

try:
    with engine.connect() as connection:
        result = connection.execute(text('SELECT COUNT(*) FROM futures_oi_data'))
        count = result.scalar()
        print(f'Total futures OI records: {count}')
        
        # Show latest records
        result = connection.execute(text('''
            SELECT underlying, futures_price, open_interest, volume, timestamp 
            FROM futures_oi_data 
            ORDER BY timestamp DESC 
            LIMIT 10
        '''))
        
        print("\nLatest 10 records:")
        for row in result:
            print(f"{row.underlying}: Price={row.futures_price}, OI={row.open_interest}, Time={row.timestamp}")
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
