#!/usr/bin/env python3
"""
Add sample NIFTY price data for testing Strategy 1
"""

import os
import sys
from datetime import datetime, time

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.nifty_price import NiftyPrice

def add_sample_nifty_data():
    """Add sample NIFTY price data for today"""
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    with app.app_context():
        today = datetime.now().date()
        
        # Check if we already have data for today
        existing_count = NiftyPrice.query.filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).count()
        
        if existing_count > 0:
            print(f"Already have {existing_count} NIFTY records for today")
            return
        
        # Sample NIFTY data for testing (simulate market opening range)
        sample_data = [
            {
                'price': 24350.50,
                'high': 24375.25,
                'low': 24325.75,
                'open': 24340.00,
                'close': 24350.50,
                'timestamp': datetime.combine(today, time(9, 15))  # Pre-market
            },
            {
                'price': 24365.75,
                'high': 24380.50,
                'low': 24340.25,
                'open': 24350.50,
                'close': 24365.75,
                'timestamp': datetime.combine(today, time(9, 30))  # Market open
            },
            {
                'price': 24372.25,
                'high': 24395.75,
                'low': 24355.50,
                'open': 24365.75,
                'close': 24372.25,
                'timestamp': datetime.combine(today, time(9, 35))  # Current time
            }
        ]
        
        print("Adding sample NIFTY data for today...")
        
        for data in sample_data:
            nifty_record = NiftyPrice(
                symbol='NIFTY 50',
                price=data['price'],
                high=data['high'],
                low=data['low'],
                open=data['open'],
                close=data['close'],
                change=data['price'] - 24340.00,  # Change from opening
                change_percent=((data['price'] - 24340.00) / 24340.00) * 100,
                timestamp=data['timestamp']
            )
            db.session.add(nifty_record)
        
        db.session.commit()
        print(f"✅ Added {len(sample_data)} sample NIFTY records for today")
        
        # Display the range for Strategy 1
        latest_record = NiftyPrice.query.filter(
            db.func.date(NiftyPrice.timestamp) == today
        ).order_by(NiftyPrice.timestamp.desc()).first()
        
        if latest_record:
            print(f"\n📊 Current NIFTY Data for Strategy 1:")
            print(f"   Current Price: ₹{latest_record.price}")
            print(f"   Today's High: ₹{latest_record.high}")
            print(f"   Today's Low: ₹{latest_record.low}")
            print(f"   Range: ₹{latest_record.high - latest_record.low:.2f}")

if __name__ == "__main__":
    add_sample_nifty_data()
