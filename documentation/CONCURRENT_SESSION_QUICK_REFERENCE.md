# 🔐 Concurrent Session Management - Quick Reference

## Current Mode: STRICT (One Session Per User)

---

## 🚀 Quick Start

### What Happens Now?
- Users can only have **ONE active session** at a time
- Attempting to login from another device → **REJECTED**
- Must logout from current device before logging in elsewhere

---

## 📍 API Endpoints

### View Your Active Sessions
```bash
GET /api/auth/sessions
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "sessions": [
    {
      "id": 1,
      "device": "Chrome on Windows",
      "ip_address": "192.168.1.100",
      "created_at": "2025-12-05T12:00:00",
      "last_used_at": "2025-12-05T14:30:00"
    }
  ],
  "total": 1
}
```

### Logout from Specific Device
```bash
DELETE /api/auth/sessions/{session_id}
Authorization: Bearer {access_token}
```

### Logout from All Devices
```bash
POST /api/auth/sessions/revoke-all
Authorization: Bearer {access_token}
```

---

## 🔍 What Gets Tracked?

For each session, we track:
- **Device Info** - Browser and OS (e.g., "Chrome on Windows")
- **IP Address** - Where the login came from
- **Created At** - When the session started
- **Last Used At** - Last activity timestamp

---

## ❗ Error Codes

### 409 Conflict - Active Session Exists
```json
{
  "error": "Another session is already active",
  "message": "You already have an active session. Please logout from your other device first.",
  "active_session": {
    "device": "Chrome on Windows",
    "ip_address": "192.168.1.100",
    "created_at": "2025-12-05T12:00:00"
  }
}
```

**What to do:**
1. Logout from the other device
2. OR use session management API to revoke the session remotely

---

## 🧪 Testing

### Run Automated Tests
```bash
python tests/test_concurrent_sessions.py
```

### Manual Test Flow
1. Login in Browser A ✅
2. Try to login in Browser B ❌ (Rejected)
3. Logout in Browser A
4. Try to login in Browser B ✅ (Success)

---

## 📊 Logging

Session activity is logged with these actions:
- `USER_LOGIN` - Successful login
- `LOGIN_REJECTED` - Concurrent session blocked
- `SESSION_REVOKED` - Manual session termination
- `ALL_SESSIONS_REVOKED` - Bulk logout

View logs:
```bash
python tests/view_logs.py --action LOGIN_REJECTED
```

---

## 💡 Common Scenarios

### Scenario 1: User Forgot to Logout at Work
**Problem:** User went home, tries to login on home computer  
**Solution:** 
- Use session management API to revoke work session
- Or wait for work session to expire (30 days)

### Scenario 2: Account Compromise Suspected
**Problem:** Unauthorized access detected  
**Solution:**
1. Call `/api/auth/sessions/revoke-all` immediately
2. Change password
3. Check logs for suspicious activity

### Scenario 3: Multiple Devices Needed
**Problem:** User needs to use both mobile and desktop  
**Solution:** 
- Current strict mode doesn't allow this
- User must logout/login when switching devices
- (Future enhancement: Limited mode allowing N devices)

---

## 🔧 Configuration

### Current Settings
- **Mode:** Strict (1 session only)
- **Access Token Expiry:** 2 hours
- **Refresh Token Expiry:** 30 days
- **Session Tracking:** Enabled

### To Modify Behavior
Edit `microservices/auth-service/app.py`:

Change `check_concurrent_session()` logic to implement different modes.

---

## 📈 Security Benefits

✅ **Prevents account takeover** - Attackers can't create additional sessions  
✅ **Detects unauthorized access** - User notified if someone tries to login  
✅ **Audit trail** - All session activity logged  
✅ **User control** - Can view and manage sessions  
✅ **Compliance** - Session tracking aids in security audits

---

## 🎯 Best Practices

### For Users:
1. Always logout when done
2. Regularly check active sessions
3. Revoke unknown sessions immediately
4. Report suspicious activity

### For Developers:
1. Monitor LOGIN_REJECTED logs for patterns
2. Set up alerts for multiple rejection attempts
3. Review session logs during security audits
4. Consider implementing email notifications for new logins

---

## 🚨 Troubleshooting

### "Cannot login - session already active"
**Check:** Are you logged in on another device?  
**Fix:** Logout from other device or use `/api/auth/sessions` to manage

### "Session revoked unexpectedly"
**Check:** Did someone logout remotely?  
**Fix:** Review logs and change password if suspicious

### "Device shows as Unknown"
**Check:** Browser/device might have unusual User-Agent  
**Info:** Functionality works fine, just cosmetic issue

---

## 📞 Support

**Documentation:** `documentation/CONCURRENT_SESSION_COMPLETE.md`  
**Tests:** `tests/test_concurrent_sessions.py`  
**Logs:** Use `tests/view_logs.py` to investigate issues

---

## ✨ Features at a Glance

| Feature | Status | Description |
|---------|--------|-------------|
| Strict Mode | ✅ Active | Only 1 session per user |
| Device Tracking | ✅ Active | OS and browser detection |
| IP Tracking | ✅ Active | Location/network info |
| Session Management API | ✅ Active | View/revoke sessions |
| Activity Timestamps | ✅ Active | created_at & last_used_at |
| Security Logging | ✅ Active | All actions logged |
| Frontend Integration | ✅ Active | User-friendly error messages |

---

**Last Updated:** December 5, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅
