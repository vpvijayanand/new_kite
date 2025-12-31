#!/usr/bin/env python3
import os
from dotenv import load_dotenv

print("=== DEBUG ENVIRONMENT LOADING ===")
print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Load .env explicitly from current directory
load_dotenv('.env')

print("\nEnvironment variables after load_dotenv():")
print(f"KITE_API_KEY: '{os.getenv('KITE_API_KEY')}'")
print(f"KITE_API_SECRET: '{os.getenv('KITE_API_SECRET')}'")

# Also check if there might be another .env file
possible_env_files = ['.env', '../.env', 'config/.env']
for env_file in possible_env_files:
    if os.path.exists(env_file):
        print(f"\nFound .env file at: {env_file}")
        with open(env_file, 'r') as f:
            lines = f.readlines()[:5]  # First 5 lines
            for line in lines:
                if 'KITE_API_KEY' in line:
                    print(f"Content: {line.strip()}")

# Test Flask config loading
print("\n=== TESTING FLASK CONFIG ===")
from config.config import Config
test_config = Config()
print(f"Config.KITE_API_KEY: '{test_config.KITE_API_KEY}'")

# Test Flask app
print("\n=== TESTING FLASK APP ===")
from app import create_app
app = create_app()
with app.app_context():
    print(f"Flask app config KITE_API_KEY: '{app.config.get('KITE_API_KEY')}'")
    
    # Test KiteConnect directly
    from kiteconnect import KiteConnect
    api_key = app.config.get('KITE_API_KEY')
    print(f"Creating KiteConnect with api_key: '{api_key}'")
    
    if api_key:
        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()
        print(f"KiteConnect login_url: {login_url}")
    else:
        print("API key is None or empty!")
