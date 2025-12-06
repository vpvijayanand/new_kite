#!/usr/bin/env python3
"""
Test Market Hours Status
Run this script to check current time and market hours status
"""

import os
import sys
from datetime import datetime, time
import pytz

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_market_status():
    """Check current market status"""
    
    # IST timezone
    ist_timezone = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist_timezone)
    
    # Market hours
    market_start = time(9, 30)
    market_end = time(15, 15)
    current_time = now_ist.time()
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    is_weekday = now_ist.weekday() < 5  # 0-4 are Mon-Fri
    
    # Check if within market hours
    is_market_time = market_start <= current_time <= market_end
    
    print("=" * 50)
    print("MARKET HOURS STATUS CHECK")
    print("=" * 50)
    print(f"Current IST Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Current Day: {now_ist.strftime('%A')}")
    print(f"Is Weekday: {is_weekday} (Markets open Monday-Friday)")
    print(f"Current Time: {current_time}")
    print(f"Market Hours: {market_start} - {market_end}")
    print(f"Is Market Time: {is_market_time}")
    print(f"Overall Market Open: {is_weekday and is_market_time}")
    print("=" * 50)
    
    if not is_weekday:
        print("❌ REASON: Market is closed on weekends")
    elif not is_market_time:
        if current_time < market_start:
            print("⏰ REASON: Market hasn't opened yet (Opens at 9:30 AM)")
        else:
            print("🔔 REASON: Market has closed (Closes at 3:15 PM)")
    else:
        print("✅ Market is OPEN - Strategy should execute")
    
    print("\nFor testing during closed hours, you can:")
    print("1. Modify the market_start and market_end times in strategy_service.py")
    print("2. Or add a --force flag to bypass market hours check")
    
    return is_weekday and is_market_time

if __name__ == "__main__":
    check_market_status()
