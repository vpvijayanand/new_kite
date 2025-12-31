from kiteconnect import KiteConnect
from flask import current_app
from app.utils.token_manager import TokenManager
import logging
import json
import os
import time
from datetime import datetime, timedelta
import calendar

class KiteService:
    def __init__(self):
        self.api_key = current_app.config['KITE_API_KEY']
        self.api_secret = current_app.config['KITE_API_SECRET']
        self.kite = KiteConnect(api_key=self.api_key)
        self.token_manager = TokenManager(current_app.config['TOKEN_FILE_PATH'])
        self.api_logger = None
        self.setup_api_logging()
    
    def setup_api_logging(self):
        """Setup logging for API requests and responses"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        self.api_logger = logging.getLogger('kite_api')
        self.api_logger.setLevel(logging.DEBUG)
        
        if not self.api_logger.handlers:
            log_file = os.path.join(log_dir, 'kite_api_requests.log')
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.api_logger.addHandler(handler)
    
    def log_api_call(self, method, endpoint, params=None, response_data=None, success=True, error=None):
        """Unified API logging method"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'method': method,
                'endpoint': endpoint,
                'params': params,
                'success': success
            }
            
            if success and response_data:
                if isinstance(response_data, dict):
                    log_data['response_keys'] = list(response_data.keys())
                    log_data['response_size'] = len(str(response_data))
                log_data['response_preview'] = str(response_data)[:500]
            elif error:
                log_data['error'] = str(error)
            
            self.api_logger.info(f"API_CALL: {json.dumps(log_data, indent=2)}")
        except Exception as e:
            self.api_logger.error(f"Error logging API call: {str(e)}")
    
    def get_login_url(self):
        return self.kite.login_url()
    
    def generate_session(self, request_token):
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data['access_token']
            self.token_manager.save_token(access_token, data.get('user_id'))
            self.kite.set_access_token(access_token)
            return access_token
        except Exception as e:
            raise Exception(f"Error generating session: {str(e)}")
    
    def get_kite_instance(self):
        access_token = self.token_manager.get_token()
        if not access_token:
            raise Exception("No access token found. Please login first.")
        self.kite.set_access_token(access_token)
        return self.kite
    
    def _get_index_quote(self, symbol_name, display_name):
        """Generic method to fetch index quotes"""
        try:
            kite = self.get_kite_instance()
            symbol = f"NSE:{symbol_name}"
            
            quote = kite.quote([symbol])
            self.log_api_call('GET', 'quote', [symbol], quote)
            
            if symbol in quote:
                data = quote[symbol]
                ohlc = data.get('ohlc', {})
                return {
                    'symbol': display_name,
                    'price': data['last_price'],
                    'high': ohlc.get('high', data['last_price']),
                    'low': ohlc.get('low', data['last_price']),
                    'open': ohlc.get('open', data['last_price']),
                    'close': ohlc.get('close', data['last_price']),
                    'change': data.get('change', 0),
                    'change_percent': data.get('change_percent', 0)
                }
            return None
        except Exception as e:
            self.log_api_call('GET', 'quote', [symbol], error=str(e), success=False)
            raise Exception(f"Error fetching {display_name} price: {str(e)}")
    
    def get_nifty_price(self):
        return self._get_index_quote('NIFTY 50', 'NIFTY 50')
    
    def get_banknifty_price(self):
        return self._get_index_quote('NIFTY BANK', 'NIFTY BANK')
    
    def _get_current_expiry(self, underlying):
        """Calculate current weekly expiry date"""
        try:
            from app.models.expiry_settings import ExpirySettings
            return ExpirySettings.get_current_expiry(underlying)
        except:
            today = datetime.now().date()
            days_ahead = 3 - today.weekday()  # Thursday
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days_ahead)
    
    def _generate_option_symbol(self, underlying, expiry_date, strike, option_type):
        """Generate option symbol in correct format"""
        month_name = expiry_date.strftime('%b').upper()[:3]
        year = expiry_date.strftime('%y')
        
        if underlying == "NIFTY":
            return f"NFO:NIFTY{year}{month_name}{int(strike)}{option_type}"
        else:  # BANKNIFTY
            return f"NFO:BANKNIFTY{year}{month_name}{int(strike)}{option_type}"
    
    def get_option_chain_data(self, underlying="NIFTY", spot_price=None):
        """Fetch option chain data - OPTIMIZED to prevent duplicates"""
        try:
            kite = self.get_kite_instance()
            
            # Get spot price
            if not spot_price:
                if underlying == "NIFTY":
                    price_data = self.get_nifty_price()
                    spot_price = price_data['price'] if price_data else 24000
                else:
                    price_data = self.get_banknifty_price()
                    spot_price = price_data['price'] if price_data else 52000
            
            # Calculate strike range
            strike_interval = 50 if underlying == "NIFTY" else 100
            min_strike = int((spot_price - 300) / strike_interval) * strike_interval
            max_strike = (int((spot_price + 300) / strike_interval) + 1) * strike_interval
            
            # Get expiry date
            expiry_date = self._get_current_expiry(underlying)
            
            # Generate unique strikes
            strikes = list(range(min_strike, max_strike + 1, strike_interval))
            
            # Create unique composite key for each option record
            option_data = []
            processed_keys = set()  # Track processed combinations
            
            for strike in strikes:
                # Generate symbols
                ce_symbol = self._generate_option_symbol(underlying, expiry_date, strike, 'CE')
                pe_symbol = self._generate_option_symbol(underlying, expiry_date, strike, 'PE')
                
                # Create unique key: underlying_expiry_strike
                unique_key = f"{underlying}_{expiry_date}_{strike}"
                
                # Skip if already processed (prevents duplicates)
                if unique_key in processed_keys:
                    continue
                
                try:
                    quotes = kite.quote([ce_symbol, pe_symbol])
                    time.sleep(0.5)  # Rate limiting
                    
                    ce_data = quotes.get(ce_symbol, {})
                    pe_data = quotes.get(pe_symbol, {})
                    
                    # Only add if we have valid data
                    if ce_data or pe_data:
                        option_info = {
                            'underlying': underlying,
                            'strike_price': strike,
                            'expiry_date': expiry_date,
                            'ce_oi': ce_data.get('oi', 0),
                            'ce_oi_change': 0,
                            'ce_volume': ce_data.get('volume', 0),
                            'ce_ltp': ce_data.get('last_price', 0.0),
                            'ce_change': ce_data.get('change', 0.0),
                            'ce_change_percent': ce_data.get('change_percent', 0.0),
                            'ce_strike_symbol': ce_symbol,
                            'ce_instrument_token': str(ce_data.get('instrument_token', '')),
                            'pe_oi': pe_data.get('oi', 0),
                            'pe_oi_change': 0,
                            'pe_volume': pe_data.get('volume', 0),
                            'pe_ltp': pe_data.get('last_price', 0.0),
                            'pe_change': pe_data.get('change', 0.0),
                            'pe_change_percent': pe_data.get('change_percent', 0.0),
                            'pe_strike_symbol': pe_symbol,
                            'pe_instrument_token': str(pe_data.get('instrument_token', '')),
                            'is_current_expiry': True,
                            'unique_key': unique_key  # Add for database UPSERT
                        }
                        
                        option_data.append(option_info)
                        processed_keys.add(unique_key)
                        
                        # Log OI data
                        self.api_logger.info(f"OI_DATA: {unique_key} - CE_OI: {option_info['ce_oi']}, PE_OI: {option_info['pe_oi']}")
                    
                except Exception as strike_error:
                    self.log_api_call('GET', 'option_quotes', [ce_symbol, pe_symbol], 
                                    error=str(strike_error), success=False)
                    continue
            
            return option_data
            
        except Exception as e:
            self.log_api_call('GET', 'option_chain_data', error=str(e), success=False)
            raise Exception(f"Error fetching option chain data: {str(e)}")
    
    def calculate_market_trend(self, option_chain_data, underlying):
        """Calculate market trend based on option chain analysis"""
        try:
            if not option_chain_data:
                return None
            
            total_ce_oi = sum(item['ce_oi'] for item in option_chain_data)
            total_pe_oi = sum(item['pe_oi'] for item in option_chain_data)
            total_ce_oi_change = sum(item['ce_oi_change'] for item in option_chain_data)
            total_pe_oi_change = sum(item['pe_oi_change'] for item in option_chain_data)
            
            pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
            
            total_oi_change = abs(total_ce_oi_change) + abs(total_pe_oi_change)
            
            if total_oi_change > 0:
                if total_pe_oi_change > total_ce_oi_change:
                    bullish_percentage = min(((total_pe_oi_change - total_ce_oi_change) / total_oi_change) * 100, 100)
                    bearish_percentage = 100 - bullish_percentage
                else:
                    bearish_percentage = min(((total_ce_oi_change - total_pe_oi_change) / total_oi_change) * 100, 100)
                    bullish_percentage = 100 - bearish_percentage
            else:
                bullish_percentage = bearish_percentage = 50
            
            # Find Max Pain
            max_pain_data = max(option_chain_data, key=lambda x: x['ce_oi'] + x['pe_oi'])
            
            # Support/Resistance
            sorted_by_oi = sorted(option_chain_data, key=lambda x: x['ce_oi'] + x['pe_oi'], reverse=True)[:3]
            support_level = min(level['strike_price'] for level in sorted_by_oi)
            resistance_level = max(level['strike_price'] for level in sorted_by_oi)
            
            return {
                'underlying': underlying,
                'expiry_date': option_chain_data[0]['expiry_date'],
                'total_ce_oi': total_ce_oi,
                'total_pe_oi': total_pe_oi,
                'total_ce_oi_change': total_ce_oi_change,
                'total_pe_oi_change': total_pe_oi_change,
                'pcr_oi': round(pcr_oi, 4),
                'pcr_volume': 0.0,
                'bullish_percentage': round(bullish_percentage, 2),
                'bearish_percentage': round(bearish_percentage, 2),
                'neutral_percentage': 0.0,
                'max_pain_strike': max_pain_data['strike_price'],
                'key_support_level': support_level,
                'key_resistance_level': resistance_level
            }
            
        except Exception as e:
            raise Exception(f"Error calculating market trend: {str(e)}")
    
    def is_authenticated(self):
        return self.token_manager.token_exists()
    
    def logout(self):
        self.token_manager.delete_token()
    
    def get_futures_data(self, underlying="NIFTY"):
        """Fetch futures data for given underlying"""
        try:
            kite = self.get_kite_instance()
            
            today = datetime.now()
            last_day = calendar.monthrange(today.year, today.month)[1]
            last_date = datetime(today.year, today.month, last_day)
            
            while last_date.weekday() != 3:  # Thursday
                last_date -= timedelta(days=1)
            
            expiry_str = last_date.strftime("%y%b").upper()
            symbol = f"NFO:{underlying}{expiry_str}FUT"
            
            quote_data = kite.quote([symbol])
            
            if quote_data and symbol in quote_data:
                data = quote_data[symbol]
                return {
                    'underlying': underlying,
                    'symbol': symbol,
                    'expiry_date': last_date.date(),
                    'futures_price': data.get('last_price', 0),
                    'open_interest': data.get('oi', 0),
                    'volume': data.get('volume', 0),
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching futures data for {underlying}: {str(e)}")
            return None
