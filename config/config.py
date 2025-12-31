import os
from dotenv import load_dotenv

# Load .env file explicitly with absolute path
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(os.path.dirname(basedir), '.env')

load_dotenv(env_path, override=True)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Kite Configuration
    KITE_API_KEY = os.getenv('KITE_API_KEY')
    KITE_API_SECRET = os.getenv('KITE_API_SECRET')
    KITE_REDIRECT_URL = os.getenv('KITE_REDIRECT_URL')
    
    # Token Storage
    TOKEN_FILE_PATH = os.getenv('TOKEN_FILE_PATH', 'storage/tokens/access_token.json')
    
    # Logging
    LOG_FILE = 'logs/app.log'
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}