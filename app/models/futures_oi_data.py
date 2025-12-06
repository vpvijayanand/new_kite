from app import db
from datetime import datetime
import pytz

class FuturesOIData(db.Model):
    __tablename__ = 'futures_oi_data'
    
    id = db.Column(db.Integer, primary_key=True)
    underlying = db.Column(db.String(20), nullable=False, index=True)  # NIFTY, BANKNIFTY
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    futures_price = db.Column(db.Float, nullable=False)
    open_interest = db.Column(db.BigInteger, nullable=False)
    volume = db.Column(db.BigInteger, default=0)
    
    # Calculated fields
    price_change = db.Column(db.Float, default=0.0)  # Change from previous record
    oi_change = db.Column(db.BigInteger, default=0)  # Change from previous record
    meaning = db.Column(db.String(50))  # Long buildup, Short buildup, etc.
    trend = db.Column(db.String(20))  # Bullish, Bearish
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_futures_oi_underlying_date', 'underlying', 'timestamp'),
        db.Index('idx_futures_oi_expiry_timestamp', 'expiry_date', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<FuturesOIData {self.underlying} {self.timestamp} Price:{self.futures_price} OI:{self.open_interest}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'underlying': self.underlying,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'futures_price': self.futures_price,
            'open_interest': self.open_interest,
            'volume': self.volume,
            'price_change': self.price_change,
            'oi_change': self.oi_change,
            'meaning': self.meaning,
            'trend': self.trend,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def calculate_meaning_and_trend(price_change, oi_change):
        """
        Calculate meaning and trend based on price and OI changes
        
        Price | OI | Meaning | Trend
        ↑     | ↑  | Long buildup | Bullish
        ↓     | ↑  | Short buildup | Bearish  
        ↑     | ↓  | Short covering | Bullish
        ↓     | ↓  | Long unwinding | Bearish
        """
        if price_change > 0 and oi_change > 0:
            return "Long buildup", "Bullish"
        elif price_change < 0 and oi_change > 0:
            return "Short buildup", "Bearish"
        elif price_change > 0 and oi_change < 0:
            return "Short covering", "Bullish"
        elif price_change < 0 and oi_change < 0:
            return "Long unwinding", "Bearish"
        else:
            # No change or mixed signals
            return "No clear signal", "Neutral"
