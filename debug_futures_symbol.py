import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Test the futures data collection with debugging
from app import create_app
from app.services.kite_service import KiteService

app = create_app()

try:
    with app.app_context():
        kite_service = KiteService()
        
        print("Testing KiteService futures symbol construction...")
        
        # Test the symbol generation logic
        from datetime import datetime, timedelta
        import calendar
        
        underlying = "NIFTY"
        today = datetime.now()
        year = today.year
        month = today.month
        
        # Find last Thursday of current month
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        
        while last_date.weekday() != 3:  # Thursday is 3
            last_date -= timedelta(days=1)
        
        expiry_str = last_date.strftime("%y%b%d").upper()
        symbol = f"NFO:NIFTY{expiry_str}FUT"
        
        print(f"Generated symbol for {underlying}: {symbol}")
        print(f"Expiry date: {last_date.date()}")
        
        # Test kite connection
        kite = kite_service.get_kite_instance()
        if kite:
            print("Kite connection successful")
            
            # Try to fetch the quote
            print(f"Fetching quote for symbol: {symbol}")
            quote_data = kite.quote([symbol])
            print(f"Quote data received: {quote_data}")
        else:
            print("Kite connection failed")
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
