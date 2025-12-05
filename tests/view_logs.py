import requests

# Login as admin
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

admin_resp = requests.post('https://localhost:8443/api/auth/login', json={'username': 'admin', 'password': 'Admin123!'}, verify=False)
token = admin_resp.json()['access_token']

# Get recent logs
logs = requests.get('https://localhost:8443/api/logs/list?page=0&size=15', headers={'Authorization': f'Bearer {token}'}, verify=False).json()

print("Recent User Action Logs:")
print("=" * 80)
for log in logs:
    print(f"{log['timestamp'][:19]}: {log['action']:30s} {log.get('username', 'N/A'):15s}")
    if log.get('details'):
        print(f"  └─ {log['details']}")
