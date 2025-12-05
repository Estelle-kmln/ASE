import requests
import time
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8443"

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False

print("Testing comprehensive user action logging...")
print("=" * 80)

# 1. Register a new user
print("\n1. Testing user registration...")
username = f"logtest_{int(time.time())}"
resp = session.post(f"{BASE_URL}/api/auth/register", json={"username": username, "password": "TestPass123"})
print(f"   Registered {username}: {resp.status_code}")

# 2. Try to register duplicate (should fail and be logged)
print("\n2. Testing duplicate registration (should fail)...")
resp = session.post(f"{BASE_URL}/api/auth/register", json={"username": username, "password": "TestPass123"})
print(f"   Duplicate registration attempt: {resp.status_code}")

# 3. Login with wrong password (should fail and be logged)
print("\n3. Testing failed login...")
resp = session.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": "WrongPassword"})
print(f"   Failed login: {resp.status_code}")

# 4. Successful login
print("\n4. Testing successful login...")
resp = session.post(f"{BASE_URL}/api/auth/login", json={"username": username, "password": "TestPass123"})
token = resp.json()['access_token']
print(f"   Successful login: {resp.status_code}")

# 5. View profile
print("\n5. Testing profile view...")
resp = session.get(f"{BASE_URL}/api/auth/profile", headers={"Authorization": f"Bearer {token}"})
print(f"   Profile viewed: {resp.status_code}")

# 6. Change password
print("\n6. Testing password change...")
resp = session.put(f"{BASE_URL}/api/auth/profile", headers={"Authorization": f"Bearer {token}"}, json={"password": "NewTestPass123"})
print(f"   Password changed: {resp.status_code}")

# 7. Try unauthorized admin access
print("\n7. Testing unauthorized admin access...")
resp = session.get(f"{BASE_URL}/api/admin/users", headers={"Authorization": f"Bearer {token}"})
print(f"   Unauthorized admin access attempt: {resp.status_code}")

# 8. Create a game
print("\n8. Testing game creation...")
resp = session.post(f"{BASE_URL}/api/games", headers={"Authorization": f"Bearer {token}"}, json={"player2_name": "admin"})
if resp.status_code == 201:
    game_id = resp.json()['game_id']
    print(f"   Game created: {resp.status_code} (ID: {game_id})")
    
    # 9. Cancel the game
    print("\n9. Testing game cancellation...")
    resp = session.post(f"{BASE_URL}/api/games/{game_id}/cancel", headers={"Authorization": f"Bearer {token}"})
    print(f"   Game cancelled: {resp.status_code}")

# 10. Admin views logs
print("\n10. Testing admin log viewing...")
admin_resp = session.post(f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "Admin123!"})
admin_token = admin_resp.json()['access_token']
resp = session.get(f"{BASE_URL}/api/logs/list?page=0&size=20", headers={"Authorization": f"Bearer {admin_token}"})
print(f"   Admin viewed logs: {resp.status_code}")

# 11. Admin searches logs
print("\n11. Testing admin log search...")
resp = session.get(f"{BASE_URL}/api/logs/search?query={username}", headers={"Authorization": f"Bearer {admin_token}"})
print(f"   Admin searched logs: {resp.status_code}")

# Wait a moment for logs to be written
time.sleep(1)

# Display all recent logs
print("\n" + "=" * 80)
print("RECENT LOGS:")
print("=" * 80)
logs = requests.get(f"{BASE_URL}/api/logs/list?page=0&size=25", headers={"Authorization": f"Bearer {admin_token}"}).json()

for log in logs[:15]:
    timestamp = log['timestamp'][:19] if log['timestamp'] else 'N/A'
    action = log['action']
    user = log.get('username', 'N/A')
    details = log.get('details', '')
    print(f"{timestamp} | {action:30s} | {user:20s}")
    if details:
        print(f"  └─ {details}")

print("\n" + "=" * 80)
print("✓ All logging tests completed!")
print("=" * 80)
