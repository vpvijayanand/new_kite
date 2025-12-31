from app import db
from datetime import datetime
import pytz

class Strategy1Entry(db.Model):
    """Separate table to track strategy entry details with NIFTY range data"""
    __tablename__ = 'strategy1_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Entry timestamp and date
    entry_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    
    # NIFTY range data during 9:12-9:33 AM
    nifty_high_912_933 = db.Column(db.Float, nullable=False)  # High during 9:12-9:33
    nifty_low_912_933 = db.Column(db.Float, nullable=False)   # Low during 9:12-9:33
    nifty_price_912 = db.Column(db.Float, nullable=True)      # Price at 9:12 AM
    nifty_price_933 = db.Column(db.Float, nullable=True)      # Price at 9:33 AM
    range_size = db.Column(db.Float, nullable=False)          # High - Low
    
    # Entry trigger details
    trigger_type = db.Column(db.String(20), nullable=False)    # 'LOW_BREAK' or 'HIGH_BREAK'
    trigger_nifty_price = db.Column(db.Float, nullable=False)  # NIFTY price when triggered
    
    # Strike prices
    sell_strike = db.Column(db.Float, nullable=False)
    buy_strike = db.Column(db.Float, nullable=False)
    option_type = db.Column(db.String(2), nullable=False)      # 'CE' or 'PE'
    
    # Entry LTPs
    sell_ltp_entry = db.Column(db.Float, nullable=False)
    buy_ltp_entry = db.Column(db.Float, nullable=False)
    net_premium_entry = db.Column(db.Float, nullable=False)
    
    # Position size
    lots = db.Column(db.Integer, default=3)
    quantity_per_lot = db.Column(db.Integer, default=75)
    total_quantity = db.Column(db.Integer, default=225)
    capital_used = db.Column(db.Float, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    closed_timestamp = db.Column(db.DateTime, nullable=True)
    close_reason = db.Column(db.String(50), nullable=True)
    
    # Relationship to LTP history
    ltp_history = db.relationship('Strategy1LTPHistory', backref='entry', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Strategy1Entry {self.entry_date} - {self.trigger_type} - {self.sell_strike}/{self.buy_strike} {self.option_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'entry_timestamp': self.entry_timestamp.isoformat() if self.entry_timestamp else None,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'nifty_high_912_933': self.nifty_high_912_933,
            'nifty_low_912_933': self.nifty_low_912_933,
            'nifty_price_912': self.nifty_price_912,
            'nifty_price_933': self.nifty_price_933,
            'range_size': self.range_size,
            'trigger_type': self.trigger_type,
            'trigger_nifty_price': self.trigger_nifty_price,
            'sell_strike': self.sell_strike,
            'buy_strike': self.buy_strike,
            'option_type': self.option_type,
            'sell_ltp_entry': self.sell_ltp_entry,
            'buy_ltp_entry': self.buy_ltp_entry,
            'net_premium_entry': self.net_premium_entry,
            'lots': self.lots,
            'quantity_per_lot': self.quantity_per_lot,
            'total_quantity': self.total_quantity,
            'capital_used': self.capital_used,
            'is_active': self.is_active,
            'closed_timestamp': self.closed_timestamp.isoformat() if self.closed_timestamp else None,
            'close_reason': self.close_reason
        }

class Strategy1LTPHistory(db.Model):
    """Table to track every LTP and P&L change for active positions"""
    __tablename__ = 'strategy1_ltp_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to entry
    entry_id = db.Column(db.Integer, db.ForeignKey('strategy1_entries.id'), nullable=False)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')), nullable=False)
    
    # Current NIFTY price
    nifty_price = db.Column(db.Float, nullable=False)
    
    # Current LTPs
    sell_ltp = db.Column(db.Float, nullable=False)
    buy_ltp = db.Column(db.Float, nullable=False)
    net_premium = db.Column(db.Float, nullable=False)
    
    # P&L calculations
    sell_pnl = db.Column(db.Float, nullable=False)     # (Entry_Sell_LTP - Current_Sell_LTP) * Qty
    buy_pnl = db.Column(db.Float, nullable=False)      # (Current_Buy_LTP - Entry_Buy_LTP) * Qty
    total_pnl = db.Column(db.Float, nullable=False)    # Sell_PnL + Buy_PnL
    pnl_percentage = db.Column(db.Float, nullable=False) # (Total_PnL / Capital_Used) * 100
    
    # Additional context
    is_market_hours = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<Strategy1LTPHistory Entry:{self.entry_id} - {self.timestamp.strftime("%H:%M")} - PnL:{self.total_pnl}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'nifty_price': self.nifty_price,
            'sell_ltp': self.sell_ltp,
            'buy_ltp': self.buy_ltp,
            'net_premium': self.net_premium,
            'sell_pnl': self.sell_pnl,
            'buy_pnl': self.buy_pnl,
            'total_pnl': self.total_pnl,
            'pnl_percentage': self.pnl_percentage,
            'is_market_hours': self.is_market_hours,
            'notes': self.notes
        }

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
