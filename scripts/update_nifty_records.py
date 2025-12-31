#!/usr/bin/env python3
"""
Update existing NIFTY price records to populate high, low, open, close fields
"""

import os
import sys

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.nifty_price import NiftyPrice

def update_existing_records():
    """Update existing NIFTY price records with missing high/low/open/close data"""
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    with app.app_context():
        # Find records with NULL high/low/open/close values
        records_to_update = NiftyPrice.query.filter(
            (NiftyPrice.high == None) | 
            (NiftyPrice.low == None) |
            (NiftyPrice.open == None) |
            (NiftyPrice.close == None)
        ).all()
        
        print(f"Found {len(records_to_update)} records to update")
        
        updated_count = 0
        for record in records_to_update:
            # Use the existing price value for missing OHLC data
            if record.high is None:
                record.high = record.price
            if record.low is None:
                record.low = record.price
            if record.open is None:
                record.open = record.price
            if record.close is None:
                record.close = record.price
                
            updated_count += 1
            
        # Commit the changes
        db.session.commit()
        print(f"Updated {updated_count} records successfully")
        
        # Verify the update
        remaining_nulls = NiftyPrice.query.filter(
            (NiftyPrice.high == None) | 
            (NiftyPrice.low == None) |
            (NiftyPrice.open == None) |
            (NiftyPrice.close == None)
        ).count()
        
        print(f"Records with NULL values remaining: {remaining_nulls}")
        
        if remaining_nulls == 0:
            print("✅ All existing records updated successfully!")
        else:
            print("⚠️  Some records still have NULL values")

if __name__ == "__main__":
    update_existing_records()
