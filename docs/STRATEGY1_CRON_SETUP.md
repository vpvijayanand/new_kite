# Strategy 1 Cron Job Setup Instructions

## Overview
Strategy 1 monitors NIFTY breakouts every minute during market hours (9:30 AM - 3:15 PM IST) with the following enhanced features:

### Enhanced Strategy Rules:
1. **Range Capture**: 9:12 AM - 9:33 AM NIFTY high/low
2. **Trading Window**: 9:30 AM - 12:12 PM (no new trades after 12:12 PM)
3. **Maximum Trades**: 2 trades per day
4. **Auto-Close**: Trades close when NIFTY crosses opposite level
5. **Position Management**: 
   - Bear Call Spread on low breakout
   - Bull Put Spread on high breakout

## Cron Job Setup Options

### Option 1: Linux/Unix Cron Job
```bash
# Edit crontab
crontab -e

# Add this line to run every minute during market hours (9:30 AM - 3:15 PM IST)
# Adjust times for your timezone
30-59 9 * * 1-5 /path/to/kite_app/scripts/strategy1_cron.sh
0-15 10-14 * * 1-5 /path/to/kite_app/scripts/strategy1_cron.sh
0-15 15 * * 1-5 /path/to/kite_app/scripts/strategy1_cron.sh
```

### Option 2: Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily, repeat every 1 minute for 6 hours (9:30 AM - 3:30 PM)
4. Set action: Start a program
5. Program: `C:\apps\kite_app\scripts\strategy1_cron.bat`
6. Set conditions: Only run on weekdays

### Option 3: Python Standalone (Recommended)
```bash
# Make script executable
chmod +x /path/to/kite_app/scripts/strategy1_standalone.py

# Add to crontab (runs every minute during market hours)
* 9-15 * * 1-5 /usr/bin/python3 /path/to/kite_app/scripts/strategy1_standalone.py

# For more precise timing (IST):
30-59 9 * * 1-5 /usr/bin/python3 /path/to/kite_app/scripts/strategy1_standalone.py
0-15 10-14 * * 1-5 /usr/bin/python3 /path/to/kite_app/scripts/strategy1_standalone.py
0-15 15 * * 1-5 /usr/bin/python3 /path/to/kite_app/scripts/strategy1_standalone.py
```

### Option 4: Built-in Flask Scheduler (Already Active)
The application already includes a built-in scheduler that runs automatically when the Flask app is running.
No additional cron job needed if the Flask application is running continuously.

## Manual Testing

### Test Strategy Execution:
```bash
# Navigate to app directory
cd /path/to/kite_app

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows

# Test the standalone script
python scripts/strategy1_standalone.py

# Test via API (if Flask app is running)
curl -X GET "http://localhost:5000/strategies/api/strategy-1/execute"
```

## Monitoring and Logs

### Log Locations:
- **Cron logs**: `/path/to/kite_app/logs/strategy1_cron.log`
- **Flask logs**: Flask application logs
- **System cron logs**: `/var/log/cron` (Linux)

### Monitor Strategy:
1. **Web Interface**: Visit `http://localhost:5000/strategies/strategy-1`
2. **API Status**: `curl http://localhost:5000/strategies/api/strategy-1/status`
3. **Database**: Check `strategy1_executions` table

## Important Configuration

### Environment Variables:
```bash
export FLASK_APP=run.py
export FLASK_ENV=production  # or development
export DATABASE_URL=your_postgres_url
```

### Database Requirements:
- PostgreSQL database with `strategy1_executions` table
- Run migrations: `flask db upgrade`

### Network Requirements:
- Access to Kite Connect API for option chain data
- Access to NSE for NIFTY price data

## Troubleshooting

### Common Issues:
1. **Permission Denied**: Make scripts executable (`chmod +x`)
2. **Python Path**: Ensure virtual environment is activated
3. **Database Connection**: Check PostgreSQL connection
4. **Market Data**: Verify Kite Connect API access
5. **Timezone**: Ensure server time is IST or adjust cron times

### Debug Commands:
```bash
# Check cron is running
systemctl status cron

# View cron logs
tail -f /var/log/cron

# Test database connection
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import db; print('DB OK' if db.engine.execute('SELECT 1') else 'DB Error')"

# Test strategy service
python -c "from app import create_app; from app.services.strategy_service import StrategyService; app = create_app(); app.app_context().push(); s = StrategyService(); print(s.get_strategy_1_data())"
```

## Strategy Performance Monitoring

### Key Metrics to Monitor:
- Daily trade count (max 2)
- P&L per trade
- Trade closure reasons
- Market range accuracy
- Option LTP accuracy

### Alerts to Set:
- Trade limit reached
- Large P&L movements
- Strategy execution errors
- Database connection issues

## Backup and Recovery
- Backup `strategy1_executions` table daily
- Monitor disk space for logs
- Set up database replication if needed
