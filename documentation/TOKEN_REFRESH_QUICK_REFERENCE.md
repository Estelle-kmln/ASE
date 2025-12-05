# Token Refresh Quick Reference

## For Developers: How to Use Token Refresh

### Frontend - Making Authenticated API Calls

#### ✅ Recommended: Use authenticatedFetch()
```javascript
// Automatically handles token refresh and retries
const response = await window.TokenManagement.authenticatedFetch(
    'http://localhost:8080/api/games',
    {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    }
);
```

#### ⚠️ Fallback Pattern (for compatibility)
```javascript
const fetchFunc = window.TokenManagement ? 
    window.TokenManagement.authenticatedFetch : fetch;

const headers = { 'Content-Type': 'application/json' };

// Add Authorization header only if not using TokenManagement
if (!window.TokenManagement) {
    const token = localStorage.getItem('token');
    headers['Authorization'] = `Bearer ${token}`;
}

const response = await fetchFunc(url, { headers });
```

### Frontend - Storing Tokens After Login/Register

```javascript
// After successful login/register
const data = await response.json();

if (window.TokenManagement) {
    window.TokenManagement.storeAuthTokens(data);
} else {
    // Fallback
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.user));
}
```

### Frontend - Logout

```javascript
function logout() {
    if (window.TokenManagement) {
        window.TokenManagement.logout(); // Revokes tokens on server
    } else {
        // Fallback
        localStorage.clear();
        window.location.href = 'login.html';
    }
}
```

### Frontend - Initialize on Page Load

```javascript
// In your main JS file, after DOM ready
if (window.TokenManagement) {
    window.TokenManagement.initializeTokenManagement();
}
```

### Backend - New Endpoints

#### Refresh Token
```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}

# Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 7200
}
```

#### Logout with Revocation
```bash
POST /api/auth/logout
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "refresh_token": "eyJ..."  # Optional, revokes all if omitted
}

# Response:
{
  "message": "Logged out successfully"
}
```

## HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Your Page</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <!-- Your content -->
    
    <!-- IMPORTANT: Load token-management.js BEFORE your page script -->
    <script src="js/token-management.js"></script>
    <script src="js/your-page.js"></script>
</body>
</html>
```

## Common Patterns

### Check Authentication Status
```javascript
if (!window.TokenManagement.isAuthenticated()) {
    window.location.href = 'login.html';
}
```

### Manual Token Refresh
```javascript
// Usually not needed - happens automatically
const success = await window.TokenManagement.refreshAccessToken();
if (!success) {
    // Redirect to login
}
```

### Check Token Expiry
```javascript
if (window.TokenManagement.TokenStorage.isTokenExpiringSoon()) {
    console.log('Token expiring soon, will auto-refresh');
}
```

## What Happens Automatically

1. **Before API Call**: Token checked, refreshed if expiring in < 5 minutes
2. **On 401 Error**: Token refreshed, request automatically retried once
3. **Every 5 Minutes**: Background check and refresh if needed
4. **On Logout**: Refresh token revoked on server

## Configuration

### Access Token Lifetime
File: `microservices/auth-service/app.py`
```python
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)
```

### Refresh Token Lifetime
```python
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
```

### Frontend Refresh Buffer
File: `frontend/js/token-management.js`
```javascript
// Token refreshed when < 5 minutes remaining
const timeUntilExpiry = parseInt(expiry) - Date.now();
return timeUntilExpiry < (5 * 60 * 1000); // 5 minutes
```

## Troubleshooting

### Token not refreshing
- Check browser console for errors
- Verify `token-management.js` loaded first
- Check `localStorage` has `refresh_token`

### Still getting 401 errors
- Verify using `authenticatedFetch()` not plain `fetch()`
- Check refresh token not expired (> 30 days old)
- Look for `TOKEN_REFRESH_FAILED` in backend logs

### Multiple refresh requests
- Normal if multiple API calls happen simultaneously
- System prevents concurrent refreshes (only one at a time)

## Migration Checklist

When updating an existing page:

- [ ] Add `<script src="js/token-management.js"></script>` before page script
- [ ] Replace `fetch()` with `authenticatedFetch()`
- [ ] Update logout to use `TokenManagement.logout()`
- [ ] Add `initializeTokenManagement()` call
- [ ] Remove manual `Authorization` header (done by authenticatedFetch)
- [ ] Test token refresh by setting short expiry

## Testing Token Refresh

1. **Set short expiry** (for testing):
   ```python
   app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=2)
   ```

2. **Login and wait**: Token will auto-refresh after ~1.5 minutes

3. **Check console**: Look for "Refreshing access token..." message

4. **Monitor logs**: Check for `TOKEN_REFRESHED` action

5. **Verify**: New token stored in `localStorage`

## API Response Format

### Login/Register Response
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "expires_in": 7200,
  "user": {
    "id": 1,
    "username": "testuser"
  }
}
```

