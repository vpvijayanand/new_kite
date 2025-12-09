import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import SQLAlchemy directly
from sqlalchemy import create_engine, text
from config.config import Config

# Create database connection directly
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

try:
    with engine.connect() as connection:
        # Count current records
        result = connection.execute(text('SELECT COUNT(*) FROM futures_oi_data'))
        count = result.scalar()
        print(f'Current futures OI records: {count}')
        
        # Delete all records if any exist
        if count > 0:
            result = connection.execute(text('DELETE FROM futures_oi_data'))
            deleted = result.rowcount
            connection.commit()
            print(f'Deleted {deleted} dummy records')
            
            # Verify deletion
            result = connection.execute(text('SELECT COUNT(*) FROM futures_oi_data'))
            remaining = result.scalar()
            print(f'Remaining records: {remaining}')
        else:
            print('No records to delete')
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
