from app.models.nifty_price import NiftyPrice
from app.models.banknifty_price import BankNiftyPrice, OptionChainData, MarketTrend
from app.services.kite_service import KiteService
from app import db
from datetime import datetime, timedelta

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
    
    def fetch_and_save_banknifty_price(self):
        try:
            price_data = self.kite_service.get_banknifty_price()
            
            if price_data:
                BankNiftyPrice.save_price(price_data)
                return price_data
            return None
        except Exception as e:
            print(f"Error in fetch_and_save_banknifty_price: {str(e)}")
            return None
    
    def fetch_and_save_option_chain(self, underlying="NIFTY"):
        """Fetch and save option chain data for given underlying - real data only"""
        try:
            option_chain_data = self.kite_service.get_option_chain_data(underlying)
            
            if option_chain_data:
                saved_count = 0
                for option_data in option_chain_data:
                    OptionChainData.save_option_data(option_data)
                    saved_count += 1
                
                # Calculate and save market trend
                trend_data = self.kite_service.calculate_market_trend(option_chain_data, underlying)
                if trend_data:
                    MarketTrend.save_trend_data(trend_data)
                
                print(f"Saved {saved_count} option chain records for {underlying}")
                return option_chain_data
            else:
                print(f"No API data available for {underlying}")
                return None
        except Exception as e:
            print(f"Error in fetch_and_save_option_chain for {underlying}: {str(e)}")
            return None
    

    
    def get_latest_prices(self, limit=100):
        return NiftyPrice.get_latest_prices(limit)
    
    def get_latest_banknifty_prices(self, limit=100):
        return BankNiftyPrice.get_latest_prices(limit)
    
    def get_price_history(self, hours=24):
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        prices = NiftyPrice.query.filter(
            NiftyPrice.timestamp >= cutoff_time
        ).order_by(NiftyPrice.timestamp.desc()).all()
        
        return [price.to_dict() for price in prices]
    
    def get_banknifty_price_history(self, hours=24):
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        prices = BankNiftyPrice.query.filter(
            BankNiftyPrice.timestamp >= cutoff_time
        ).order_by(BankNiftyPrice.timestamp.desc()).all()
        
        return [price.to_dict() for price in prices]
    
    def get_current_option_chain(self, underlying="NIFTY", limit=50):
        """Get current option chain data for analysis"""
        return OptionChainData.get_latest_option_chain(underlying, limit=limit)
    
    def get_oi_analysis_data(self, underlying="NIFTY"):
        """Get detailed OI analysis data for divergence analysis"""
        return OptionChainData.get_oi_analysis(underlying)
    
    def get_market_trend(self, underlying="NIFTY"):
        """Get current market trend analysis"""
        return MarketTrend.get_latest_trend(underlying)
    
    def get_dashboard_data(self):
        """Get comprehensive dashboard data"""
        try:
            # Get latest prices
            nifty_price = None
            banknifty_price = None
            
            latest_nifty = NiftyPrice.query.order_by(NiftyPrice.timestamp.desc()).first()
            if latest_nifty:
                nifty_price = latest_nifty.to_dict()
            
            latest_banknifty = BankNiftyPrice.query.order_by(BankNiftyPrice.timestamp.desc()).first()
            if latest_banknifty:
                banknifty_price = latest_banknifty.to_dict()
            
            # Get market trends
            nifty_trend = self.get_market_trend("NIFTY")
            banknifty_trend = self.get_market_trend("BANKNIFTY")
            
            # Get option chain summaries
            nifty_options = self.get_current_option_chain("NIFTY", limit=10)
            banknifty_options = self.get_current_option_chain("BANKNIFTY", limit=10)
            
            return {
                'nifty_price': nifty_price,
                'banknifty_price': banknifty_price,
                'nifty_trend': nifty_trend.to_dict() if nifty_trend else None,
                'banknifty_trend': banknifty_trend.to_dict() if banknifty_trend else None,
                'nifty_options_summary': [opt.to_dict() for opt in nifty_options[:5]],
                'banknifty_options_summary': [opt.to_dict() for opt in banknifty_options[:5]]
            }
        except Exception as e:
            print(f"Error getting dashboard data: {str(e)}")
            return {
                'nifty_price': None,
                'banknifty_price': None,
                'nifty_trend': None,
                'banknifty_trend': None,
                'nifty_options_summary': [],
                'banknifty_options_summary': []
            }