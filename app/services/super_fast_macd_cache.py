import json
import os
from datetime import datetime, timedelta
from threading import Lock
import pytz

class SuperFastMacdCache:
    """Ultra-fast MACD cache using in-memory storage with file backup"""
    
    def __init__(self):
        self.cache = {}
        self.lock = Lock()
        self.cache_file = 'storage/fast_macd_cache.json'
        self.ist = pytz.timezone('Asia/Kolkata')
        self.ensure_storage_dir()
        self.load_from_file()
    
    def ensure_storage_dir(self):
        """Ensure storage directory exists"""
        os.makedirs('storage', exist_ok=True)
    
    def load_from_file(self):
        """Load cache from file on startup"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print("MACD cache loaded from file")
        except Exception as e:
            print(f"Error loading cache: {e}")
            self.cache = {}
    
    def save_to_file(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_cache_key(self, symbol: str, timeframe: int) -> str:
        """Generate cache key"""
        return f"{symbol}_{timeframe}min"
    
    def is_cache_fresh(self, cache_data: dict, max_age_minutes: int = 3) -> bool:
        """Check if cache data is fresh"""
        try:
            last_update = datetime.fromisoformat(cache_data.get('last_updated', ''))
            age = datetime.utcnow() - last_update
            return age.total_seconds() < (max_age_minutes * 60)
        except:
            return False
    
    def get_fast_signal(self, symbol: str, timeframe: int) -> dict:
        """Get MACD signal from ultra-fast cache"""
        with self.lock:
            cache_key = self.get_cache_key(symbol, timeframe)
            
            # Check if we have fresh data
            if cache_key in self.cache:
                cache_data = self.cache[cache_key]
                if self.is_cache_fresh(cache_data):
                    return {
                        'success': True,
                        'signal': cache_data['signal'],
                        'macd_line': cache_data['macd_line'],
                        'signal_line': cache_data['signal_line'],
                        'histogram': cache_data['histogram'],
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'timestamp': cache_data['timestamp'],
                        'formatted_time': cache_data['formatted_time'],
                        'timezone': 'IST'
                    }
            
            # Return stale data with warning if available
            if cache_key in self.cache:
                cache_data = self.cache[cache_key]
                result = {
                    'success': True,
                    'signal': cache_data['signal'],
                    'macd_line': cache_data['macd_line'],
                    'signal_line': cache_data['signal_line'],
                    'histogram': cache_data['histogram'],
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': cache_data['timestamp'],
                    'formatted_time': cache_data['formatted_time'] + ' (cached)',
                    'timezone': 'IST'
                }
                return result
            
            # No cache data available
            return {
                'success': False,
                'error': 'No cached data available. Please wait for next update.'
            }
    
    def update_signal(self, symbol: str, timeframe: int, signal_data: dict):
        """Update signal in cache"""
        with self.lock:
            cache_key = self.get_cache_key(symbol, timeframe)
            
            # Store essential data only
            self.cache[cache_key] = {
                'signal': signal_data.get('signal', 'NEUTRAL'),
                'macd_line': signal_data.get('macd_line', 0),
                'signal_line': signal_data.get('signal_line', 0),
                'histogram': signal_data.get('histogram', 0),
                'timestamp': signal_data.get('timestamp', datetime.utcnow().isoformat()),
                'formatted_time': signal_data.get('formatted_time', '--'),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Save to file periodically (every 5th update)
            if len(self.cache) % 5 == 0:
                self.save_to_file()
    
    def get_all_timeframes(self, symbol: str) -> dict:
        """Get all timeframes data at once"""
        timeframes = [30, 15, 12, 6, 3]
        results = {}
        
        for tf in timeframes:
            data = self.get_fast_signal(symbol, tf)
            if data.get('success'):
                results[f'{tf}min'] = [{
                    'signal': data['signal'],
                    'formatted_time': data['formatted_time'],
                    'macd_line': data['macd_line'],
                    'signal_line': data['signal_line'],
                    'candle_timestamp': data['timestamp']
                }]
            else:
                results[f'{tf}min'] = []
        
        return results

# Global cache instance
fast_cache = SuperFastMacdCache()
