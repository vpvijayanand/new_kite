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
