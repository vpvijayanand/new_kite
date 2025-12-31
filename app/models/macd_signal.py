from app import db
from datetime import datetime

class MacdSignal(db.Model):
    """Model to store MACD crossover signals for different timeframes"""
    __tablename__ = 'macd_signals'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    timeframe = db.Column(db.Integer, nullable=False, index=True)  # 3, 6, 12, 15, 30
    signal = db.Column(db.String(10), nullable=False)  # BUY, SELL
    macd_line = db.Column(db.Float, nullable=False)
    signal_line = db.Column(db.Float, nullable=False)
    histogram = db.Column(db.Float, nullable=False)
    candle_timestamp = db.Column(db.DateTime, nullable=False, index=True)  # When the signal candle formed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # When signal was detected/stored
    
    # Composite index for efficient querying
    __table_args__ = (
        db.Index('idx_symbol_timeframe_candle', 'symbol', 'timeframe', 'candle_timestamp'),
        db.Index('idx_symbol_timeframe_created', 'symbol', 'timeframe', 'created_at'),
    )
    
    def __repr__(self):
        return f'<MacdSignal {self.symbol}-{self.timeframe}m {self.signal} at {self.candle_timestamp}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'signal': self.signal,
            'macd_line': round(self.macd_line, 4),
            'signal_line': round(self.signal_line, 4),
            'histogram': round(self.histogram, 4),
            'candle_timestamp': self.candle_timestamp.isoformat(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def get_latest_signal(cls, symbol='NIFTY', timeframe=15):
        """Get the latest signal for a symbol and timeframe"""
        return cls.query.filter_by(
            symbol=symbol,
            timeframe=timeframe
        ).order_by(cls.candle_timestamp.desc()).first()
    
    @classmethod
    def get_recent_signals(cls, symbol='NIFTY', timeframe=15, limit=6):
        """Get recent signals for a symbol and timeframe"""
        return cls.query.filter_by(
            symbol=symbol,
            timeframe=timeframe
        ).order_by(cls.candle_timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_all_recent_signals(cls, symbol='NIFTY', limit=6):
        """Get recent signals for all timeframes"""
        timeframes = [3, 6, 12, 15, 30]
        results = {}
        
        for tf in timeframes:
            signals = cls.get_recent_signals(symbol, tf, limit)
            results[tf] = [signal.to_dict() for signal in signals]
        
        return results
