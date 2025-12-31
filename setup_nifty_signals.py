#!/usr/bin/env python3
"""
NIFTY Trading Signals Production Setup Script

This script initializes the database tables for NIFTY signal tracking
and generates initial signals for production deployment.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.nifty_signal import NiftySignal
from app.services.nifty_signal_service import NiftySignalGenerator

def create_database_tables():
    """Create all database tables"""
    print("📊 Creating database tables...")
    try:
        db.create_all()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

def check_nifty_price_data():
    """Check if NIFTY price data is available"""
    print("🔍 Checking NIFTY price data availability...")
    try:
        from app.models.nifty_price import NiftyPrice
        
        # Get total count
        total_records = NiftyPrice.query.count()
        print(f"📈 Found {total_records} NIFTY price records")
        
        if total_records == 0:
            print("⚠️ No NIFTY price data found. Please run market data collection first.")
            return False
        
        # Get latest record
        latest_record = NiftyPrice.query.order_by(NiftyPrice.timestamp.desc()).first()
        if latest_record:
            print(f"🕐 Latest record: {latest_record.timestamp} - Price: ₹{latest_record.price}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking NIFTY price data: {e}")
        return False

def generate_initial_signals():
    """Generate initial signals from historical data"""
    print("🎯 Generating initial trading signals...")
    try:
        signal_generator = NiftySignalGenerator()
        
        # Generate signals for the last 30 days (720 hours)
        print("📊 Generating signals from last 30 days of available data")
        
        # Generate signals using the correct method signature
        signals = signal_generator.generate_signals(lookback_hours=720)  # 30 days
        
        if signals:
            buy_signals = sum(1 for signal in signals if signal and signal.signal_type == 'BUY')
            sell_signals = sum(1 for signal in signals if signal and signal.signal_type == 'SELL')
            
            print(f"✅ Successfully generated {len(signals)} signals")
            print(f"📈 Buy signals: {buy_signals}")
            print(f"📉 Sell signals: {sell_signals}")
            return True
        else:
            print("⚠️ No signals generated - this may be normal if no crossovers occurred")
            return True  # Don't fail setup for this
            
    except Exception as e:
        print(f"❌ Error generating initial signals: {e}")
        return False

def validate_signal_generation():
    """Validate that signals were generated correctly"""
    print("✅ Validating signal generation...")
    try:
        # Check total signals
        total_signals = NiftySignal.query.count()
        print(f"📊 Total signals in database: {total_signals}")
        
        if total_signals == 0:
            print("⚠️ No signals found in database")
            return False
        
        # Check latest signals
        latest_signals = NiftySignal.get_latest_signals(limit=5)
        print(f"🔍 Latest {len(latest_signals)} signals:")
        
        for signal in latest_signals:
            signal_type = "📈 BUY" if signal.signal_type == 'BUY' else "📉 SELL"
            print(f"  {signal_type} - {signal.timestamp} - Price: ₹{signal.price} - Confidence: {signal.confidence}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating signals: {e}")
        return False

def main():
    """Main setup function for production"""
    print("🚀 Starting NIFTY Trading Signals Production Setup...")
    print("="*60)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Step 1: Create database tables
        if not create_database_tables():
            print("❌ Setup failed at database creation")
            return False
        
        # Step 2: Check NIFTY price data
        if not check_nifty_price_data():
            print("❌ Setup failed: No NIFTY price data available")
            print("💡 Please run market data collection first")
            return False
        
        # Step 3: Generate initial signals
        if not generate_initial_signals():
            print("❌ Setup failed at signal generation")
            return False
        
        # Step 4: Validate signal generation
        if not validate_signal_generation():
            print("❌ Setup failed at validation")
            return False
        
        # Step 5: Test signal generation (optional)
        try:
            print("🚀 Testing signal generation service...")
            test_generator = NiftySignalGenerator()
            test_signals = test_generator.generate_signals_for_latest_data()
            if test_signals:
                print(f"✅ Signal generation service working - Generated {len(test_signals)} recent signals")
            else:
                print("ℹ️ Signal generation service working - No recent crossovers detected")
        except Exception as e:
            print(f"⚠️ Signal generation test warning: {e}")
        
        print("\n🎉 Production setup completed successfully!")
        print("📊 Signals Dashboard: /signals/")
        print("📈 Chart View: /signals/chart")
        print("🔗 API Endpoint: /api/signals")
        
        return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Production deployment ready!")
        else:
            print("\n❌ Setup failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during setup: {e}")
        sys.exit(1)
