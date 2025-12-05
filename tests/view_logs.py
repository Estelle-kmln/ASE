import requests

# Login as admin
admin_resp = requests.post('http://localhost:8080/api/auth/login', json={'username': 'admin', 'password': 'Admin123!'})
token = admin_resp.json()['access_token']

# Get recent logs
logs = requests.get('http://localhost:8080/api/logs/list?page=0&size=15', headers={'Authorization': f'Bearer {token}'}).json()

print("Recent User Action Logs:")
print("=" * 80)
for log in logs:
    print(f"{log['timestamp'][:19]}: {log['action']:30s} {log.get('username', 'N/A'):15s}")
    if log.get('details'):
        print(f"  └─ {log['details']}")
