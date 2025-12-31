@echo off
REM Strategy 1 Execution Script for Windows Task Scheduler
REM This script runs Strategy 1 monitoring every minute during market hours

REM Set the working directory
cd /d "C:\apps\kite_app"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set Flask environment
set FLASK_APP=run.py
set FLASK_ENV=production

REM Run the strategy execution via Python
C:\apps\kite_app\venv\Scripts\python.exe -c "from app import create_app; from app.services.strategy_service import StrategyService; import os; app = create_app(os.getenv('FLASK_ENV', 'production')); app.app_context().push(); strategy_service = StrategyService(); result = strategy_service.execute_strategy_1(); print(f'Strategy execution: {result.get(\"message\", \"Unknown status\")}')"

echo Strategy 1 execution completed at %date% %time%
