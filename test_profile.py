import requests
import urllib3

urllib3.disable_warnings()

# Register
r1 = requests.post('https://localhost:8443/api/auth/register', 
                   json={'username': 'testprofile999', 'password': 'Test12345!'}, 
                   verify=False)
print(f"Register: {r1.status_code}")

# Login
r2 = requests.post('https://localhost:8443/api/auth/login', 
                   json={'username': 'testprofile999', 'password': 'Test12345!'}, 
                   verify=False)
print(f"Login: {r2.status_code}")
if r2.status_code == 200:
    token = r2.json()['access_token']
    print(f"Token: {token[:20]}...")
    
    # Get profile
    r3 = requests.get('https://localhost:8443/api/auth/profile', 
                     headers={'Authorization': f'Bearer {token}'}, 
                     verify=False)
    print(f"Profile status: {r3.status_code}")
    print(f"Profile response: {r3.text}")
