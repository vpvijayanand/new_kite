from app import db
from datetime import datetime
from sqlalchemy import Index

class NiftySignal(db.Model):
    """
    Model to store NIFTY trading signals based on Fast/Slow MA crossover
    Equivalent to Pine Script: Fast MA (12) crossover/crossunder Slow MA (27)
    """
    __tablename__ = 'nifty_signals'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Signal Information
    signal_type = db.Column(db.String(10), nullable=False)  # 'BUY' or 'SELL'
    signal_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Price Information at signal time
    price = db.Column(db.Float, nullable=False)  # NIFTY price when signal generated
    fast_ma = db.Column(db.Float, nullable=False)  # Fast MA (12) value
    slow_ma = db.Column(db.Float, nullable=False)  # Slow MA (27) value
    very_slow_ma = db.Column(db.Float)  # Very Slow MA (189) value
    
    # Technical Indicators
    ma_difference = db.Column(db.Float)  # fast_ma - slow_ma
    ma_difference_percent = db.Column(db.Float)  # (ma_difference / price) * 100
    
    # Signal Strength & Context
    trend_direction = db.Column(db.String(10))  # 'UP' or 'DOWN' based on very_slow_ma
    volume = db.Column(db.BigInteger)  # Volume at signal time (if available)
    
    # Signal Validation
    is_valid = db.Column(db.Boolean, default=True)  # For filtering false signals
    confidence_score = db.Column(db.Float)  # 0-100 confidence in signal
    
    # Performance Tracking
    entry_price = db.Column(db.Float)  # Price when position taken
    exit_price = db.Column(db.Float)  # Price when position closed
    exit_time = db.Column(db.DateTime)  # When position was closed
    pnl = db.Column(db.Float)  # Profit/Loss from this signal
    pnl_percent = db.Column(db.Float)  # P&L percentage
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for performance
    __table_args__ = (
        Index('idx_signal_time', 'signal_time'),
        Index('idx_signal_type', 'signal_type'),
        Index('idx_signal_time_type', 'signal_time', 'signal_type'),
    )
    
    def __repr__(self):
        return f'<NiftySignal {self.signal_type} at {self.signal_time} price={self.price}>'
    
    def to_dict(self):
        """Convert signal to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'signal_type': self.signal_type,
            'signal_time': self.signal_time.isoformat() if self.signal_time else None,
            'price': self.price,
            'fast_ma': self.fast_ma,
            'slow_ma': self.slow_ma,
            'very_slow_ma': self.very_slow_ma,
            'ma_difference': self.ma_difference,
            'ma_difference_percent': self.ma_difference_percent,
            'trend_direction': self.trend_direction,
            'is_valid': self.is_valid,
            'confidence_score': self.confidence_score,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_latest_signals(cls, limit=50):
        """Get the latest signals"""
        return cls.query.order_by(cls.signal_time.desc()).limit(limit).all()
    
    @classmethod
    def get_signals_by_date(cls, date):
        """Get signals for a specific date"""
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        return cls.query.filter(
            cls.signal_time >= start_date,
            cls.signal_time <= end_date
        ).order_by(cls.signal_time.desc()).all()
    
    @classmethod
    def get_performance_summary(cls):
        """Get performance summary of all signals"""
        total_signals = cls.query.count()
        buy_signals = cls.query.filter_by(signal_type='BUY').count()
        sell_signals = cls.query.filter_by(signal_type='SELL').count()
        
        # Calculate P&L statistics
        valid_pnl_signals = cls.query.filter(
            cls.pnl.isnot(None),
            cls.is_valid == True
        ).all()
        
        total_pnl = sum(s.pnl for s in valid_pnl_signals)
        profitable_trades = len([s for s in valid_pnl_signals if s.pnl > 0])
        losing_trades = len([s for s in valid_pnl_signals if s.pnl < 0])
        
        return {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_pnl': total_pnl,
            'profitable_trades': profitable_trades,
            'losing_trades': losing_trades,
            'win_rate': (profitable_trades / len(valid_pnl_signals) * 100) if valid_pnl_signals else 0
        }
