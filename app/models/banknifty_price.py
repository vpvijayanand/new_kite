from app import db
from datetime import datetime

class BankNiftyPrice(db.Model):
    __tablename__ = 'banknifty_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, default='NIFTY BANK')
    price = db.Column(db.Float, nullable=False)
    change = db.Column(db.Float)
    change_percent = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<BankNiftyPrice {self.symbol} - {self.price} at {self.timestamp}>'
    
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
        new_price = cls(
            symbol=price_data.get('symbol', 'NIFTY BANK'),
            price=price_data['price'],
            change=price_data.get('change'),
            change_percent=price_data.get('change_percent')
        )
        db.session.add(new_price)
        db.session.commit()
        return new_price


class OptionChainData(db.Model):
    __tablename__ = 'option_chain_data'
    
    id = db.Column(db.Integer, primary_key=True)
    underlying = db.Column(db.String(20), nullable=False, index=True)  # 'NIFTY' or 'BANKNIFTY'
    strike_price = db.Column(db.Float, nullable=False, index=True)
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    
    # CE (Call) Option Data
    ce_oi = db.Column(db.Integer, default=0)  # Open Interest
    ce_oi_change = db.Column(db.Integer, default=0)  # OI Change
    ce_volume = db.Column(db.Integer, default=0)
    ce_ltp = db.Column(db.Float, default=0.0)  # Last Traded Price
    ce_change = db.Column(db.Float, default=0.0)
    ce_change_percent = db.Column(db.Float, default=0.0)
    ce_iv = db.Column(db.Float, default=0.0)  # Implied Volatility
    
    # PE (Put) Option Data  
    pe_oi = db.Column(db.Integer, default=0)
    pe_oi_change = db.Column(db.Integer, default=0)
    pe_volume = db.Column(db.Integer, default=0)
    pe_ltp = db.Column(db.Float, default=0.0)
    pe_change = db.Column(db.Float, default=0.0)
    pe_change_percent = db.Column(db.Float, default=0.0)
    pe_iv = db.Column(db.Float, default=0.0)
    
    # Kite API Symbols and Instrument Tokens for Verification
    ce_strike_symbol = db.Column(db.String(100))  # CE Option Symbol (e.g., "NIFTY25DEC24100CE")
    ce_instrument_token = db.Column(db.String(50))  # CE Unique Instrument ID for Kite API
    pe_strike_symbol = db.Column(db.String(100))  # PE Option Symbol (e.g., "NIFTY25DEC24100PE") 
    pe_instrument_token = db.Column(db.String(50))  # PE Unique Instrument ID for Kite API
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_current_expiry = db.Column(db.Boolean, default=True, index=True)
    
    # Composite indexes for better query performance
    __table_args__ = (
        db.Index('idx_underlying_expiry_strike', 'underlying', 'expiry_date', 'strike_price'),
        db.Index('idx_underlying_current_expiry', 'underlying', 'is_current_expiry', 'timestamp'),
    )
    
    def __repr__(self):
        return f'<OptionChain {self.underlying} {self.strike_price} {self.expiry_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'underlying': self.underlying,
            'strike_price': self.strike_price,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d'),
            'ce_data': {
                'oi': self.ce_oi,
                'oi_change': self.ce_oi_change,
                'volume': self.ce_volume,
                'ltp': self.ce_ltp,
                'change': self.ce_change,
                'change_percent': self.ce_change_percent,
                'iv': self.ce_iv,
                'symbol': self.ce_strike_symbol,
                'instrument_token': self.ce_instrument_token
            },
            'pe_data': {
                'oi': self.pe_oi,
                'oi_change': self.pe_oi_change,
                'volume': self.pe_volume,
                'ltp': self.pe_ltp,
                'change': self.pe_change,
                'change_percent': self.pe_change_percent,
                'iv': self.pe_iv,
                'symbol': self.pe_strike_symbol,
                'instrument_token': self.pe_instrument_token
            },
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_current_expiry': self.is_current_expiry
        }
    
    @classmethod
    def get_latest_option_chain(cls, underlying, expiry_date=None, limit=50):
        """Get latest option chain data for given underlying"""
        query = cls.query.filter_by(underlying=underlying)
        
        if expiry_date:
            query = query.filter_by(expiry_date=expiry_date)
        else:
            # Get current expiry data
            query = query.filter_by(is_current_expiry=True)
        
        return query.order_by(cls.strike_price.asc()).limit(limit).all()
    
    @classmethod
    def get_oi_analysis(cls, underlying, expiry_date=None):
        """Get OI analysis data for trend calculation"""
        query = cls.query.filter_by(underlying=underlying)
        
        if expiry_date:
            query = query.filter_by(expiry_date=expiry_date)
        else:
            query = query.filter_by(is_current_expiry=True)
            
        # Get latest data for each strike
        subquery = db.session.query(
            cls.strike_price,
            db.func.max(cls.timestamp).label('max_timestamp')
        ).filter_by(underlying=underlying)
        
        if expiry_date:
            subquery = subquery.filter_by(expiry_date=expiry_date)
        else:
            subquery = subquery.filter_by(is_current_expiry=True)
            
        subquery = subquery.group_by(cls.strike_price).subquery()
        
        return query.join(
            subquery,
            db.and_(
                cls.strike_price == subquery.c.strike_price,
                cls.timestamp == subquery.c.max_timestamp
            )
        ).order_by(cls.strike_price.asc()).all()
    
    @classmethod
    def save_option_data(cls, option_data):
        """Save or update option chain data"""
        # Validate OI data - skip if both CE and PE OI are zero or None
        ce_oi = option_data.get('ce_oi', 0) or 0
        pe_oi = option_data.get('pe_oi', 0) or 0
        
        if ce_oi == 0 and pe_oi == 0:
            print(f"Skipping strike {option_data.get('strike_price')} - no meaningful OI data (CE_OI: {ce_oi}, PE_OI: {pe_oi})")
            return None
        
        existing = cls.query.filter_by(
            underlying=option_data['underlying'],
            strike_price=option_data['strike_price'],
            expiry_date=option_data['expiry_date']
        ).order_by(cls.timestamp.desc()).first()
        
        # Calculate OI changes by comparing with previous record
        ce_oi_change = 0
        pe_oi_change = 0
        
        # Calculate price changes by comparing with previous record
        ce_change = option_data.get('ce_change', 0.0) or 0.0
        pe_change = option_data.get('pe_change', 0.0) or 0.0
        ce_change_percent = option_data.get('ce_change_percent', 0.0) or 0.0
        pe_change_percent = option_data.get('pe_change_percent', 0.0) or 0.0
        
        if existing:
            ce_oi_change = ce_oi - existing.ce_oi
            pe_oi_change = pe_oi - existing.pe_oi
            
            # If API doesn't provide change data, calculate it ourselves
            ce_ltp = option_data.get('ce_ltp', 0.0) or 0.0
            pe_ltp = option_data.get('pe_ltp', 0.0) or 0.0
            
            if ce_change == 0.0 and existing.ce_ltp > 0:
                ce_change = ce_ltp - existing.ce_ltp
                if existing.ce_ltp > 0:
                    ce_change_percent = (ce_change / existing.ce_ltp) * 100
                    
            if pe_change == 0.0 and existing.pe_ltp > 0:
                pe_change = pe_ltp - existing.pe_ltp
                if existing.pe_ltp > 0:
                    pe_change_percent = (pe_change / existing.pe_ltp) * 100
        
        # Create new entry
        new_option = cls(
            underlying=option_data['underlying'],
            strike_price=option_data['strike_price'],
            expiry_date=option_data['expiry_date'],
            ce_oi=ce_oi,
            ce_oi_change=ce_oi_change,
            ce_volume=option_data.get('ce_volume', 0),
            ce_ltp=option_data.get('ce_ltp', 0.0),
            ce_change=ce_change,
            ce_change_percent=ce_change_percent,
            ce_iv=option_data.get('ce_iv', 0.0),
            pe_oi=pe_oi,
            pe_oi_change=pe_oi_change,
            pe_volume=option_data.get('pe_volume', 0),
            pe_ltp=option_data.get('pe_ltp', 0.0),
            pe_change=pe_change,
            pe_change_percent=pe_change_percent,
            pe_iv=option_data.get('pe_iv', 0.0),
            # New fields for Kite API verification
            ce_strike_symbol=option_data.get('ce_strike_symbol'),
            ce_instrument_token=option_data.get('ce_instrument_token'),
            pe_strike_symbol=option_data.get('pe_strike_symbol'),
            pe_instrument_token=option_data.get('pe_instrument_token'),
            is_current_expiry=option_data.get('is_current_expiry', True)
        )
        
        db.session.add(new_option)
        db.session.commit()
        return new_option
    
    @classmethod
    def get_top_oi_changes(cls, underlying="NIFTY", limit=10):
        """Get top OI changes (both positive and negative) for analysis"""
        from datetime import datetime, timedelta
        from sqlalchemy import or_
        
        # Get records from last 24 hours
        since_time = datetime.utcnow() - timedelta(hours=24)
        
        query = cls.query.filter(
            cls.underlying == underlying,
            cls.timestamp >= since_time,
            or_(cls.ce_oi_change != 0, cls.pe_oi_change != 0)
        )
        
        # Get top CE OI increases
        top_ce_increases = query.filter(cls.ce_oi_change > 0).order_by(cls.ce_oi_change.desc()).limit(limit).all()
        
        # Get top CE OI decreases
        top_ce_decreases = query.filter(cls.ce_oi_change < 0).order_by(cls.ce_oi_change.asc()).limit(limit).all()
        
        # Get top PE OI increases
        top_pe_increases = query.filter(cls.pe_oi_change > 0).order_by(cls.pe_oi_change.desc()).limit(limit).all()
        
        # Get top PE OI decreases
        top_pe_decreases = query.filter(cls.pe_oi_change < 0).order_by(cls.pe_oi_change.asc()).limit(limit).all()
        
        return {
            'ce_increases': top_ce_increases,
            'ce_decreases': top_ce_decreases,
            'pe_increases': top_pe_increases,
            'pe_decreases': top_pe_decreases
        }
    
    @classmethod
    def get_oi_change_summary(cls, underlying="NIFTY"):
        """Get summary of OI changes for dashboard display"""
        from datetime import datetime, timedelta
        from sqlalchemy import or_, func
        
        # Get records from last 6 hours for more recent activity
        since_time = datetime.utcnow() - timedelta(hours=6)
        
        query = cls.query.filter(
            cls.underlying == underlying,
            cls.timestamp >= since_time,
            or_(cls.ce_oi_change != 0, cls.pe_oi_change != 0)
        )
        
        # Get top 3 CE and PE changes
        top_ce = query.filter(cls.ce_oi_change != 0).order_by(
            func.abs(cls.ce_oi_change).desc()
        ).limit(3).all()
        
        top_pe = query.filter(cls.pe_oi_change != 0).order_by(
            func.abs(cls.pe_oi_change).desc()
        ).limit(3).all()
        
        return {
            'top_ce_changes': top_ce,
            'top_pe_changes': top_pe,
            'last_updated': datetime.utcnow()
        }


