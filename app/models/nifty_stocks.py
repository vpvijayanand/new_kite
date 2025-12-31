from app import db
from datetime import datetime, date
from app.utils.datetime_utils import utc_to_ist

class NiftyStock(db.Model):
    __tablename__ = 'nifty_stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True, index=True)
    company_name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    nifty_weightage = db.Column(db.Float, nullable=False)  # Weight percentage in NIFTY 50
    instrument_token = db.Column(db.Integer, nullable=True)  # For API calls
    
    # Current trading data
    current_price = db.Column(db.Float, default=0.0)
    opening_price = db.Column(db.Float, default=0.0)  # 9:20 AM opening price
    price_change = db.Column(db.Float, default=0.0)  # Absolute change from opening
    price_change_percent = db.Column(db.Float, default=0.0)  # Percentage change
    nifty_influence = db.Column(db.Float, default=0.0)  # Impact on NIFTY (positive/negative)
    
    volume = db.Column(db.BigInteger, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    trading_date = db.Column(db.Date, default=date.today, index=True)
    
    def __repr__(self):
        return f'<NiftyStock {self.symbol}: {self.current_price}>'
    
    @classmethod
    def initialize_nifty_stocks(cls):
        """Initialize NIFTY 50 stocks with static data"""
        nifty_50_data = [
            # Symbol, Company Name, Sector, Weight %
            ('RELIANCE', 'Reliance Industries Ltd', 'Oil & Gas / Energy', 7.77),
            ('HDFCBANK', 'HDFC Bank Ltd', 'Banking & Financial Services', 12.70),
            ('ICICIBANK', 'ICICI Bank Ltd', 'Banking & Financial Services', 8.52),
            ('INFY', 'Infosys Ltd', 'Information Technology', 6.38),
            ('TCS', 'Tata Consultancy Services Ltd', 'Information Technology', 3.94),
            ('BHARTIARTL', 'Bharti Airtel Ltd', 'Telecom', 4.01),
            ('ITC', 'ITC Ltd', 'FMCG', 4.24),
            ('LT', 'Larsen & Toubro Ltd', 'Infrastructure / Engineering', 4.00),
            ('KOTAKBANK', 'Kotak Mahindra Bank Ltd', 'Banking', 2.47),
            ('HINDUNILVR', 'Hindustan Unilever Ltd', 'FMCG', 1.95),
            ('SBIN', 'State Bank of India', 'Banking', 2.88),
            ('BAJFINANCE', 'Bajaj Finance Ltd', 'NBFC / Financial Services', 1.80),
            ('HCLTECH', 'HCL Technologies Ltd', 'IT Services', 1.91),
            ('MARUTI', 'Maruti Suzuki India Ltd', 'Automobiles', 1.35),
            ('M&M', 'Mahindra & Mahindra Ltd', 'Automobiles', 2.51),
            ('ASIANPAINT', 'Asian Paints Ltd', 'Consumer / Paints', 0.97),
            ('SUNPHARMA', 'Sun Pharmaceutical Industries Ltd', 'Pharmaceuticals', 1.92),
            ('TATAMOTORS', 'Tata Motors Ltd', 'Automobiles', 1.46),
            ('ULTRACEMCO', 'UltraTech Cement Ltd', 'Cement', 1.23),
            ('AXISBANK', 'Axis Bank Ltd', 'Banking', 2.86),
            ('JSWSTEEL', 'JSW Steel Ltd', 'Metals & Mining', 0.81),
            ('POWERGRID', 'Power Grid Corporation of India Ltd', 'Power / Utilities', 1.32),
            ('NTPC', 'NTPC Ltd', 'Power / Utilities', 1.49),
            ('TECHM', 'Tech Mahindra Ltd', 'IT Services', 1.02),
            ('ADANIPORTS', 'Adani Ports and Special Economic Zone Ltd', 'Ports / Infrastructure', 0.85),
            ('COALINDIA', 'Coal India Ltd', 'Mining / Energy', 0.82),
            ('ONGC', 'Oil and Natural Gas Corporation Ltd', 'Oil & Gas / Energy', 0.87),
            ('HINDALCO', 'Hindalco Industries Ltd', 'Metals / Aluminium', 0.82),
            ('BAJAJFINSV', 'Bajaj Finserv Ltd', 'Financial Services', 0.81),
            ('BAJAJ-AUTO', 'Bajaj Auto Ltd', 'Automobiles', 0.92),
            ('NESTLEIND', 'Nestle India Ltd', 'FMCG', 0.73),
            ('CIPLA', 'Cipla Ltd', 'Pharmaceuticals', 0.79),
            ('DRREDDY', 'Dr. Reddys Laboratories Ltd', 'Pharmaceuticals', 0.80),
            ('TITAN', 'Titan Company Ltd', 'Consumer Durables / Jewellery', 1.27),
            ('TRENT', 'Trent Ltd', 'Retail', 1.49),
            ('SBILIFE', 'SBI Life Insurance Company Ltd', 'Insurance / Financial Services', 0.59),
            ('TATASTEEL', 'Tata Steel Ltd', 'Metals / Steel', 1.08),
            ('WIPRO', 'Wipro Ltd', 'Information Technology', 0.81),
            ('GRASIM', 'Grasim Industries Ltd', 'Diversified / Cement', 0.85),
            ('ADANIENT', 'Adani Enterprises Ltd', 'Conglomerate / Mining', 0.59),
            ('TATACONSUM', 'Tata Consumer Products Ltd', 'FMCG / Beverages', 0.56),
            ('JIOFIN', 'Jio Financial Services Ltd', 'Financial Services', 0.59),
            ('INDIGO', 'InterGlobe Aviation Ltd', 'Airlines / Aviation', 0.59),
            ('APOLLOHOSP', 'Apollo Hospitals Enterprise Ltd', 'Hospitals / Healthcare', 0.70),
            ('BEL', 'Bharat Electronics Ltd', 'Defence Electronics', 0.99),
            ('EICHERMOT', 'Eicher Motors Ltd', 'Automobiles / Premium Bikes', 0.62),
            ('SHIRAMFIN', 'Shriram Finance Ltd', 'NBFC', 0.76),
            ('TMPV', 'Tata Motors Ltd (DVR)', 'Automobiles (Tata Motors DVR)', 0.59),
            ('MAXHEALTH', 'Max Healthcare Institute Ltd', 'Healthcare / Hospitals', 0.59),
        ]
        
        for symbol, name, sector, weight in nifty_50_data:
            existing = cls.query.filter_by(symbol=symbol).first()
            if not existing:
                stock = cls(
                    symbol=symbol,
                    company_name=name,
                    sector=sector,
                    nifty_weightage=weight
                )
                db.session.add(stock)
        
        db.session.commit()
        print(f"Initialized {len(nifty_50_data)} NIFTY 50 stocks")
    
    @classmethod
    def update_stock_price(cls, symbol, price_data):
        """Update stock price and calculate changes"""
        from app.utils.datetime_utils import is_market_hours
        
        # Only update during market hours
        if not is_market_hours():
            print(f"Skipping {symbol} price update - outside market hours")
            return None
        
        stock = cls.query.filter_by(symbol=symbol).first()
        if not stock:
            print(f"Stock {symbol} not found in NIFTY 50 list")
            return None
        
        current_price = float(price_data.get('last_price', 0))
        
        # Set opening price (9:20 AM) if not set for today
        today = date.today()
        if stock.trading_date != today or stock.opening_price == 0:
            stock.opening_price = current_price
            stock.trading_date = today
            stock.price_change = 0
            stock.price_change_percent = 0
            stock.nifty_influence = 0
        else:
            # Calculate changes from opening price (9:20 AM)
            stock.price_change = current_price - stock.opening_price
            if stock.opening_price > 0:
                stock.price_change_percent = (stock.price_change / stock.opening_price) * 100
            else:
                stock.price_change_percent = 0
            
            # Calculate influence on NIFTY 50 index
            # Formula: (Stock Change % * Weight in NIFTY) / 100
            stock.nifty_influence = (stock.price_change_percent * stock.nifty_weightage) / 100
        
        stock.current_price = current_price
        stock.volume = int(price_data.get('volume', 0))
        stock.last_updated = datetime.utcnow()
        
        db.session.commit()
        return stock
    
    @classmethod
    def get_nifty_stocks_summary(cls):
        """Get summary of all NIFTY 50 stocks with today's performance"""
        today = date.today()
        stocks = cls.query.filter_by(trading_date=today).order_by(cls.nifty_influence.desc()).all()
        
        if not stocks:
            # If no data for today, get all stocks
            stocks = cls.query.order_by(cls.nifty_weightage.desc()).all()
        
        # Calculate total NIFTY influence
        total_positive_influence = sum(s.nifty_influence for s in stocks if s.nifty_influence > 0)
        total_negative_influence = sum(s.nifty_influence for s in stocks if s.nifty_influence < 0)
        net_nifty_influence = total_positive_influence + total_negative_influence
        
        return {
            'stocks': stocks,
            'total_positive_influence': round(total_positive_influence, 4),
            'total_negative_influence': round(total_negative_influence, 4),
            'net_nifty_influence': round(net_nifty_influence, 4),
            'total_stocks': len(stocks),
            'gainers': len([s for s in stocks if s.price_change > 0]),
            'losers': len([s for s in stocks if s.price_change < 0]),
            'unchanged': len([s for s in stocks if s.price_change == 0])
        }
    
    def to_dict(self):
        """Convert stock data to dictionary for API responses"""
        return {
            'symbol': self.symbol,
            'company_name': self.company_name,
            'sector': self.sector,
            'nifty_weightage': self.nifty_weightage,
            'current_price': self.current_price,
            'price_9_20_am': self.opening_price,  # Map opening_price to price_9_20_am for frontend
            'price_change': round(self.price_change, 2) if self.price_change else 0,
            'change_percent': round(self.price_change_percent, 2) if self.price_change_percent else 0,
            'nifty_influence': round(self.nifty_influence, 4) if self.nifty_influence else 0,
            'volume': self.volume if self.volume else 0,
            'last_updated': self.last_updated.strftime('%H:%M:%S') if self.last_updated else 'N/A'
        }
