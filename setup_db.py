#!/usr/bin/env python3
"""
Kite App Setup and Database Migration Script
This script sets up the database and runs all necessary migrations.
"""

import os
import sys
import subprocess
from app import create_app, db
from app.models.nifty_price import NiftyPrice

def run_command(command, description=""):
    """Run a shell command and return the result"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Success: {description}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
    else:
        print(f"❌ Error: {description}")
        print(f"Error output: {result.stderr}")
        return False
    
    return True

def check_database_connection():
    """Check if the database connection is working"""
    try:
        app = create_app()
        with app.app_context():
            # Test database connection
            db.engine.connect()
            print("✅ Database connection successful!")
            
            # Check existing tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Existing tables: {tables}")
            
            # Check NiftyPrice model
            count = NiftyPrice.query.count()
            print(f"📊 NiftyPrice records count: {count}")
            
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def setup_database():
    """Set up database migrations and schema"""
    
    print("\n" + "="*50)
    print("🚀 KITE APP DATABASE SETUP")
    print("="*50)
    
    # Check database connection first
    if not check_database_connection():
        print("\n❌ Database setup failed - connection error")
        return False
    
    # Check if migrations directory exists
    if not os.path.exists('migrations'):
        print("\n📁 Initializing Flask-Migrate...")
        if not run_command(f"{sys.executable} -m flask db init", "Initialize migrations"):
            return False
    else:
        print("\n✅ Migrations directory already exists")
    
    # Check current migration status
    print("\n🔍 Checking migration status...")
    result = subprocess.run(f"{sys.executable} -m flask db current", 
                          shell=True, capture_output=True, text=True)
    
    # Create migration if needed
    print("\n🔄 Creating/updating migration files...")
    run_command(f'{sys.executable} -m flask db migrate -m "Auto migration"', 
               "Generate migration files")
    
    # Apply migrations
    print("\n⬆️ Applying migrations...")
    if not run_command(f"{sys.executable} -m flask db upgrade", "Apply migrations"):
        return False
    
    # Final verification
    print("\n🧪 Final verification...")
    return check_database_connection()

def test_app():
    """Test if the app starts correctly"""
    print("\n🧪 Testing application startup...")
    
    try:
        app = create_app()
        with app.test_client() as client:
            # Test basic routes
            routes_to_test = [
                ('/', 'Root route'),
                ('/login', 'Login route'),
                ('/api/status', 'API status route')
            ]
            
            for route, description in routes_to_test:
                response = client.get(route)
                if response.status_code == 200:
                    print(f"✅ {description}: {response.status_code}")
                else:
                    print(f"⚠️ {description}: {response.status_code}")
        
        print("✅ Application startup test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Application test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🎯 Starting Kite App setup...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️ Warning: .env file not found. Please ensure environment variables are set.")
    
    # Setup database
    if not setup_database():
        print("\n❌ Setup failed!")
        return False
    
    # Test application
    if not test_app():
        print("\n⚠️ Application tests failed, but database setup completed.")
    
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\n📝 Next steps:")
    print("1. Ensure your .env file has correct API credentials")
    print("2. Run 'python run.py' to start the application")
    print("3. Visit http://localhost:5000 to access the app")
    
    return True

if __name__ == "__main__":
    main()
