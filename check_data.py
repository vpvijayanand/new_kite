from app import create_app
from app.models.nifty_price import NiftyPrice
from app import db
from datetime import datetime, timedelta

app = create_app('development')
with app.app_context():
    # Check recent data
    recent = db.session.query(NiftyPrice).filter(
        NiftyPrice.symbol == 'NIFTY 50'
    ).order_by(NiftyPrice.timestamp.desc()).limit(10).all()
    
    print('Recent 10 records:')
    for r in recent:
        print(f'{r.timestamp}: {r.price}')
    
    total = db.session.query(NiftyPrice).filter(NiftyPrice.symbol == 'NIFTY 50').count()
    print(f'\nTotal records: {total}')
    
    # Check data from last 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    recent_24h = db.session.query(NiftyPrice).filter(
        NiftyPrice.symbol == 'NIFTY 50',
        NiftyPrice.timestamp >= start_time
    ).count()
    
    print(f'Records in last 24 hours: {recent_24h}')