### Refresh Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer",
  "expires_in": 7200
}
```

### Error Response
```json
{
  "error": "Invalid or expired refresh token"
}
```

## Database Queries

### View Active Refresh Tokens
```sql
SELECT rt.id, u.username, rt.expires_at, rt.created_at, rt.revoked
FROM refresh_tokens rt
JOIN users u ON rt.user_id = u.id
WHERE rt.revoked = FALSE
ORDER BY rt.created_at DESC;
```

### Count Tokens by User
```sql
SELECT u.username, COUNT(rt.id) as token_count
FROM users u
LEFT JOIN refresh_tokens rt ON u.id = rt.user_id
WHERE rt.revoked = FALSE
GROUP BY u.username
ORDER BY token_count DESC;
```

### Clean Expired Tokens
```sql
DELETE FROM refresh_tokens 
WHERE expires_at < CURRENT_TIMESTAMP OR revoked = TRUE;
```

## Monitoring Commands

### View Auth Service Logs
```powershell
# Follow logs in real-time
docker logs -f microservices-auth-service-1

# Last 100 lines
docker logs microservices-auth-service-1 --tail 100

# Search for refresh events
docker logs microservices-auth-service-1 | Select-String "TOKEN_REFRESH"
```

### Check Database
```powershell
docker exec -it microservices-postgresql-1 psql -U gameuser -d battlecards
```

### View Network Requests (Browser)
1. Open DevTools (F12)
2. Go to Network tab
3. Look for `/api/auth/refresh` calls
4. Check response status (should be 200)

## Common Use Cases

### Case 1: Making an API Call
```javascript
const response = await window.TokenManagement.authenticatedFetch(
    'http://localhost:8080/api/games/user/johndoe',
    { method: 'GET' }
);
const data = await response.json();
```

### Case 2: Posting Data
```javascript
const response = await window.TokenManagement.authenticatedFetch(
    'http://localhost:8080/api/profile',
    {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'new@email.com' })
    }
);
```

### Case 3: Handling Errors
```javascript
try {
    const response = await window.TokenManagement.authenticatedFetch(url);
    if (!response.ok) {
        console.error('Request failed:', response.status);
    }
    const data = await response.json();
} catch (error) {
    console.error('Network error:', error);
}
```

## Security Best Practices

1. **Always use HTTPS** in production
2. **Never log tokens** in production code
3. **Validate tokens** on every backend request
4. **Revoke tokens** on logout
5. **Monitor** for suspicious refresh patterns
6. **Rate limit** refresh endpoint
7. **Rotate tokens** regularly

## Quick Debug Checklist

Token not working? Check:
1. ✅ `token-management.js` loaded in HTML
2. ✅ `localStorage` has all required tokens
3. ✅ Token not expired (check `token_expiry`)
4. ✅ Using `authenticatedFetch()` not plain `fetch()`
5. ✅ Backend service is running
6. ✅ No errors in browser console
7. ✅ Check backend logs for errors

## Need Help?

Check the other documentation:
- `TOKEN_REFRESH_COMPLETE.md` - Test results summary
- `TOKEN_REFRESH_TESTING.md` - All testing methods
- `TOKEN_REFRESH_IMPLEMENTATION.md` - Full technical details
