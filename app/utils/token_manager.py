import json
import os
from datetime import datetime

class TokenManager:
    def __init__(self, token_file_path):
        self.token_file_path = token_file_path
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        directory = os.path.dirname(self.token_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    def save_token(self, access_token, user_id=None):
        token_data = {
            'access_token': access_token,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        with open(self.token_file_path, 'w') as f:
            json.dump(token_data, f, indent=4)
        
        return True
    
    def get_token(self):
        if not os.path.exists(self.token_file_path):
            return None
        
        try:
            with open(self.token_file_path, 'r') as f:
                token_data = json.load(f)
                return token_data.get('access_token')
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    def delete_token(self):
        if os.path.exists(self.token_file_path):
            os.remove(self.token_file_path)
            return True
        return False
    
    def token_exists(self):
        return os.path.exists(self.token_file_path) and self.get_token() is not None