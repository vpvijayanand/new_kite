import sys
sys.path.append('c:/apps/kite_app')
from app import create_app
from app.services.macd_cache_service import MacdCacheService
from app.services.super_fast_macd_cache import fast_cache

app = create_app()
with app.app_context():
    cache_service = MacdCacheService()
    timeframes = [30, 15, 12, 6, 3]
    
    for tf in timeframes:
        try:
            data = cache_service.calculate_fresh_macd('NIFTY', tf)
            if data.get('success'):
                fast_cache.update_signal('NIFTY', tf, data)
                print(f'Updated {tf}min: {data.get("signal")} at {data.get("formatted_time")}')
            else:
                print(f'Error {tf}min: {data.get("error", "Unknown error")}')
        except Exception as e:
            print(f'Exception {tf}min: {e}')
    
    print('Cache update completed')
