from kiteconnect import KiteConnect
from flask import current_app
from app.utils.token_manager import TokenManager
import logging
import json
import os
from datetime import datetime

class KiteService:
    def __init__(self):
        self.api_key = current_app.config['KITE_API_KEY']
        self.api_secret = current_app.config['KITE_API_SECRET']
        self.kite = KiteConnect(api_key=self.api_key)
        self.token_manager = TokenManager(current_app.config['TOKEN_FILE_PATH'])
        
        # Setup API logging
        self.setup_api_logging()
    
    def setup_api_logging(self):
        """Setup logging for API requests and responses"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup logger for API calls
        self.api_logger = logging.getLogger('kite_api')
        self.api_logger.setLevel(logging.DEBUG)
        
        # Create file handler if not already exists
        if not self.api_logger.handlers:
            log_file = os.path.join(log_dir, 'kite_api_requests.log')
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.DEBUG)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.api_logger.addHandler(handler)
    
    def log_api_request(self, method, endpoint, params=None):
        """Log API request details"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'method': method,
                'endpoint': endpoint,
                'params': params,
                'type': 'REQUEST'
            }
            self.api_logger.info(f"API_REQUEST: {json.dumps(log_data, indent=2)}")
        except Exception as e:
            self.api_logger.error(f"Error logging request: {str(e)}")
    
    def log_api_response(self, method, endpoint, response_data, success=True, error=None):
        """Log API response details"""
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'method': method,
                'endpoint': endpoint,
                'success': success,
                'type': 'RESPONSE'
            }
            
            if success:
                # Log response structure and key data
                if isinstance(response_data, dict):
                    log_data['response_keys'] = list(response_data.keys())
                    log_data['response_size'] = len(str(response_data))
                    
                    # For option chain data, log specific details
                    if 'option_chain' in str(endpoint).lower() or any(key in response_data for key in ['oi', 'volume', 'ltp']):
                        log_data['sample_data'] = self._extract_sample_data(response_data)
                else:
                    log_data['response_type'] = type(response_data).__name__
                    log_data['response_size'] = len(str(response_data))
                
                # Log first 500 chars of response for debugging
                log_data['response_preview'] = str(response_data)[:500] + "..." if len(str(response_data)) > 500 else str(response_data)
            else:
                log_data['error'] = str(error)
            
            self.api_logger.info(f"API_RESPONSE: {json.dumps(log_data, indent=2)}")
        except Exception as e:
            self.api_logger.error(f"Error logging response: {str(e)}")
    
    def _extract_sample_data(self, response_data):
        """Extract sample data from option chain response for logging"""
        try:
            sample = {}
            
            # If it's a quote response
            if isinstance(response_data, dict):
                for key, value in response_data.items():
                    if isinstance(value, dict):
                        sample[key] = {
                            'oi': value.get('oi', 'N/A'),
                            'volume': value.get('volume', 'N/A'), 
                            'last_price': value.get('last_price', 'N/A'),
                            'change': value.get('change', 'N/A')
                        }
                        break  # Just sample first instrument
            
            return sample
        except:
            return "Error extracting sample data"

    def get_login_url(self):
        return self.kite.login_url()
    
    def generate_session(self, request_token):
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data['access_token']
            
            # Save token
            self.token_manager.save_token(access_token, data.get('user_id'))
            
            # Set access token for current session
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
    
    def get_nifty_price(self):
        try:
            kite = self.get_kite_instance()
            
            # Log API request
            self.log_api_request('GET', 'quote', ['NSE:NIFTY 50'])
            
            quote = kite.quote(["NSE:NIFTY 50"])
            
            # Log API response
            self.log_api_response('GET', 'quote', quote, success=True)
            
            if "NSE:NIFTY 50" in quote:
                data = quote["NSE:NIFTY 50"]
                ohlc = data.get('ohlc', {})
                return {
                    'symbol': 'NIFTY 50',
                    'price': data['last_price'],
                    'high': ohlc.get('high', data['last_price']),
                    'low': ohlc.get('low', data['last_price']),
                    'open': ohlc.get('open', data['last_price']),
                    'close': ohlc.get('close', data['last_price']),
                    'change': data.get('change'),
                    'change_percent': data.get('change_percent', 0)
                }
            return None
        except Exception as e:
            # Log API error
            self.log_api_response('GET', 'quote', None, success=False, error=str(e))
            raise Exception(f"Error fetching Nifty price: {str(e)}")
    
    def get_banknifty_price(self):
        try:
            kite = self.get_kite_instance()
            
            # Log API request
            self.log_api_request('GET', 'quote', ['NSE:NIFTY BANK'])
            
            quote = kite.quote(["NSE:NIFTY BANK"])
            
            # Log API response
            self.log_api_response('GET', 'quote', quote, success=True)
            
            if "NSE:NIFTY BANK" in quote:
                data = quote["NSE:NIFTY BANK"]
                ohlc = data.get('ohlc', {})
                return {
                    'symbol': 'NIFTY BANK',
                    'price': data['last_price'],
                    'high': ohlc.get('high', data['last_price']),
                    'low': ohlc.get('low', data['last_price']),
                    'open': ohlc.get('open', data['last_price']),
                    'close': ohlc.get('close', data['last_price']),
                    'change': data.get('change'),
                    'change_percent': data.get('change_percent', 0)
                }
            return None
        except Exception as e:
            raise Exception(f"Error fetching BankNifty price: {str(e)}")
    
    def get_option_chain_data(self, underlying="NIFTY", spot_price=None):
        """
        Fetch option chain data for given underlying
        Args:
            underlying: 'NIFTY' or 'BANKNIFTY' 
            spot_price: Current spot price to determine strike range
        """
        try:
            kite = self.get_kite_instance()
            
            if not spot_price:
                if underlying == "NIFTY":
                    nifty_data = self.get_nifty_price()
                    spot_price = nifty_data['price'] if nifty_data else 24000
                else:  # BANKNIFTY
                    banknifty_data = self.get_banknifty_price()
                    spot_price = banknifty_data['price'] if banknifty_data else 52000
            
            # Calculate strike range: ±300 points from current price
            min_strike = (spot_price - 300)
            max_strike = (spot_price + 300)
            
            # Round to nearest 50 for NIFTY or 100 for BANKNIFTY
            strike_interval = 50 if underlying == "NIFTY" else 100
            
            # Adjust range to strike intervals
            min_strike = (int(min_strike / strike_interval) * strike_interval)
            max_strike = (int(max_strike / strike_interval) + 1) * strike_interval
            
            # Get current expiry date - use custom settings if available
            try:
                from app.models.expiry_settings import ExpirySettings
                expiry_date = ExpirySettings.get_current_expiry(underlying)
            except:
                # Fallback to automatic calculation
                from datetime import datetime, timedelta
                today = datetime.now().date()
                days_ahead = 3 - today.weekday()  # 3 = Thursday
                if days_ahead <= 0:
                    days_ahead += 7
                expiry_date = today + timedelta(days_ahead)
            
            # Generate strike prices in the range
            strikes = []
            current_strike = min_strike
            while current_strike <= max_strike:
                strikes.append(current_strike)
                current_strike += strike_interval
            
            option_data = []
            
            for strike in strikes:
                # Format option symbols for Kite - CORRECTED FORMAT
                if underlying == "NIFTY":
                    # Correct format: NFO:NIFTY25DEC26000CE (YY + Month name + Strike + CE/PE)
                    month_name = expiry_date.strftime('%b').upper()[:3]  # DEC, JAN, etc.
                    ce_symbol = f"NFO:NIFTY{expiry_date.strftime('%y')}{month_name}{int(strike)}CE"
                    pe_symbol = f"NFO:NIFTY{expiry_date.strftime('%y')}{month_name}{int(strike)}PE"
                else:  # BANKNIFTY
                    # Correct format: NFO:BANKNIFTY25DEC59000CE
                    month_name = expiry_date.strftime('%b').upper()[:3]  # DEC, JAN, etc.
                    ce_symbol = f"NFO:BANKNIFTY{expiry_date.strftime('%y')}{month_name}{int(strike)}CE"
                    pe_symbol = f"NFO:BANKNIFTY{expiry_date.strftime('%y')}{month_name}{int(strike)}PE"
                
                try:
                    # Log API request for option data
                    self.log_api_request('GET', 'option_quotes', [ce_symbol, pe_symbol])
                    
                    # Get quotes for both CE and PE
                    quotes = kite.quote([ce_symbol, pe_symbol])
                    
                    # Log API response for option data
                    self.log_api_response('GET', 'option_quotes', quotes, success=True)
                    
                    ce_data = quotes.get(ce_symbol, {})
                    pe_data = quotes.get(pe_symbol, {})
                    
                    # Extract instrument tokens from the response
                    ce_instrument_token = str(ce_data.get('instrument_token', ''))
                    pe_instrument_token = str(pe_data.get('instrument_token', ''))
                    
                    option_info = {
                        'underlying': underlying,
                        'strike_price': strike,
                        'expiry_date': expiry_date,
                        'ce_oi': ce_data.get('oi', 0),
                        'ce_oi_change': 0,  # Will be calculated by comparing with previous record
                        'ce_volume': ce_data.get('volume', 0),
                        'ce_ltp': ce_data.get('last_price', 0.0),
                        'ce_change': ce_data.get('change', 0.0),
                        'ce_change_percent': ce_data.get('change_percent', 0.0),
                        'ce_strike_symbol': ce_symbol,
                        'ce_instrument_token': ce_instrument_token,
                        'pe_oi': pe_data.get('oi', 0),
                        'pe_oi_change': 0,  # Will be calculated by comparing with previous record
                        'pe_volume': pe_data.get('volume', 0),
                        'pe_ltp': pe_data.get('last_price', 0.0),
                        'pe_change': pe_data.get('change', 0.0),
                        'pe_change_percent': pe_data.get('change_percent', 0.0),
                        'pe_strike_symbol': pe_symbol,
                        'pe_instrument_token': pe_instrument_token,
                        'is_current_expiry': True
                    }
                    
                    # Log detailed OI data for debugging
                    oi_details = {
                        'strike': strike,
                        'ce_symbol': ce_symbol,
                        'pe_symbol': pe_symbol,
                        'ce_raw_data': {
                            'oi': ce_data.get('oi'),
                            'volume': ce_data.get('volume'),
                            'last_price': ce_data.get('last_price'),
                            'oi_day_change': ce_data.get('oi_day_change'),
                            'change': ce_data.get('change'),
                            'net_change': ce_data.get('net_change'),
                            'all_keys': list(ce_data.keys()) if ce_data else []
                        },
                        'pe_raw_data': {
                            'oi': pe_data.get('oi'),
                            'volume': pe_data.get('volume'),  
                            'last_price': pe_data.get('last_price'),
                            'oi_day_change': pe_data.get('oi_day_change'),
                            'change': pe_data.get('change'),
                            'net_change': pe_data.get('net_change'),
                            'all_keys': list(pe_data.keys()) if pe_data else []
                        }
                    }
                    self.api_logger.info(f"OI_DATA_DETAIL: {json.dumps(oi_details, indent=2, default=str)}")
                    
                    option_data.append(option_info)
                    
                except Exception as strike_error:
                    # Log API error for this strike
                    self.log_api_response('GET', 'option_quotes', None, success=False, 
                                        error=f"Strike {strike}: {str(strike_error)}")
                    # Skip this strike if there's an error
                    print(f"Error fetching option data for {strike}: {strike_error}")
                    continue
            
            return option_data
            
        except Exception as e:
            # Log overall option chain error
            self.log_api_response('GET', 'option_chain_data', None, success=False, error=str(e))
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
            
            # Calculate Put-Call Ratio
            pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
            
            # Calculate trend percentages based on OI changes
            total_oi_change = abs(total_ce_oi_change) + abs(total_pe_oi_change)
            
            if total_oi_change > 0:
                # More PE addition = Bullish, More CE addition = Bearish
                if total_pe_oi_change > total_ce_oi_change:
                    bullish_percentage = min(((total_pe_oi_change - total_ce_oi_change) / total_oi_change) * 100, 100)
                    bearish_percentage = 100 - bullish_percentage
                else:
                    bearish_percentage = min(((total_ce_oi_change - total_pe_oi_change) / total_oi_change) * 100, 100)
                    bullish_percentage = 100 - bearish_percentage
            else:
                bullish_percentage = bearish_percentage = 50
            
            # Find Max Pain (strike with highest total OI)
            max_pain_strike = 0
            max_total_oi = 0
            
            for item in option_chain_data:
                total_oi = item['ce_oi'] + item['pe_oi']
                if total_oi > max_total_oi:
                    max_total_oi = total_oi
                    max_pain_strike = item['strike_price']
            
            # Simple support/resistance based on high OI levels
            sorted_by_oi = sorted(option_chain_data, key=lambda x: x['ce_oi'] + x['pe_oi'], reverse=True)
            key_levels = sorted_by_oi[:3]  # Top 3 OI levels
            
            support_level = min(level['strike_price'] for level in key_levels)
            resistance_level = max(level['strike_price'] for level in key_levels)
            
            return {
                'underlying': underlying,
                'expiry_date': option_chain_data[0]['expiry_date'],
                'total_ce_oi': total_ce_oi,
                'total_pe_oi': total_pe_oi,
                'total_ce_oi_change': total_ce_oi_change,
                'total_pe_oi_change': total_pe_oi_change,
                'pcr_oi': pcr_oi,
                'pcr_volume': 0.0,  # Would need volume data
                'bullish_percentage': round(bullish_percentage, 2),
                'bearish_percentage': round(bearish_percentage, 2),
                'neutral_percentage': 0.0,
                'max_pain_strike': max_pain_strike,
                'key_support_level': support_level,
                'key_resistance_level': resistance_level
            }
            
        except Exception as e:
            raise Exception(f"Error calculating market trend: {str(e)}")
    
    def is_authenticated(self):
        return self.token_manager.token_exists()
    
    def logout(self):
        self.token_manager.delete_token()
    
    def get_stock_price(self, symbol):
        """Get current stock price for a given symbol"""
        try:
            # Load access token
            access_token = self.token_manager.load_token()
            if not access_token:
                print(f"No access token available for fetching {symbol} price")
                return None
            
            self.kite.set_access_token(access_token)
            
            # Get instrument token for the symbol (this is a simplified approach)
            # In production, you'd need to map symbols to instrument tokens
            
            # For now, we'll use a demo/mock approach for stock prices
            # since getting individual stock prices requires instrument tokens
            return self._get_demo_stock_price(symbol)
            
        except Exception as e:
            print(f"Error fetching stock price for {symbol}: {e}")
            return None
    
    def _get_demo_stock_price(self, symbol):
        """Generate demo stock price data for development"""
        import random
        
        # Base prices for major NIFTY 50 stocks (approximate current levels)
        base_prices = {
            'RELIANCE': 3000, 'HDFCBANK': 1700, 'ICICIBANK': 1200, 'INFY': 1800, 'TCS': 4200,
            'BHARTIARTL': 1500, 'ITC': 450, 'LT': 3800, 'KOTAKBANK': 1800, 'HINDUNILVR': 2400,
            'SBIN': 850, 'BAJFINANCE': 7000, 'HCLTECH': 1800, 'MARUTI': 11000, 'M&M': 3000,
            'ASIANPAINT': 2500, 'SUNPHARMA': 1800, 'TATAMOTORS': 1000, 'ULTRACEMCO': 11500,
            'AXISBANK': 1200, 'JSWSTEEL': 900, 'POWERGRID': 350, 'NTPC': 400, 'TECHM': 1700,
            'ADANIPORTS': 1500, 'COALINDIA': 450, 'ONGC': 280, 'HINDALCO': 650, 'BAJAJFINSV': 1600,
            'BAJAJ-AUTO': 9000, 'NESTLEIND': 2200, 'CIPLA': 1700, 'DRREDDY': 1300, 'TITAN': 3400,
            'TRENT': 6500, 'SBILIFE': 1600, 'TATASTEEL': 150, 'WIPRO': 550, 'GRASIM': 2600,
            'ADANIENT': 3200, 'TATACONSUM': 900, 'JIOFIN': 350, 'INDIGO': 4500, 'APOLLOHOSP': 7000,
            'BEL': 300, 'EICHERMOT': 4800, 'SHIRAMFIN': 3200, 'TMPV': 800, 'MAXHEALTH': 1000
        }
        
        base_price = base_prices.get(symbol, 1000)  # Default to 1000 if symbol not found
        
        # Add some random variation (-3% to +3%)
        variation = random.uniform(-0.03, 0.03)
        current_price = base_price * (1 + variation)
        
        # Generate volume (random between 10K to 10M)
        volume = random.randint(10000, 10000000)
        
        return {
            'last_price': round(current_price, 2),
            'volume': volume,
            'change': round(base_price * variation, 2),
            'change_percent': round(variation * 100, 2)
        }