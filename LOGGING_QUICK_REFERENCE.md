# Quick Reference: User Action Logging

## 🎯 What's Been Implemented

Your Battle Cards application now logs **all important user actions** for security monitoring and control.

## 📊 Logged Actions Summary

| Action Type | Event | When It's Logged |
|-------------|-------|------------------|
| **Authentication** | USER_REGISTERED | New user signs up |
| | REGISTRATION_FAILED | Duplicate username attempt |
| | USER_LOGIN | Successful login |
| | LOGIN_FAILED | Wrong password/username |
| **Security** | PASSWORD_CHANGED | User changes password |
| | UNAUTHORIZED_ADMIN_ACCESS | Non-admin tries admin endpoint |
| **Game Actions** | GAME_CREATED | Player creates a game |
| | GAME_INVITATION_ACCEPTED | Player accepts invitation |
| | GAME_INVITATION_DECLINED | Player declines invitation |
| | GAME_INVITATION_CANCELLED | Creator cancels invitation |
| | DECK_SELECTED | Player selects their deck |
| | GAME_STARTED | Both players ready, game begins |
| | GAME_COMPLETED | Game finishes with winner |
| | GAME_ABANDONED | Game ends without winner |

## 🔍 How to View Logs

### Option 1: Admin Panel (Easiest)
1. Open http://localhost:8080/admin.html
2. Login with: `admin` / `Admin123!`
3. Click "View Logs"
4. Browse, search, and filter logs

### Option 2: Command Line
```bash
cd tests
python view_logs.py
```

### Option 3: API Direct
```bash
# Get admin token first
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin123!"}'

# Then view logs (use token from above)
curl http://localhost:8080/api/logs/list?page=0&size=20 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🚨 Security Alerts to Watch For

### Critical (Check Daily)
- **Multiple LOGIN_FAILED** from same user → Possible brute force
- **UNAUTHORIZED_ADMIN_ACCESS** → Privilege escalation attempt
- **Unusual PASSWORD_CHANGED** patterns → Account compromise

### Important (Check Weekly)
- **High REGISTRATION_FAILED** rate → Bot activity
- **Repeated GAME_ABANDONED** → Griefing behavior
- **Admin activity** → Audit trail

## ✅ Testing Verification

All logging has been tested and is working:
```bash
cd tests
python comprehensive_logging_test.py
```

## 📁 Key Files

- **Logs Storage**: Database table `logs`
- **Auth Service**: `microservices/auth-service/app.py`
- **Game Service**: `microservices/game-service/app.py`
- **Logs Service**: `microservices/logs-service/app.py`
- **Documentation**: `USER_LOGGING_SUMMARY.md`

## 💡 Quick Tips

1. **Search logs**: Use the search feature in admin panel or API
2. **Filter by user**: Search for username to see all their actions
3. **Time-based review**: Logs sorted by timestamp (newest first)
4. **Export data**: Use API to export logs for analysis

## 🎬 Example Usage

### Find all failed login attempts:
Search: "LOGIN_FAILED"

### Track a specific user's activity:
Search: "username123"

### Monitor admin actions:
Search: "ADMIN_"

### Security audit:
Search: "UNAUTHORIZED" or "FAILED"

## 📞 Need Help?

- Review full docs: `USER_LOGGING_SUMMARY.md`
- Check implementation: `LOGGING_IMPLEMENTATION_COMPLETE.md`
- Run tests: `tests/comprehensive_logging_test.py`
