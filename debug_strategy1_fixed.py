#!/usr/bin/env python3
"""
Debug Strategy 1 breakout detection logic
"""
import sys
import os
sys.path.append('.')

from datetime import datetime
import pytz

def debug_strategy1_breakout():
    """Debug why Strategy 1 shows MONITORING instead of executing bearish breakout"""
    
    print("=== Strategy 1 Breakout Debug Analysis ===")
    print(f"Current Time (IST): {datetime.now(pytz.timezone('Asia/Kolkata'))}")
    print()
    
    try:
        # Create Flask app context
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Initialize services
            from app.services.strategy_service import StrategyService
            from app.services.kite_service import KiteService
            
            strategy_service = StrategyService()
            kite_service = KiteService()
            
            # Get current NIFTY price with OHLC data
            print("1. Getting Current NIFTY Data...")
            current_data = kite_service.get_nifty_price()
            print(f"Current NIFTY Data: {current_data}")
            print()
            
            # Get the range data that strategy uses
            print("2. Getting Range Data (High/Low from 9:12-9:33 AM)...")
            range_data = strategy_service.get_nifty_high_low_range()
            print(f"Range Data: {range_data}")
            print()
            
            # Extract values for analysis
            current_price = current_data.get('price') if current_data else None
            range_high = range_data.get('high') if range_data else None
            range_low = range_data.get('low') if range_data else None
            
            print("3. Breakout Analysis:")
            print(f"  Current Price: {current_price}")
            print(f"  Range High: {range_high}")
            print(f"  Range Low: {range_low}")
            print()
            
            # Check breakout conditions
            if current_price and range_high and range_low:
                print("4. Breakout Decision:")
                if current_price > range_high:
                    print(f"  ✅ BULLISH BREAKOUT: {current_price} > {range_high}")
                    print(f"     Should execute: BULLISH credit spread strategy")
                elif current_price < range_low:
                    print(f"  ✅ BEARISH BREAKOUT: {current_price} < {range_low}")
                    print(f"     Should execute: BEARISH credit spread strategy")
                else:
                    print(f"  ❌ No breakout - within range: {range_low} <= {current_price} <= {range_high}")
                    print(f"     Should show: MONITORING status")
            else:
                print("4. Missing Data Issues:")
                if not current_price: 
                    print(f"    ❌ Current price is None or missing")
                if not range_high: 
                    print(f"    ❌ Range high is None or missing")
                if not range_low: 
                    print(f"    ❌ Range low is None or missing")
            
            print()
            
            # Additional debugging - check actual database records
            print("5. Database Range Records Check:")
            try:
                from app.models.nifty_price import NiftyPrice
                from app import db
                
                # Get records from 9:12-9:33 AM today
                ist = pytz.timezone('Asia/Kolkata')
                today = datetime.now(ist).date()
                
                # Query records in the time range
                records = db.session.query(NiftyPrice).filter(
                    db.func.date(NiftyPrice.timestamp) == today,
                    db.func.extract('hour', NiftyPrice.timestamp) == 9,
                    db.func.extract('minute', NiftyPrice.timestamp).between(12, 33)
                ).order_by(NiftyPrice.timestamp).all()
                
                if records:
                    print(f"  Found {len(records)} records in 9:12-9:33 AM range:")
                    for record in records:
                        print(f"    {record.timestamp}: Price={record.price}, High={record.high}, Low={record.low}")
                    
                    # Calculate actual high/low from records
                    actual_high = max(r.high or r.price for r in records)
                    actual_low = min(r.low or r.price for r in records)
                    print(f"  Calculated Range: High={actual_high}, Low={actual_low}")
                else:
                    print(f"  ❌ No records found in 9:12-9:33 AM range for today")
                    
            except Exception as e:
                print(f"  Error checking database records: {str(e)}")
            
            print()
            print("=== Debug Analysis Complete ===")
        
    except Exception as e:
        print(f"Error in debug analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_strategy1_breakout()
