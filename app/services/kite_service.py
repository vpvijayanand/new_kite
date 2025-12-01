from kiteconnect import KiteConnect
from flask import current_app
from app.utils.token_manager import TokenManager

class KiteService:
    def __init__(self):
        self.api_key = current_app.config['KITE_API_KEY']
        self.api_secret = current_app.config['KITE_API_SECRET']
        self.kite = KiteConnect(api_key=self.api_key)
        self.token_manager = TokenManager(current_app.config['TOKEN_FILE_PATH'])
    
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
            # NIFTY 50 instrument token
            instrument_token = 256265  # NSE:NIFTY 50
            
            quote = kite.quote(["NSE:NIFTY 50"])
            
            if "NSE:NIFTY 50" in quote:
                data = quote["NSE:NIFTY 50"]
                return {
                    'symbol': 'NIFTY 50',
                    'price': data['last_price'],
                    'change': data.get('change'),
                    'change_percent': data.get('change_percent', 0)
                }
            return None
        except Exception as e:
            raise Exception(f"Error fetching Nifty price: {str(e)}")
    
    def is_authenticated(self):
        return self.token_manager.token_exists()
    
    def logout(self):
        self.token_manager.delete_token()