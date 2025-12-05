"""
Quick test script to verify token refresh mechanism is working
"""

import requests
import json
import time

API_BASE = "http://localhost:8080/api/auth"

def test_token_refresh():
    print("🧪 Testing Token Refresh Mechanism\n")
    print("=" * 60)
    
    # Step 1: Register a test user
    print("\n1️⃣ Registering test user...")
    username = f"test_refresh_{int(time.time())}"
    password = "TestPass@123"
    
    try:
        register_response = requests.post(
            f"{API_BASE}/register",
            json={"username": username, "password": password}
        )
        
        if register_response.status_code == 201:
            data = register_response.json()
            print(f"   ✅ User registered: {username}")
            print(f"   📝 Access token: {data['access_token'][:20]}...")
            print(f"   🔑 Refresh token: {data['refresh_token'][:20]}...")
            print(f"   ⏱️  Expires in: {data['expires_in']} seconds")
            
            access_token = data['access_token']
            refresh_token = data['refresh_token']
        else:
            print(f"   ❌ Registration failed: {register_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 2: Verify access token works
    print("\n2️⃣ Testing access token...")
    try:
        profile_response = requests.get(
            f"{API_BASE}/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if profile_response.status_code == 200:
            user_data = profile_response.json()
            print(f"   ✅ Access token works! User: {user_data['user']['username']}")
        else:
            print(f"   ❌ Access token failed: {profile_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 3: Test token refresh
    print("\n3️⃣ Testing token refresh...")
    try:
        refresh_response = requests.post(
            f"{API_BASE}/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if refresh_response.status_code == 200:
            new_data = refresh_response.json()
            print(f"   ✅ Token refresh successful!")
            print(f"   📝 New access token: {new_data['access_token'][:20]}...")
            print(f"   ⏱️  Expires in: {new_data['expires_in']} seconds")
            
            new_access_token = new_data['access_token']
            
            # Verify new token works
            print("\n4️⃣ Testing new access token...")
            profile_response2 = requests.get(
                f"{API_BASE}/profile",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            
            if profile_response2.status_code == 200:
                print(f"   ✅ New access token works!")
            else:
                print(f"   ❌ New token failed: {profile_response2.text}")
                
        else:
            print(f"   ❌ Token refresh failed: {refresh_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 5: Test logout with token revocation
    print("\n5️⃣ Testing logout with token revocation...")
    try:
        logout_response = requests.post(
            f"{API_BASE}/logout",
            headers={"Authorization": f"Bearer {new_access_token}"},
            json={"refresh_token": refresh_token}
        )
        
        if logout_response.status_code == 200:
            print(f"   ✅ Logout successful, refresh token revoked")
        else:
            print(f"   ⚠️  Logout response: {logout_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 6: Verify refresh token is now invalid
    print("\n6️⃣ Verifying revoked refresh token fails...")
    try:
        refresh_response2 = requests.post(
            f"{API_BASE}/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if refresh_response2.status_code == 401:
            print(f"   ✅ Revoked refresh token correctly rejected!")
        else:
            print(f"   ⚠️  Unexpected response: {refresh_response2.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Token Refresh Mechanism Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_token_refresh()
