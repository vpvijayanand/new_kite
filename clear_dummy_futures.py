from app import create_app
from app.models.futures_oi_data import FuturesOIData
from app import db

app = create_app()
ctx = app.app_context()
ctx.push()

try:
    # Count current records
    count = FuturesOIData.query.count()
    print(f'Current futures OI records: {count}')
    
    # Delete all records
    if count > 0:
        deleted = db.session.query(FuturesOIData).delete()
        db.session.commit()
        print(f'Deleted {deleted} dummy records')
        
        # Verify deletion
        remaining = FuturesOIData.query.count()
        print(f'Remaining records: {remaining}')
    else:
        print('No records to delete')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    db.session.rollback()
finally:
    ctx.pop()
