"""
Nifty Prices Data Transfer Script
Runs every minute during market hours (9:14 AM - 3:31 PM) on weekdays
Excludes holidays defined in holidays.json
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime, time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nifty_transfer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define market hours
MARKET_START = time(9, 14)  # 9:14 AM
MARKET_END = time(15, 31)   # 3:31 PM

def load_holidays():
    """Load holiday dates from holidays.json"""
    holidays_file = Path(__file__).parent.parent / 'holidays.json'
    
    try:
        if holidays_file.exists():
            with open(holidays_file, 'r') as f:
                data = json.load(f)
                # Convert string dates to date objects
                holidays = [datetime.strptime(d, '%Y-%m-%d').date() 
                           for d in data.get('holidays', [])]
                logger.info(f"Loaded {len(holidays)} holidays")
                return holidays
        else:
            logger.warning("holidays.json not found, running without holiday checks")
            return []
    except Exception as e:
        logger.error(f"Error loading holidays: {e}")
        return []

def is_trading_time():
    """Check if current time is within trading hours and not a holiday"""
    now = datetime.now()
    current_time = now.time()
    current_date = now.date()
    current_day = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Check if weekend (Saturday=5, Sunday=6)
    if current_day > 4:
        logger.info("Weekend - skipping execution")
        return False
    
    # Check if holiday
    holidays = load_holidays()
    if current_date in holidays:
        logger.info(f"Holiday ({current_date}) - skipping execution")
        return False
    
    # Check if within market hours
    if not (MARKET_START <= current_time <= MARKET_END):
        logger.info(f"Outside market hours ({current_time}) - skipping execution")
        return False
    
    return True

def get_db_connection():
    """Create and return database connection from DATABASE_URL"""
    load_dotenv()
    
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in .env file")
        
        conn = psycopg2.connect(database_url)
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def get_latest_nifty_data(conn):
    """Fetch latest records from nifty_prices table"""
    query = """
        SELECT DISTINCT ON (symbol) 
            symbol, 
            price, 
            timestamp
        FROM nifty_prices
        ORDER BY symbol, timestamp DESC;
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            logger.info(f"Fetched {len(results)} latest records from nifty_prices")
            return results
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise

def insert_into_master_clear_price(conn, data):
    """Insert data into master_clear_price table"""
    if not data:
        logger.warning("No data to insert")
        return
    
    insert_query = """
        INSERT INTO master_clear_price (symbol, price, date_time)
        VALUES %s
    """
    
    try:
        with conn.cursor() as cur:
            # Prepare data for insertion (symbol, price, timestamp)
            execute_values(cur, insert_query, data)
            conn.commit()
            logger.info(f"Successfully inserted {len(data)} records into master_clear_price")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting data: {e}")
        raise

def main():
    """Main execution function"""
    # Check if we should run during this time
    if not is_trading_time():
        return
    
    conn = None
    try:
        logger.info("Starting data transfer process")
        
        # Connect to database
        conn = get_db_connection()
        
        # Fetch latest data
        latest_data = get_latest_nifty_data(conn)
        
        if latest_data:
            # Insert into master_clear_price
            insert_into_master_clear_price(conn, latest_data)
            logger.info("Data transfer completed successfully")
        else:
            logger.warning("No data found to transfer")
            
    except Exception as e:
        logger.error(f"Process failed: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()
