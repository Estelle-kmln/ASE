# Token Refresh Testing Guide

## ✅ Your services are now running with token refresh enabled!

## Quick Testing Methods

### Method 1: Browser Manual Test (Easiest)

1. **Open the application**: http://localhost:8080/login.html

2. **Open Browser DevTools** (F12):
   - Go to **Console** tab (to see logs)
   - Go to **Application** > **Local Storage** > http://localhost:8080

3. **Register or Login**:
   - Create a new account or login
   - After successful login, check Local Storage:
     - ✅ `token` (access token)
     - ✅ `refresh_token` (NEW!)
     - ✅ `token_expiry` (NEW!)
     - ✅ `user` (user data)

4. **Verify Token Refresh Console Logs**:
   - Look for these messages in Console:
     ```
     Auth check passed
     Token: exists
     ```

5. **Navigate around** (index.html, profile.html):
   - Should work seamlessly without re-login

### Method 2: API Testing with cURL/PowerShell

#### Test Login (returns refresh token):
```powershell
$response = Invoke-RestMethod -Uri 'http://localhost:8080/api/auth/login' `
    -Method POST `
    -ContentType 'application/json' `
    -Body '{"username":"testuser","password":"Test@123"}'

$response | ConvertTo-Json

# Should see:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",  <-- NEW!
#   "token_type": "bearer",
#   "expires_in": 7200,
#   "user": {...}
# }
```

#### Test Token Refresh:
```powershell
$refreshToken = $response.refresh_token

$newTokens = Invoke-RestMethod -Uri 'http://localhost:8080/api/auth/refresh' `
    -Method POST `
    -ContentType 'application/json' `
    -Body "{`"refresh_token`":`"$refreshToken`"}"

$newTokens | ConvertTo-Json

# Should see new access token:
# {
#   "access_token": "eyJ...",  <-- NEW ACCESS TOKEN
#   "token_type": "bearer",
#   "expires_in": 7200
# }
```

#### Test Logout with Token Revocation:
```powershell
$accessToken = $response.access_token

Invoke-RestMethod -Uri 'http://localhost:8080/api/auth/logout' `
    -Method POST `
    -ContentType 'application/json' `
    -Headers @{ "Authorization" = "Bearer $accessToken" } `
    -Body "{`"refresh_token`":`"$refreshToken`"}"

# Should see:
# { "message": "Logged out successfully" }

# Now try using the refresh token (should fail):
Invoke-RestMethod -Uri 'http://localhost:8080/api/auth/refresh' `
    -Method POST `
    -ContentType 'application/json' `
    -Body "{`"refresh_token`":`"$refreshToken`"}"

# Should get error: "Invalid or expired refresh token"
```

### Method 3: Run Automated Test

```powershell
cd tests
python test_token_refresh.py
```

Expected output:
```
🧪 Testing Token Refresh Mechanism
============================================================
1️⃣ Registering test user...
   ✅ User registered
   📝 Access token received
   🔑 Refresh token received
   ⏱️  Expires in: 7200 seconds

2️⃣ Testing access token...
   ✅ Access token works!

3️⃣ Testing token refresh...
   ✅ Token refresh successful!

4️⃣ Testing new access token...
   ✅ New access token works!

5️⃣ Testing logout with token revocation...
   ✅ Logout successful, refresh token revoked

6️⃣ Verifying revoked refresh token fails...
   ✅ Revoked refresh token correctly rejected!

============================================================
✅ Token Refresh Mechanism Test Complete!
============================================================
```

### Method 4: Test Automatic Refresh

Currently, access tokens expire in **2 hours**. To test automatic refresh:

#### Option A: Manually expire token for quick test
1. Login to app
2. Open DevTools > Application > Local Storage
3. Set `token_expiry` to a past timestamp:
   ```javascript
   localStorage.setItem('token_expiry', Date.now() - 10000);
   ```
4. Reload the page or make an API call
5. Watch Console for: "Refreshing access token..."
6. Should auto-refresh and continue working

#### Option B: Temporary short expiry (for testing)
Modify `microservices/auth-service/app.py` temporarily:
```python
# Change this line:
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=2)  # 2 minutes for testing
```

Then:
1. Rebuild services: `docker compose up -d --build auth-service`
2. Login
3. Wait 2 minutes
4. Watch automatic refresh happen

#### Option C: Wait naturally (2 hours)
1. Login and use the app
2. Wait ~1 hour 55 minutes
3. Keep console open
4. You'll see: "Token expiring soon, refreshing..."
5. Make an API call - should work seamlessly

## What to Look For

### ✅ Success Indicators

**In Browser Console:**
- "Refreshing access token..."
- "Access token refreshed successfully"

**In Local Storage:**
- `refresh_token` exists
- `token_expiry` timestamp updates after refresh
- `token` changes (new access token)

**In Network Tab:**
- POST to `/api/auth/refresh` (200 OK)
- Subsequent API calls succeed

**In Backend Logs:**
Check auth-service logs:
```powershell
docker logs microservices-auth-service-1 --tail 50
```

Look for:
- `TOKEN_REFRESHED` entries
- `USER_LOGIN` with refresh token stored
- `USER_LOGOUT` with token revocation

### ❌ Failure Indicators

- "Failed to refresh token"
- "Invalid or expired refresh token"
- Automatic redirect to login
- 401 errors that don't retry

## Database Verification

Check that refresh tokens are stored:

```powershell
docker exec -it microservices-postgresql-1 psql -U gameuser -d battlecards
```

```sql
-- View refresh tokens
SELECT id, user_id, expires_at, created_at, revoked 
FROM refresh_tokens 
ORDER BY created_at DESC 
LIMIT 10;

