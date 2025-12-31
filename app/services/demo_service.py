# Demo Service - Sample data for testing without Kite API
import datetime
from typing import Dict, List
import random

class DemoService:
    """Provides sample data for testing the option chain functionality"""
    
    @staticmethod
    def get_demo_nifty_price():
        """Returns demo NIFTY price data"""
        return {
            "symbol": "NIFTY 50",
            "price": 24150.50,
            "change": 125.30,
            "change_percent": 0.52,
            "timestamp": datetime.datetime.now()
        }
    
    @staticmethod
    def get_demo_banknifty_price():
        """Returns demo BankNifty price data"""
        return {
            "symbol": "BANKNIFTY",
            "price": 52450.75,
            "change": -89.25,
            "change_percent": -0.17,
            "timestamp": datetime.datetime.now()
        }
    
    @staticmethod
    def get_demo_expiry_dates():
        """Returns current and next expiry dates from settings or defaults"""
        try:
            from app.models.expiry_settings import ExpirySettings
            
            # Try to get expiry from settings
            nifty_expiry = ExpirySettings.get_current_expiry('NIFTY')
            banknifty_expiry = ExpirySettings.get_current_expiry('BANKNIFTY')
            
            return {
                'current_expiry': nifty_expiry,
                'next_expiry': nifty_expiry + datetime.timedelta(days=7),
                'nifty_expiry': nifty_expiry,
                'banknifty_expiry': banknifty_expiry
            }
        except:
            # Fallback to default calculation
            today = datetime.date.today()
            days_ahead = 3 - today.weekday()  # 3 = Thursday
            if days_ahead <= 0:  # Thursday already happened this week
                days_ahead += 7
            
            current_expiry = today + datetime.timedelta(days=days_ahead)
            next_expiry = current_expiry + datetime.timedelta(days=7)
            
            return {
                'current_expiry': current_expiry,
                'next_expiry': next_expiry,
                'nifty_expiry': current_expiry,
                'banknifty_expiry': current_expiry
            }
    
    @staticmethod
    def get_demo_option_chain(underlying: str):
        """
        Returns demo option chain data for NIFTY or BANKNIFTY
        
        Logic for Strike Selection:
        - NIFTY: 50-point intervals (23900, 23950, 24000, etc.)
        - BANKNIFTY: 100-point intervals (52200, 52300, 52400, etc.)
        - Range: ±300 points from current price
        """
        if underlying == "NIFTY":
            current_price = 24150.50
            interval = 50
        else:  # BANKNIFTY
            current_price = 52450.75
            interval = 100
        
        # Calculate ATM strike (closest to current price)
        atm_strike = round(current_price / interval) * interval
        
        # Generate strikes in ±300 point range
        strikes = []
        for i in range(-6, 7):  # -300 to +300 in intervals
            strike = atm_strike + (i * interval)
            strikes.append(strike)
        
        # Get current expiry based on underlying - use custom settings if available
        try:
            from app.models.expiry_settings import ExpirySettings
            current_expiry = ExpirySettings.get_current_expiry(underlying)
        except:
            # Fallback to demo dates
            expiry_dates = DemoService.get_demo_expiry_dates()
            if underlying == "NIFTY":
                current_expiry = expiry_dates['nifty_expiry']
            else:  # BANKNIFTY
                current_expiry = expiry_dates['banknifty_expiry']
        
        option_chain = []
        for strike in strikes:
            # Generate realistic option data
            distance_from_atm = abs(strike - current_price)
            
            # Call options (CE)
            if strike < current_price:  # ITM calls
                ce_ltp = max(1, current_price - strike + random.uniform(-20, 20))
                ce_iv = random.uniform(12, 18)
            else:  # OTM calls
                ce_ltp = max(0.05, random.uniform(0.5, 50))
                ce_iv = random.uniform(15, 25)
            
            # Put options (PE)  
            if strike > current_price:  # ITM puts
                pe_ltp = max(1, strike - current_price + random.uniform(-20, 20))
                pe_iv = random.uniform(12, 18)
            else:  # OTM puts
                pe_ltp = max(0.05, random.uniform(0.5, 50))
                pe_iv = random.uniform(15, 25)
            
            # Generate OI data (higher for ATM strikes)
            base_oi = max(10000, 50000 - (distance_from_atm * 100))
            ce_oi = int(base_oi * random.uniform(0.8, 1.2))
            pe_oi = int(base_oi * random.uniform(0.8, 1.2))
            
            # OI changes (simulate market activity)
            ce_oi_change = int(ce_oi * random.uniform(-0.1, 0.1))
            pe_oi_change = int(pe_oi * random.uniform(-0.1, 0.1))
            
            # Generate realistic Kite API symbols and instrument tokens
            expiry_str = current_expiry.strftime('%y%b%d').upper()  # e.g., "25DEC02"
            
            # Generate option symbols (Kite format)
            ce_symbol = f"{underlying}{expiry_str}{strike}CE"  # e.g., "NIFTY25DEC0224100CE"
            pe_symbol = f"{underlying}{expiry_str}{strike}PE"  # e.g., "NIFTY25DEC0224100PE"
            
            # Generate realistic instrument tokens (Kite uses numeric IDs)
            base_token = 256265 if underlying == "NIFTY" else 260105  # Real NIFTY/BANKNIFTY tokens
            ce_token = str(base_token + int(strike) * 100 + 1)  # CE token
            pe_token = str(base_token + int(strike) * 100 + 2)  # PE token

            option_data = {
                'strike_price': strike,
                'expiry_date': current_expiry,
                'underlying': underlying,
                
                # Call data
                'ce_oi': ce_oi,
                'ce_oi_change': ce_oi_change, 
                'ce_volume': int(ce_oi * random.uniform(0.1, 0.3)),
                'ce_ltp': round(ce_ltp, 2),
                'ce_change': round(ce_ltp * random.uniform(-0.1, 0.1), 2),
                'ce_iv': round(ce_iv, 2),
                'ce_strike_symbol': ce_symbol,
                'ce_instrument_token': ce_token,
                
                # Put data
                'pe_oi': pe_oi,
                'pe_oi_change': pe_oi_change,
                'pe_volume': int(pe_oi * random.uniform(0.1, 0.3)), 
                'pe_ltp': round(pe_ltp, 2),
                'pe_change': round(pe_ltp * random.uniform(-0.1, 0.1), 2),
                'pe_iv': round(pe_iv, 2),
                'pe_strike_symbol': pe_symbol,
                'pe_instrument_token': pe_token,
                
                'timestamp': datetime.datetime.now()
            }
            
            option_chain.append(option_data)
        
        return option_chain
    
    @staticmethod
    def get_demo_market_trend(underlying: str):
        """
        Calculate market sentiment from option chain data
        
        Logic:
        1. Total CE OI vs PE OI (Put-Call Ratio)
        2. OI Changes - More PE addition = Bullish, More CE addition = Bearish
        3. Max Pain - Strike with highest combined OI
        4. Support/Resistance from OI distribution
        """
        option_chain = DemoService.get_demo_option_chain(underlying)
        
        total_ce_oi = sum(opt['ce_oi'] for opt in option_chain)
        total_pe_oi = sum(opt['pe_oi'] for opt in option_chain)
        total_ce_oi_change = sum(opt['ce_oi_change'] for opt in option_chain)
        total_pe_oi_change = sum(opt['pe_oi_change'] for opt in option_chain)
        
        # Calculate Put-Call Ratio
        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
        
        # Calculate sentiment based on OI changes
        total_oi_change = abs(total_ce_oi_change) + abs(total_pe_oi_change)
        
        if total_oi_change > 0:
            if total_pe_oi_change > total_ce_oi_change:
                # More put addition = bullish (hedging/support buying)
                bullish_percentage = min(80, 50 + (abs(total_pe_oi_change) / total_oi_change * 30))
                bearish_percentage = 100 - bullish_percentage
            else:
                # More call addition = bearish (covering/resistance selling)
                bearish_percentage = min(80, 50 + (abs(total_ce_oi_change) / total_oi_change * 30))
                bullish_percentage = 100 - bearish_percentage
        else:
            bullish_percentage = 50
            bearish_percentage = 50
        
        # Find Max Pain (strike with highest combined OI)
        max_pain_strike = max(option_chain, 
                            key=lambda x: x['ce_oi'] + x['pe_oi'])['strike_price']
        
        # Find support and resistance levels
        sorted_strikes = sorted(option_chain, 
                              key=lambda x: x['ce_oi'] + x['pe_oi'], 
                              reverse=True)
        
        support_level = min([strike['strike_price'] for strike in sorted_strikes[:3]])
        resistance_level = max([strike['strike_price'] for strike in sorted_strikes[:3]])
        
        # Get correct expiry for trend calculation
        try:
            from app.models.expiry_settings import ExpirySettings
            current_expiry = ExpirySettings.get_current_expiry(underlying)
        except:
            expiry_dates = DemoService.get_demo_expiry_dates()
            current_expiry = expiry_dates['nifty_expiry'] if underlying == "NIFTY" else expiry_dates['banknifty_expiry']
        
        return {
            'underlying': underlying,
            'expiry_date': current_expiry,
            'bullish_percentage': round(bullish_percentage, 1),
            'bearish_percentage': round(bearish_percentage, 1),
            'pcr': pcr,
            'max_pain_strike': max_pain_strike,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'total_ce_oi': total_ce_oi,
            'total_pe_oi': total_pe_oi,
            'total_ce_oi_change': total_ce_oi_change,
            'total_pe_oi_change': total_pe_oi_change,
            'timestamp': datetime.datetime.now()
        }
