#!/usr/bin/env python3
"""
Quick script to set the correct expiry dates via API
"""
import requests
import json

def set_correct_expiry():
    """Set the correct expiry dates"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🔧 Setting Correct Expiry Dates")
    print("=" * 40)
    
    # Set correct expiry dates
    expiry_data = {
        "nifty_expiry": "2025-12-02",      # Current expiry as per user
        "banknifty_expiry": "2025-12-02",  # Current expiry as per user
        "nifty_next_expiry": "2025-12-05",     # Next Thursday
        "banknifty_next_expiry": "2025-12-05"  # Next Thursday
    }
    
    try:
        response = requests.post(
            f"{base_url}/admin/bulk-set-expiry",
            headers={'Content-Type': 'application/json'},
            json=expiry_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Expiry dates updated successfully!")
                print(f"📅 NIFTY expiry set to: 2025-12-02")
                print(f"📅 BankNifty expiry set to: 2025-12-02")
                
                # Show results
                for result in data.get('results', []):
                    underlying = result.get('underlying')
                    setting_data = result.get('data', {})
                    current_expiry = setting_data.get('current_expiry')
                    print(f"   ✓ {underlying}: {current_expiry}")
                
            else:
                print(f"❌ Failed to update: {data.get('message')}")
        else:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n🔍 Verifying New Settings")
    print("-" * 30)
    
    # Verify NIFTY setting
    try:
        response = requests.get(f"{base_url}/admin/get-expiry/NIFTY", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                expiry_info = data['data']
                current_expiry = expiry_info.get('current_expiry')
                is_default = expiry_info.get('is_default', False)
                status = "Default" if is_default else "Custom"
                print(f"✅ NIFTY: {current_expiry} ({status})")
            else:
                print(f"❌ NIFTY verification failed: {data.get('message')}")
        else:
            print(f"❌ NIFTY verification error: Status {response.status_code}")
    except Exception as e:
        print(f"❌ NIFTY verification error: {e}")
        
    # Verify BankNifty setting
    try:
        response = requests.get(f"{base_url}/admin/get-expiry/BANKNIFTY", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                expiry_info = data['data']
                current_expiry = expiry_info.get('current_expiry')
                is_default = expiry_info.get('is_default', False)
                status = "Default" if is_default else "Custom"
                print(f"✅ BankNifty: {current_expiry} ({status})")
            else:
                print(f"❌ BankNifty verification failed: {data.get('message')}")
        else:
            print(f"❌ BankNifty verification error: Status {response.status_code}")
    except Exception as e:
        print(f"❌ BankNifty verification error: {e}")
        
    print("\n🎯 Now all option chains will use 2025-12-02 as expiry!")
    print("Visit the dashboard to see the updated data.")

if __name__ == "__main__":
    set_correct_expiry()
