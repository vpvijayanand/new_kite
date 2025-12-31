import sys
import time
sys.path.append('c:/apps/kite_app')
import os
os.chdir('c:/apps/kite_app')

from app import create_app
from app.services.macd_cache_service import MacdCacheService
from app.services.super_fast_macd_cache import fast_cache

app = create_app()
with app.app_context():
    cache_service = MacdCacheService()
    timeframes = [30, 15, 12, 6, 3]
    
    total_start = time.time()
    
    for tf in timeframes:
        try:
            start_time = time.time()
            data = cache_service.calculate_fresh_macd('NIFTY', tf)
            calc_time = time.time() - start_time
            
            if data.get('success'):
                fast_cache.update_signal('NIFTY', tf, data)
                print(f'Updated {tf}min in {calc_time:.3f}s: {data.get("signal")} at {data.get("formatted_time")}')
            else:
                print(f'Error {tf}min in {calc_time:.3f}s: {data.get("error", "Unknown error")}')
        except Exception as e:
            print(f'Exception {tf}min: {e}')
    
    total_time = time.time() - total_start
    print(f'Total cache update time: {total_time:.3f}s')
    print('Cache update completed')
