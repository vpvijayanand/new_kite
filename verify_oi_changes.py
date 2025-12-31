#!/usr/bin/env python3
"""
Verification script to check if OI Change percentages are being calculated correctly
"""

import requests
import sys

def test_oi_change_percentages():
    """Test OI change percentage calculations for various strikes"""
    
    print("🔍 Verifying OI Change Percentage Calculations")
    print("=" * 60)
    
    # Get available strikes
    try:
        response = requests.get('http://127.0.0.1:5000/api/strikes/NIFTY')
        if response.status_code != 200:
            print("❌ Failed to get strikes data")
            return False
            
        strikes_data = response.json()
        if not strikes_data.get('success'):
            print("❌ Strikes API returned error")
            return False
            
        strikes = strikes_data['strikes'][:10]  # Test first 10 strikes
        print(f"📊 Testing {len(strikes)} strikes for CE and PE options...")
        print()
        
    except Exception as e:
        print(f"❌ Error getting strikes: {e}")
        return False
    
    # Test each strike for both CE and PE
    success_count = 0
    total_tests = len(strikes) * 2
    
    for i, strike in enumerate(strikes):
        print(f"Strike {strike}:")
        
        # Test CE
        try:
            response = requests.get(f'http://127.0.0.1:5000/api/oi-history/NIFTY/{strike}/CE')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data['summary']
                    oi_change = summary.get('total_oi_change', 0)
                    oi_change_pct = summary.get('total_oi_change_percent', 0)
                    first_oi = summary.get('first_oi', 0)
                    latest_oi = summary.get('latest_oi', 0)
                    
                    # Verify calculation
                    expected_pct = (oi_change / first_oi * 100) if first_oi > 0 else 0
                    
                    print(f"  CE: {oi_change:>8} change, {oi_change_pct:>6}% (Expected: {expected_pct:.2f}%) ✅")
                    success_count += 1
                else:
                    print(f"  CE: No data available - {data.get('message', 'Unknown error')}")
            else:
                print(f"  CE: API Error (HTTP {response.status_code})")
        except Exception as e:
            print(f"  CE: Exception - {e}")
        
        # Test PE
        try:
            response = requests.get(f'http://127.0.0.1:5000/api/oi-history/NIFTY/{strike}/PE')
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data['summary']
                    oi_change = summary.get('total_oi_change', 0)
                    oi_change_pct = summary.get('total_oi_change_percent', 0)
                    first_oi = summary.get('first_oi', 0)
                    latest_oi = summary.get('latest_oi', 0)
                    
                    # Verify calculation
                    expected_pct = (oi_change / first_oi * 100) if first_oi > 0 else 0
                    
                    print(f"  PE: {oi_change:>8} change, {oi_change_pct:>6}% (Expected: {expected_pct:.2f}%) ✅")
                    success_count += 1
                else:
                    print(f"  PE: No data available - {data.get('message', 'Unknown error')}")
            else:
                print(f"  PE: API Error (HTTP {response.status_code})")
        except Exception as e:
            print(f"  PE: Exception - {e}")
        
        print()
    
    # Summary
    print("=" * 60)
    print(f"📈 Results: {success_count}/{total_tests} tests successful")
    
    if success_count == total_tests:
        print("✅ All OI Change percentages are calculated correctly!")
        return True
    elif success_count > 0:
        print("⚠️  Some OI Change percentages working, others may have no data")
        return True
    else:
        print("❌ No OI Change percentages found - possible system issue")
        return False

def test_specific_example():
    """Test a specific example that should have data"""
    print("\n🎯 Testing specific example (NIFTY 26200 CE):")
    print("-" * 40)
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/oi-history/NIFTY/26200/CE')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data['summary']
                history = data.get('history', [])
                
                print(f"Strike: {data['strike_price']} {data['option_type']}")
                print(f"Records today: {len(history)}")
                print(f"First OI: {summary['first_oi']:,}")
                print(f"Latest OI: {summary['latest_oi']:,}")
                print(f"Total OI Change: {summary['total_oi_change']:,}")
                print(f"Total OI Change %: {summary['total_oi_change_percent']}%")
                
                # Show sample history records with percentages
                if history:
                    print("\nSample history records:")
                    for i, record in enumerate(history[-3:]):  # Last 3 records
                        print(f"  {record['timestamp']}: OI {record['oi']:,}, "
                              f"Change from start: {record['oi_change_from_start']:,} "
                              f"({record['oi_change_percent_from_start']}%)")
                
                return True
            else:
                print(f"❌ API Error: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 OI Change Percentage Verification Tool")
    print("=" * 60)
    
    # Test general functionality
    general_success = test_oi_change_percentages()
    
    # Test specific example
    specific_success = test_specific_example()
    
    print("\n" + "=" * 60)
    if general_success and specific_success:
        print("🎉 CONCLUSION: OI Change percentages are working correctly!")
        print("📝 If you're seeing 0% values, it's likely because:")
        print("   - The OI hasn't changed much during the selected time period")
        print("   - You're looking at a time when markets are closed")
        print("   - The strike you selected has minimal activity")
        sys.exit(0)
    else:
        print("⚠️  CONCLUSION: There may be issues with some calculations")
        sys.exit(1)
