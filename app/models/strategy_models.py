from app import db
from datetime import datetime
import pytz

class Strategy1Execution(db.Model):
    __tablename__ = 'strategy1_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Timestamp and basic info
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')), nullable=False)
    execution_date = db.Column(db.Date, nullable=False)
    
    # NIFTY range data (9:12 - 9:33 AM)
    range_high = db.Column(db.Float, nullable=True)
    range_low = db.Column(db.Float, nullable=True)
    range_captured = db.Column(db.Boolean, default=False)
    
    # Current NIFTY price at execution
    current_nifty_price = db.Column(db.Float, nullable=True)
    
    # Strategy trigger status
    triggered = db.Column(db.Boolean, default=False)
    trigger_type = db.Column(db.String(20), nullable=True)  # 'LOW_BREAK' or 'HIGH_BREAK'
    
    # Position details
    sell_strike = db.Column(db.Float, nullable=True)
    buy_strike = db.Column(db.Float, nullable=True)
    option_type = db.Column(db.String(2), nullable=True)  # 'CE' or 'PE'
    
    # LTP at entry
    sell_ltp_entry = db.Column(db.Float, nullable=True)
    buy_ltp_entry = db.Column(db.Float, nullable=True)
    net_premium_entry = db.Column(db.Float, nullable=True)
    
    # Current LTP (updated every minute)
    sell_ltp_current = db.Column(db.Float, nullable=True)
    buy_ltp_current = db.Column(db.Float, nullable=True)
    net_premium_current = db.Column(db.Float, nullable=True)
    
    # P&L calculations
    current_pnl = db.Column(db.Float, default=0.0)
    capital_used = db.Column(db.Float, default=0.0)
    pnl_percentage = db.Column(db.Float, default=0.0)
    
    # Position parameters
    lots = db.Column(db.Integer, default=3)
    quantity_per_lot = db.Column(db.Integer, default=75)
    total_quantity = db.Column(db.Integer, default=225)
    
    # Market status
    is_market_hours = db.Column(db.Boolean, default=True)
    
    # Additional metadata
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Strategy1Execution {self.execution_date} - {self.trigger_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'execution_date': self.execution_date.isoformat() if self.execution_date else None,
            'range_high': self.range_high,
            'range_low': self.range_low,
            'range_captured': self.range_captured,
            'current_nifty_price': self.current_nifty_price,
            'triggered': self.triggered,
            'trigger_type': self.trigger_type,
            'sell_strike': self.sell_strike,
            'buy_strike': self.buy_strike,
            'option_type': self.option_type,
            'sell_ltp_entry': self.sell_ltp_entry,
            'buy_ltp_entry': self.buy_ltp_entry,
            'net_premium_entry': self.net_premium_entry,
            'sell_ltp_current': self.sell_ltp_current,
            'buy_ltp_current': self.buy_ltp_current,
            'net_premium_current': self.net_premium_current,
            'current_pnl': self.current_pnl,
            'capital_used': self.capital_used,
            'pnl_percentage': self.pnl_percentage,
            'lots': self.lots,
            'quantity_per_lot': self.quantity_per_lot,
            'total_quantity': self.total_quantity,
            'is_market_hours': self.is_market_hours,
            'notes': self.notes
        }