class MarketTrend(db.Model):
    __tablename__ = 'market_trends'
    
    id = db.Column(db.Integer, primary_key=True)
    underlying = db.Column(db.String(20), nullable=False, index=True)
    expiry_date = db.Column(db.Date, nullable=False)
    
    # Market sentiment indicators
    total_ce_oi = db.Column(db.BigInteger, default=0)
    total_pe_oi = db.Column(db.BigInteger, default=0)
    total_ce_oi_change = db.Column(db.BigInteger, default=0)
    total_pe_oi_change = db.Column(db.BigInteger, default=0)
    
    # Put-Call Ratio
    pcr_oi = db.Column(db.Float, default=0.0)  # PE OI / CE OI
    pcr_volume = db.Column(db.Float, default=0.0)  # PE Volume / CE Volume
    
    # Trend indicators
    bullish_percentage = db.Column(db.Float, default=0.0)
    bearish_percentage = db.Column(db.Float, default=0.0)
    neutral_percentage = db.Column(db.Float, default=0.0)
    
    # Max Pain and Support/Resistance
    max_pain_strike = db.Column(db.Float, default=0.0)
    key_support_level = db.Column(db.Float, default=0.0)
    key_resistance_level = db.Column(db.Float, default=0.0)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<MarketTrend {self.underlying} {self.expiry_date} - {self.bullish_percentage}% Bull>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'underlying': self.underlying,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d'),
            'total_ce_oi': self.total_ce_oi,
            'total_pe_oi': self.total_pe_oi,
            'total_ce_oi_change': self.total_ce_oi_change,
            'total_pe_oi_change': self.total_pe_oi_change,
            'pcr_oi': self.pcr_oi,
            'pcr_volume': self.pcr_volume,
            'bullish_percentage': self.bullish_percentage,
            'bearish_percentage': self.bearish_percentage,
            'neutral_percentage': self.neutral_percentage,
            'max_pain_strike': self.max_pain_strike,
            'key_support_level': self.key_support_level,
            'key_resistance_level': self.key_resistance_level,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @classmethod
    def get_latest_trend(cls, underlying):
        return cls.query.filter_by(underlying=underlying).order_by(cls.timestamp.desc()).first()
    
    @classmethod
    def save_trend_data(cls, trend_data):
        new_trend = cls(
            underlying=trend_data['underlying'],
            expiry_date=trend_data['expiry_date'],
            total_ce_oi=trend_data.get('total_ce_oi', 0),
            total_pe_oi=trend_data.get('total_pe_oi', 0),
            total_ce_oi_change=trend_data.get('total_ce_oi_change', 0),
            total_pe_oi_change=trend_data.get('total_pe_oi_change', 0),
            pcr_oi=trend_data.get('pcr_oi', 0.0),
            pcr_volume=trend_data.get('pcr_volume', 0.0),
            bullish_percentage=trend_data.get('bullish_percentage', 0.0),
            bearish_percentage=trend_data.get('bearish_percentage', 0.0),
            neutral_percentage=trend_data.get('neutral_percentage', 0.0),
            max_pain_strike=trend_data.get('max_pain_strike', 0.0),
            key_support_level=trend_data.get('key_support_level', 0.0),
            key_resistance_level=trend_data.get('key_resistance_level', 0.0)
        )
        
        db.session.add(new_trend)
        db.session.commit()
        return new_trend
