#!/usr/bin/env python3
"""
Production Validation Script for NIFTY Signals

Quick validation script to check if all components are working
in production environment.
"""

import sys
import os
import requests
from datetime import datetime

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection and table creation"""
    try:
        from app import create_app, db
        from app.models.nifty_signal import NiftySignal
        
        app = create_app()
        with app.app_context():
            # Test database connection
            db.engine.execute('SELECT 1')
            print("✅ Database connection: OK")
            
            # Check if nifty_signals table exists
            result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nifty_signals'")
            if result.fetchone():
                print("✅ NiftySignal table: EXISTS")
            else:
                print("❌ NiftySignal table: NOT FOUND")
                return False
                
            # Check signal count
            signal_count = NiftySignal.query.count()
            print(f"📊 Total signals in database: {signal_count}")
            
            return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_signal_service():
    """Test signal generation service"""
    try:
        from app import create_app
        from app.services.nifty_signal_service import NiftySignalGenerator
        
        app = create_app()
        with app.app_context():
            generator = NiftySignalGenerator()
            
            # Test signal generation
            result = generator.generate_current_signal()
            
            if result['success']:
                print("✅ Signal generation service: OK")
                if result['signal_generated']:
                    signal = result['signal']
                    print(f"📊 Generated signal: {signal['signal_type']} at ₹{signal['price']}")
                else:
                    print("ℹ️ No signal generated (no crossover)")
            else:
                print(f"⚠️ Signal generation: {result['message']}")
            
            return True
    except Exception as e:
        print(f"❌ Signal service test failed: {e}")
        return False

def test_api_endpoints(base_url="http://localhost:5000"):
    """Test API endpoints"""
    try:
        # Test signals dashboard
        response = requests.get(f"{base_url}/signals/", timeout=10)
        if response.status_code == 200:
            print("✅ Signals dashboard: ACCESSIBLE")
        else:
            print(f"❌ Signals dashboard: HTTP {response.status_code}")
            
        # Test API endpoint
        response = requests.get(f"{base_url}/api/signals", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signals API: OK ({len(data.get('signals', []))} signals)")
        else:
            print(f"❌ Signals API: HTTP {response.status_code}")
            
        # Test chart page
        response = requests.get(f"{base_url}/signals/chart", timeout=10)
        if response.status_code == 200:
            print("✅ Chart page: ACCESSIBLE")
        else:
            print(f"❌ Chart page: HTTP {response.status_code}")
            
        return True
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def test_scheduler():
    """Test if scheduler is configured"""
    try:
        from app import create_app
        from app.services.signal_scheduler import init_signal_scheduler
        
        app = create_app()
        with app.app_context():
            # Try to initialize scheduler
            init_signal_scheduler(app)
            print("✅ Signal scheduler: CONFIGURED")
            return True
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🔍 NIFTY Signals Production Validation")
    print("=" * 50)
    print(f"🕐 Time: {datetime.now()}")
    print("")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Signal Service", test_signal_service),
        ("API Endpoints", lambda: test_api_endpoints()),
        ("Background Scheduler", test_scheduler)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            print("")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            print("")
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Production deployment is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
