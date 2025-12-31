#!/bin/bash

# Strategy 1 Execution Script for Cron Job
# This script runs Strategy 1 monitoring every minute during market hours

# Set the working directory
cd /path/to/your/kite_app

# Activate virtual environment (adjust path as needed)
source venv/bin/activate

# Set Flask app environment
export FLASK_APP=run.py
export FLASK_ENV=production

# Run the strategy execution via API call
# You can use curl to call the strategy execution endpoint
curl -s -X GET "http://localhost:5000/strategies/api/strategy-1/execute" > /dev/null

# Alternative: Run via Python script
# python3 -c "
# from app import create_app
# from app.services.strategy_service import StrategyService
# import os

# app = create_app(os.getenv('FLASK_ENV', 'production'))
# with app.app_context():
#     strategy_service = StrategyService()
#     result = strategy_service.execute_strategy_1()
#     print(f'Strategy execution: {result.get(\"message\", \"Unknown status\")}')
# "

echo "Strategy 1 execution completed at $(date)"
