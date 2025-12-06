# Temporary Market Hours Adjustment for Testing

## Current Setting (Production):
```python
market_start = time(9, 30)  # 9:30 AM
market_end = time(15, 15)   # 3:15 PM
```

## For Testing (modify temporarily):
```python
market_start = time(9, 0)   # 9:00 AM (or earlier)
market_end = time(16, 0)    # 4:00 PM (or later)
```

## Steps to Test:
1. Edit `/var/www/html/Kite_app/app/services/strategy_service.py`
2. Change line ~23: `market_start = time(9, 0)`  # Start earlier
3. Test the strategy
4. **Remember to change it back** for production!

## Or Use Force Flag (Better for Testing):
```bash
cd /var/www/html/Kite_app
source venv/bin/activate
python scripts/strategy1_standalone.py --force
```

## Cron Job Schedule (Already Correct):
Your cron jobs are correctly set for market hours:
- `30-59 9 * * 1-5` - Last 30 minutes of 9 AM hour (9:30-9:59 AM) ✅
- `0-15 10-14 * * 1-5` - First 15 minutes of each hour from 10 AM-2 PM ✅  
- `0-15 15 * * 1-5` - First 15 minutes of 3 PM (3:00-3:15 PM) ✅

The cron schedule perfectly matches the market hours!
