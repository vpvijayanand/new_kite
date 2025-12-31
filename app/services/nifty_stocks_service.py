from app.models.nifty_stocks import NiftyStock
from app.services.kite_service import KiteService
from app import db
import logging

class NiftyStocksService:
    def __init__(self):
        self.kite_service = KiteService()
        self.logger = logging.getLogger(__name__)
    
    def initialize_stocks(self):
        """Initialize NIFTY 50 stocks in database"""
        try:
            NiftyStock.initialize_nifty_stocks()
            self.logger.info("NIFTY 50 stocks initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing NIFTY 50 stocks: {e}")
            return False
    
    def update_all_stock_prices(self):
        """Fetch and update prices for all NIFTY 50 stocks"""
        try:
            stocks = NiftyStock.query.all()
            updated_count = 0
            
            for stock in stocks:
                try:
                    # Get stock price data from Kite API
                    price_data = self.kite_service.get_stock_price(stock.symbol)
                    
                    if price_data:
                        updated_stock = NiftyStock.update_stock_price(stock.symbol, price_data)
                        if updated_stock:
                            updated_count += 1
                            self.logger.debug(f"Updated {stock.symbol}: ₹{price_data.get('last_price', 0)}")
                    
                except Exception as e:
                    self.logger.error(f"Error updating {stock.symbol}: {e}")
                    continue
            
            self.logger.info(f"Updated {updated_count} NIFTY 50 stocks")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error updating NIFTY 50 stock prices: {e}")
            return 0
    
    def update_single_stock(self, symbol):
        """Update price for a single stock"""
        try:
            price_data = self.kite_service.get_stock_price(symbol)
            
            if price_data:
                updated_stock = NiftyStock.update_stock_price(symbol, price_data)
                if updated_stock:
                    self.logger.info(f"Updated {symbol}: ₹{price_data.get('last_price', 0)}")
                    return updated_stock
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating single stock {symbol}: {e}")
            return None
    
    def get_nifty_stocks_data(self):
        """Get all NIFTY 50 stocks data for display"""
        try:
            return NiftyStock.get_nifty_stocks_summary()
        except Exception as e:
            self.logger.error(f"Error getting NIFTY stocks data: {e}")
            return {
                'stocks': [],
                'total_positive_influence': 0,
                'total_negative_influence': 0,
                'net_nifty_influence': 0,
                'total_stocks': 0,
                'gainers': 0,
                'losers': 0,
                'unchanged': 0
            }
    
    def get_top_performers(self, limit=5):
        """Get top gaining and losing stocks"""
        try:
            from datetime import date
            today = date.today()
            
            # Top gainers by percentage change
            gainers = NiftyStock.query.filter(
                NiftyStock.trading_date == today,
                NiftyStock.price_change_percent > 0
            ).order_by(NiftyStock.price_change_percent.desc()).limit(limit).all()
            
            # Top losers by percentage change
            losers = NiftyStock.query.filter(
                NiftyStock.trading_date == today,
                NiftyStock.price_change_percent < 0
            ).order_by(NiftyStock.price_change_percent.asc()).limit(limit).all()
            
            # Top NIFTY influencers (positive)
            positive_influencers = NiftyStock.query.filter(
                NiftyStock.trading_date == today,
                NiftyStock.nifty_influence > 0
            ).order_by(NiftyStock.nifty_influence.desc()).limit(limit).all()
            
            # Top NIFTY drag (negative)
            negative_influencers = NiftyStock.query.filter(
                NiftyStock.trading_date == today,
                NiftyStock.nifty_influence < 0
            ).order_by(NiftyStock.nifty_influence.asc()).limit(limit).all()
            
            return {
                'top_gainers': [stock.to_dict() for stock in gainers],
                'top_losers': [stock.to_dict() for stock in losers],
                'positive_influencers': [stock.to_dict() for stock in positive_influencers],
                'negative_influencers': [stock.to_dict() for stock in negative_influencers]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return {
                'top_gainers': [],
                'top_losers': [],
                'positive_influencers': [],
                'negative_influencers': []
            }
    
    def get_sector_performance(self):
        """Get sector-wise performance summary"""
        try:
            from datetime import date
            from sqlalchemy import func
            
            today = date.today()
            
            sector_data = db.session.query(
                NiftyStock.sector,
                func.count(NiftyStock.id).label('stock_count'),
                func.avg(NiftyStock.price_change_percent).label('avg_change'),
                func.sum(NiftyStock.nifty_influence).label('sector_influence'),
                func.sum(NiftyStock.nifty_weightage).label('sector_weight')
            ).filter(
                NiftyStock.trading_date == today
            ).group_by(NiftyStock.sector).order_by(
                func.sum(NiftyStock.nifty_influence).desc()
            ).all()
            
            sectors = []
            for sector, count, avg_change, influence, weight in sector_data:
                sectors.append({
                    'sector': sector,
                    'stock_count': count,
                    'avg_change': round(avg_change or 0, 2),
                    'total_influence': round(influence or 0, 4),
                    'sector_weight': round(weight or 0, 2)
                })
            
            return sectors
            
        except Exception as e:
            self.logger.error(f"Error getting sector performance: {e}")
            return []
