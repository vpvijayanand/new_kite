"""
Script to update existing records in option_chain_data table
to calculate price changes (ce_change, pe_change, ce_change_percent, pe_change_percent)
for records that currently have 0 values.
"""

from app import create_app, db
from app.models.banknifty_price import OptionChainData
from sqlalchemy import text
from datetime import datetime

def update_existing_price_changes():
    """Update existing records to calculate price changes"""
    
    app = create_app()
    
    with app.app_context():
        print("Starting update of existing price change records...")
        
        # Get all records ordered by underlying, strike_price, expiry_date, timestamp
        print("Fetching all records...")
        records = db.session.query(OptionChainData).order_by(
            OptionChainData.underlying,
            OptionChainData.strike_price,
            OptionChainData.expiry_date,
            OptionChainData.timestamp
        ).all()
        
        print(f"Found {len(records)} total records")
        
        updated_count = 0
        processed_count = 0
        
        # Group records by underlying, strike_price, expiry_date
        current_group = None
        previous_record = None
        
        for record in records:
            processed_count += 1
            
            # Create group key
            group_key = (record.underlying, record.strike_price, record.expiry_date)
            
            # If we're in a new group, reset previous_record
            if current_group != group_key:
                current_group = group_key
                previous_record = record
                continue
            
            # Calculate changes if current record has 0 changes and previous record exists
            needs_update = False
            
            # Check CE changes
            if (record.ce_change == 0.0 and record.ce_change_percent == 0.0 and 
                previous_record and previous_record.ce_ltp > 0 and record.ce_ltp > 0):
                
                ce_change = record.ce_ltp - previous_record.ce_ltp
                ce_change_percent = (ce_change / previous_record.ce_ltp) * 100 if previous_record.ce_ltp > 0 else 0.0
                
                # Only update if there's a meaningful change (not exactly 0)
                if abs(ce_change) > 0.0001:  # Avoid floating point precision issues
                    record.ce_change = round(ce_change, 4)
                    record.ce_change_percent = round(ce_change_percent, 4)
                    needs_update = True
            
            # Check PE changes
            if (record.pe_change == 0.0 and record.pe_change_percent == 0.0 and 
                previous_record and previous_record.pe_ltp > 0 and record.pe_ltp > 0):
                
                pe_change = record.pe_ltp - previous_record.pe_ltp
                pe_change_percent = (pe_change / previous_record.pe_ltp) * 100 if previous_record.pe_ltp > 0 else 0.0
                
                # Only update if there's a meaningful change (not exactly 0)
                if abs(pe_change) > 0.0001:  # Avoid floating point precision issues
                    record.pe_change = round(pe_change, 4)
                    record.pe_change_percent = round(pe_change_percent, 4)
                    needs_update = True
            
            if needs_update:
                updated_count += 1
                if updated_count % 100 == 0:
                    print(f"Updated {updated_count} records so far...")
                    db.session.commit()  # Commit in batches
            
            # Update previous_record for next iteration
            previous_record = record
            
            if processed_count % 1000 == 0:
                print(f"Processed {processed_count} records...")
        
        # Final commit
        db.session.commit()
        
        print(f"\nUpdate completed!")
        print(f"Total records processed: {processed_count}")
        print(f"Records updated with price changes: {updated_count}")
        
        # Verify the update
        print("\nVerifying updates...")
        
        # Count records with non-zero changes
        ce_changes = db.session.query(OptionChainData).filter(OptionChainData.ce_change != 0.0).count()
        pe_changes = db.session.query(OptionChainData).filter(OptionChainData.pe_change != 0.0).count()
        
        print(f"Records with CE price changes: {ce_changes}")
        print(f"Records with PE price changes: {pe_changes}")
        
        # Show some examples
        sample_changes = db.session.query(OptionChainData).filter(
            (OptionChainData.ce_change != 0.0) | (OptionChainData.pe_change != 0.0)
        ).order_by(OptionChainData.timestamp.desc()).limit(5).all()
        
        print("\nSample updated records:")
        for record in sample_changes:
            print(f"Strike {record.strike_price}: CE_Change: {record.ce_change}, CE_Change%: {record.ce_change_percent}, PE_Change: {record.pe_change}, PE_Change%: {record.pe_change_percent}")

if __name__ == "__main__":
    update_existing_price_changes()
