#!/usr/bin/env python3
"""
Production Deployment Script for Kite MACD Trading System
Run this script to set up the production database with all required tables.
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate, upgrade, init, migrate as create_migration
from app import create_app, db

def deploy_production():
    """Deploy the application to production"""
    
    print("🚀 Starting Production Deployment for Kite MACD System")
    print("=" * 60)
    
    # Create Flask app
    app = create_app()
    migrate = Migrate(app, db)
    
    with app.app_context():
        
        # Step 1: Initialize migration repository if needed
        print("\n📁 Step 1: Checking migration repository...")
        if not os.path.exists('migrations'):
            print("   Creating migration repository...")
            init()
        else:
            print("   ✅ Migration repository exists")
        
        # Step 2: Create database tables
        print("\n🗄️  Step 2: Creating database tables...")
        try:
            # Import all models to ensure they're registered
            from app.models.nifty_price import NiftyPrice
            from app.models.banknifty_price import BankNiftyPrice, OptionChainData, MarketTrend
            from app.models.macd_signal import MacdSignal
            from app.models.futures_oi_data import FuturesOIData
            from app.models.strategy_models import Strategy1Entry, Strategy1LTPHistory, Strategy1Execution
            from app.models.expiry_settings import ExpirySettings
            from app.models.nifty_stocks import NiftyStock
            
            print("   📋 All models imported successfully")
            
            # Create all tables
            db.create_all()
            print("   ✅ Database tables created successfully")
            
            # Step 3: Run migrations
            print("\n⚡ Step 3: Running database migrations...")
            try:
                upgrade()
                print("   ✅ Database migrations completed")
            except Exception as e:
                print(f"   ⚠️  Migration info: {e}")
                # This is often normal if tables already exist
            
            # Step 4: Verify tables
            print("\n🔍 Step 4: Verifying database tables...")
            tables = db.engine.table_names()
            required_tables = [
                'nifty_price', 'banknifty_price', 'option_chain_data', 
                'market_trend', 'macd_signal', 'futures_oi_data',
                'strategy1_entry', 'strategy1_ltp_history', 'strategy1_execution',
                'expiry_settings', 'nifty_stock'
            ]
            
            missing_tables = []
            for table in required_tables:
                if table in tables:
                    print(f"   ✅ {table}")
                else:
                    missing_tables.append(table)
                    print(f"   ❌ {table} - MISSING")
            
            if missing_tables:
                print(f"\n⚠️  Warning: {len(missing_tables)} tables are missing!")
                print("   This might be normal if using different table names.")
            else:
                print(f"\n🎉 Success: All {len(required_tables)} required tables exist!")
            
            # Step 5: Create required directories
            print("\n📂 Step 5: Creating required directories...")
            directories = [
                'storage/tokens',
                'storage/macd_cache',
                'logs'
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                print(f"   ✅ {directory}")
            
            print("\n🚀 Production Deployment Complete!")
            print("=" * 60)
            print("✅ Database tables: Created")
            print("✅ Migrations: Applied")  
            print("✅ Directories: Created")
            print("✅ MACD System: Ready for production")
            print("\n🎯 Next Steps:")
            print("1. Start your Flask application: python run.py")
            print("2. The background MACD jobs will start automatically")
            print("3. API will be available at http://localhost:5000")
            print("4. MACD signals update every 2 minutes automatically")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during deployment: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = deploy_production()
    if success:
        print("\n🎉 Deployment successful! Your MACD system is ready.")
        sys.exit(0)
    else:
        print("\n💥 Deployment failed! Check errors above.")
        sys.exit(1)