-- Count active tokens
SELECT COUNT(*) FROM refresh_tokens WHERE revoked = FALSE;

-- View tokens with user info
SELECT rt.id, u.username, rt.expires_at, rt.revoked 
FROM refresh_tokens rt
JOIN users u ON rt.user_id = u.id
ORDER BY rt.created_at DESC;
```

Exit with: `\q`

## Testing Scenarios

### Scenario 1: Normal Login Flow
1. ✅ Login
2. ✅ Receive both access and refresh tokens
3. ✅ Token stored in localStorage
4. ✅ Navigate to different pages
5. ✅ All API calls work

### Scenario 2: Token Expiration & Auto-Refresh
1. ✅ Login
2. ✅ Wait for token to expire (or manually expire)
3. ✅ Make API call
4. ✅ Token automatically refreshes
5. ✅ API call succeeds
6. ✅ New token stored

### Scenario 3: Logout & Revocation
1. ✅ Login
2. ✅ Logout
3. ✅ Refresh token revoked on server
4. ✅ Try to use refresh token
5. ✅ Fails with error

### Scenario 4: Multiple Tabs
1. ✅ Open app in two tabs
2. ✅ Login in tab 1
3. ✅ Use tab 2 (should work - same localStorage)
4. ✅ Token refreshes in one tab
5. ✅ Other tab picks up new token

### Scenario 5: Expired Refresh Token
1. ✅ Login
2. ✅ Wait 30+ days (or manually revoke token in DB)
3. ✅ Try to use refresh token
4. ✅ Fails, redirects to login

## Monitoring & Logs

### View Auth Service Logs
```powershell
# Follow logs in real-time
docker logs -f microservices-auth-service-1

# Last 100 lines
docker logs microservices-auth-service-1 --tail 100
```

Look for:
- `USER_LOGIN` - User logged in
- `TOKEN_REFRESHED` - Token was refreshed
- `TOKEN_REFRESH_FAILED` - Refresh failed
- `USER_LOGOUT` - User logged out with token revocation

### View Database Logs
```powershell
docker logs microservices-postgresql-1 --tail 50
```

## Performance Testing

Test with multiple concurrent users:

```powershell
# In tests directory
cd tests

# Run locust performance test
# This will test login, token refresh, and API calls
python -m locust -f locustfile.py --host=http://localhost:8080
```

Then open: http://localhost:8089

## Common Issues & Solutions

### Issue: No refresh_token in localStorage
**Solution**: Clear localStorage and login again. Old sessions don't have refresh tokens.

### Issue: "Invalid or expired refresh token"
**Solution**: 
- Check if token is > 30 days old
- Check database: `SELECT * FROM refresh_tokens WHERE revoked = FALSE`
- Login again to get new tokens

### Issue: Token not auto-refreshing
**Solution**:
- Check browser console for errors
- Verify `token-management.js` loaded before other scripts
- Check `token_expiry` in localStorage is set

### Issue: 401 errors still occurring
**Solution**:
- Verify using `authenticatedFetch()` not plain `fetch()`
- Check that `_isRetry` flag works
- Review network tab for refresh attempts

## Advanced Testing

### Test with Short Expiry (2 minutes)
1. Edit `microservices/auth-service/app.py`:
   ```python
   app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=2)
   ```

2. Rebuild:
   ```powershell
   cd microservices
   docker compose up -d --build auth-service
   ```

3. Login and wait 2 minutes
4. Watch automatic refresh

### Load Test Token Refresh
Use provided test script:
```powershell
cd tests
python test_auth_service.py
```

## Success Criteria

Your token refresh mechanism is working correctly if:

- ✅ Login returns both `access_token` and `refresh_token`
- ✅ Refresh token stored in database
- ✅ Token automatically refreshes when expiring
- ✅ 401 errors trigger refresh and retry
- ✅ Logout revokes refresh token
- ✅ Expired refresh tokens are rejected
- ✅ Users stay logged in for 30 days
- ✅ No disruption to user experience

## Next Steps

1. ✅ Test in browser (easiest)
2. ✅ Verify tokens in localStorage
3. ✅ Check database for refresh_tokens table
4. ✅ Monitor logs for TOKEN_REFRESHED
5. ✅ Test logout and revocation
6. ⏳ Wait for auto-refresh or manually trigger it
7. 🎉 Enjoy seamless token refresh!

## Need Help?

Check the other documentation:
- `TOKEN_REFRESH_COMPLETE.md` - Test results summary
- `TOKEN_REFRESH_IMPLEMENTATION.md` - Full technical details
- `TOKEN_REFRESH_QUICK_REFERENCE.md` - Developer quick start
