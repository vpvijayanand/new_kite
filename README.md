# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL database
createdb kite_db

# 4. Configure environment variables
# Edit .env file with your credentials

# 5. Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 6. Run the application
python run.py

# Edit crontab
crontab -e

# Add these lines for market hours execution
30-59 9 * * 1-5 /path/to/kite_app/scripts/strategy1_standalone.py
0-15 10-14 * * 1-5 /path/to/kite_app/scripts/strategy1_standalone.py
0-15 15 * * 1-5 /path/to/kite_app/scripts/strategy1_standalone.py
