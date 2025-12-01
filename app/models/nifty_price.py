from app import db
from datetime import datetime

class NiftyPrice(db.Model):
    __tablename__ = 'nifty_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, default='NIFTY 50')
    price = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float)
    change_percent = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<NiftyPrice {self.symbol} - {self.price} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @classmethod
    def get_latest_prices(cls, limit=100):
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def save_price(cls, price_data):
        """Save NIFTY price data - only during market hours (9:00 AM to 3:45 PM IST)"""
        from app.utils.datetime_utils import is_market_hours
        
        # Check if current time is within market hours
        if not is_market_hours():
            print("Skipping NIFTY price collection - outside market hours (9:00 AM - 3:45 PM IST)")
            return None
            
        new_price = cls(
            symbol=price_data.get('symbol', 'NIFTY 50'),
            price=price_data['price'],
            change=price_data.get('change'),
            change_percent=price_data.get('change_percent')
        )
        db.session.add(new_price)
        db.session.commit()
        return new_price