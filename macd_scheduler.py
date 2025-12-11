#!/usr/bin/env python3
"""
Standalone MACD Calculator and Scheduler
Calculates MACD signals for multiple timeframes and updates the nifty_prices table
Can be run independently or as a scheduled service

Usage:
    python macd_scheduler.py --calculate-all    # Calculate for all historical data
    python macd_scheduler.py --update-latest    # Update latest signals only
    python macd_scheduler.py --schedule          # Run as continuous scheduler
"""

import sys
import os
import argparse
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytz
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('macd_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MacdCalculator:
    """Calculate MACD signals using EMA12-EMA27 formula"""
    
    def __init__(self, database_url=None):
        """Initialize calculator with database connection"""
        if not database_url:
            # Default SQLite database path
            database_url = 'sqlite:///instance/kite_app.db'
        
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.ist = pytz.timezone('Asia/Kolkata')
        
        logger.info(f"MACD Calculator initialized with database: {database_url}")
    
    def get_price_data(self, symbol='NIFTY 50', limit=5000):
        """Get price data from database"""
        query = text("""
            SELECT id, price, timestamp 
            FROM nifty_prices 
            WHERE symbol = :symbol 
            ORDER BY timestamp ASC 
            LIMIT :limit
        """)
        
        result = self.session.execute(query, {'symbol': symbol, 'limit': limit})
        data = result.fetchall()
        
        if not data:
            logger.warning(f"No data found for symbol: {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['id', 'price', 'timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Convert to IST timezone
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(self.ist)
        df.set_index('timestamp', inplace=True)
        
        logger.info(f"Retrieved {len(df)} price records for {symbol}")
        return df
    
    def calculate_macd_signals(self, df, timeframes=['3min', '6min', '15min', '30min']):
        """Calculate MACD signals for multiple timeframes"""
        results = {}
        
        for timeframe in timeframes:
            logger.info(f"Calculating MACD for {timeframe} timeframe")
            
            # Resample data to timeframe
            ohlc_data = df['price'].resample(timeframe).ohlc()
            ohlc_data.dropna(inplace=True)
            
            if len(ohlc_data) < 50:  # Need enough data for EMA27 + margin
                logger.warning(f"Insufficient data for {timeframe}: {len(ohlc_data)} candles")
                continue
            
            # Use close prices for MACD calculation
            close_prices = ohlc_data['close']
            
            # Calculate EMAs using the specified formula: EMA12 - EMA27
            ema_12 = close_prices.ewm(span=12).mean()
            ema_27 = close_prices.ewm(span=27).mean()  # Changed from 26 to 27
            
            # Calculate MACD line
            macd_line = ema_12 - ema_27
            
            # Calculate Signal line (9-period EMA of MACD)
            signal_line = macd_line.ewm(span=9).mean()
            
            # Calculate Histogram
            histogram = macd_line - signal_line
            
            # Find crossover signals
            signals = []
            for i in range(1, len(macd_line)):
                prev_macd = macd_line.iloc[i-1]
                prev_signal = signal_line.iloc[i-1]
                curr_macd = macd_line.iloc[i]
                curr_signal = signal_line.iloc[i]
                timestamp = macd_line.index[i]
                
                signal_type = None
                if prev_macd <= prev_signal and curr_macd > curr_signal:
                    signal_type = 'BUY'
                elif prev_macd >= prev_signal and curr_macd < curr_signal:
                    signal_type = 'SELL'
                
                if signal_type:
                    # Format: "BUY 10-12-2025 14:30" or "SELL 10-12-2025 14:30"
                    date_str = timestamp.strftime('%d-%m-%Y')
                    time_str = timestamp.strftime('%H:%M')
                    signal_string = f"{signal_type} {date_str} {time_str}"
                    
                    signals.append({
                        'timestamp': timestamp,
                        'signal': signal_type,
                        'signal_string': signal_string,
                        'macd_line': curr_macd,
                        'signal_line': curr_signal,
                        'histogram': histogram.iloc[i]
                    })
            
            results[timeframe] = signals
            logger.info(f"Found {len(signals)} crossover signals for {timeframe}")
        
        return results
    
    def update_nifty_prices_table(self, signals_by_timeframe):
        """Update nifty_prices table with latest MACD signals"""
        try:
            # Get the latest signal for each timeframe
            latest_signals = {}
            timeframe_columns = {
                '3min': 'macd_3m',
                '6min': 'macd_6m', 
                '15min': 'macd_15m',
                '30min': 'macd_30m'
            }
            
            for timeframe, signals in signals_by_timeframe.items():
                if signals:
                    # Get the most recent signal
                    latest_signal = max(signals, key=lambda x: x['timestamp'])
                    latest_signals[timeframe] = latest_signal['signal_string']
                    logger.info(f"Latest {timeframe} signal: {latest_signal['signal_string']}")
            
            # Update all records with the latest signals
            if latest_signals:
                # Build update query
                set_clauses = []
                params = {}
                
                for timeframe, column in timeframe_columns.items():
                    if timeframe in latest_signals:
                        set_clauses.append(f"{column} = :{column}")
                        params[column] = latest_signals[timeframe]
                
                if set_clauses:
                    update_query = f"""
                        UPDATE nifty_prices 
                        SET {', '.join(set_clauses)}
                        WHERE symbol = :symbol
                    """
                    params['symbol'] = 'NIFTY 50'
                    
                    result = self.session.execute(text(update_query), params)
                    self.session.commit()
                    
                    logger.info(f"Updated {result.rowcount} records with latest MACD signals")
                    
                    # Log the updates
                    for timeframe, signal_string in latest_signals.items():
                        logger.info(f"Set {timeframe_columns[timeframe]} = {signal_string}")
            
        except Exception as e:
            logger.error(f"Error updating nifty_prices table: {str(e)}")
            self.session.rollback()
            raise
    
    def calculate_and_update_all(self):
        """Calculate MACD signals for all data and update database"""
        try:
            logger.info("Starting full MACD calculation for all historical data")
            
            # Get price data
            df = self.get_price_data()
            if df.empty:
                logger.error("No price data available")
                return False
            
            # Calculate signals for all timeframes
            signals = self.calculate_macd_signals(df)
            
            # Update database
            self.update_nifty_prices_table(signals)
            
            logger.info("Full MACD calculation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in calculate_and_update_all: {str(e)}")
            return False
    
    def update_latest_signals(self):
        """Update only the latest MACD signals (for scheduler)"""
        try:
            logger.info("Updating latest MACD signals")
            
            # Get recent data (last 1000 records should be enough for calculations)
            df = self.get_price_data(limit=1000)
            if df.empty:
                logger.error("No price data available")
                return False
            
            # Calculate signals
            signals = self.calculate_macd_signals(df)
            
            # Update database
            self.update_nifty_prices_table(signals)
            
            logger.info("Latest MACD signals updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in update_latest_signals: {str(e)}")
            return False
    
    def get_latest_signals_summary(self):
        """Get summary of latest MACD signals"""
        try:
            query = text("""
                SELECT symbol, macd_3m, macd_6m, macd_15m, macd_30m
                FROM nifty_prices 
                WHERE symbol = 'NIFTY 50'
                AND id = (SELECT MAX(id) FROM nifty_prices WHERE symbol = 'NIFTY 50')
            """)
            
            result = self.session.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    'symbol': row[0],
                    '3min': row[1] or 'No signal',
                    '6min': row[2] or 'No signal',
                    '15min': row[3] or 'No signal',
                    '30min': row[4] or 'No signal'
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest signals: {str(e)}")
            return None
    
    def close(self):
        """Close database connection"""
        self.session.close()

def run_scheduler():
    """Run MACD calculator as continuous scheduler"""
    logger.info("Starting MACD Scheduler - will update every 5 minutes")
    
    calculator = MacdCalculator()
    
    try:
        while True:
            logger.info("Running scheduled MACD update")
            
            # Update latest signals
            success = calculator.update_latest_signals()
            
            if success:
                # Show summary
                summary = calculator.get_latest_signals_summary()
                if summary:
                    logger.info("Current MACD Signals:")
                    for timeframe, signal in summary.items():
                        if timeframe != 'symbol':
                            logger.info(f"  {timeframe}: {signal}")
            
            # Wait 5 minutes before next update
            logger.info("Waiting 5 minutes for next update...")
            time.sleep(300)  # 300 seconds = 5 minutes
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
    finally:
        calculator.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='MACD Calculator and Scheduler')
    parser.add_argument('--calculate-all', action='store_true', 
                       help='Calculate MACD for all historical data')
    parser.add_argument('--update-latest', action='store_true',
                       help='Update latest MACD signals only')
    parser.add_argument('--schedule', action='store_true',
                       help='Run as continuous scheduler')
    parser.add_argument('--summary', action='store_true',
                       help='Show current MACD signals summary')
    
    args = parser.parse_args()
    
    if not any([args.calculate_all, args.update_latest, args.schedule, args.summary]):
        parser.print_help()
        return
    
    calculator = MacdCalculator()
    
    try:
        if args.calculate_all:
            logger.info("Calculating MACD for all historical data...")
            success = calculator.calculate_and_update_all()
            if success:
                print("✅ All historical MACD calculations completed!")
            else:
                print("❌ Error in calculations")
        
        elif args.update_latest:
            logger.info("Updating latest MACD signals...")
            success = calculator.update_latest_signals()
            if success:
                print("✅ Latest MACD signals updated!")
            else:
                print("❌ Error updating signals")
        
        elif args.schedule:
            run_scheduler()
        
        elif args.summary:
            summary = calculator.get_latest_signals_summary()
            if summary:
                print("\n📊 Current MACD Signals:")
                print("=" * 40)
                for timeframe, signal in summary.items():
                    if timeframe != 'symbol':
                        print(f"{timeframe:>6}: {signal}")
            else:
                print("❌ No signals found")
        
        # Always show summary at the end
        if not args.schedule and not args.summary:
            summary = calculator.get_latest_signals_summary()
            if summary:
                print("\n📊 Updated MACD Signals:")
                print("=" * 40)
                for timeframe, signal in summary.items():
                    if timeframe != 'symbol':
                        print(f"{timeframe:>6}: {signal}")
    
    finally:
        calculator.close()

if __name__ == '__main__':
    main()
