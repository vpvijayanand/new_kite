from app.models.nifty_price import NiftyPrice
from app.services.kite_service import KiteService
from app import db

class MarketService:
    def __init__(self):
        self.kite_service = KiteService()
    
    def fetch_and_save_nifty_price(self):
        try:
            price_data = self.kite_service.get_nifty_price()
            
            if price_data:
                NiftyPrice.save_price(price_data)
                return price_data
            return None
        except Exception as e:
            print(f"Error in fetch_and_save_nifty_price: {str(e)}")
            return None
    
    def get_latest_prices(self, limit=100):
        return NiftyPrice.get_latest_prices(limit)
    
    def get_price_history(self, hours=24):
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        prices = NiftyPrice.query.filter(
            NiftyPrice.timestamp >= cutoff_time
        ).order_by(NiftyPrice.timestamp.desc()).all()
        
        return [price.to_dict() for price in prices]