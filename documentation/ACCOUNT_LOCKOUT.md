# Account Lockout Security Feature

## Overview

The account lockout mechanism protects user accounts from brute-force attacks by temporarily locking accounts after multiple failed login attempts.

## Security Parameters

- **Failed Attempts Threshold**: 3 attempts
- **Lockout Duration**: 15 minutes
- **HTTP Status Code**: 423 (Locked)

## How It Works

### Failed Login Attempts

1. **First Failed Attempt**
   - Counter increments to 1
   - Returns HTTP 401 with `remaining_attempts: 2`
   - User can try again

2. **Second Failed Attempt**
   - Counter increments to 2
   - Returns HTTP 401 with `remaining_attempts: 1`
   - User receives warning

3. **Third Failed Attempt**
   - Account is locked for 15 minutes
   - Returns HTTP 423 (Locked) with:
     - `locked_until`: ISO timestamp when lock expires
     - `retry_after`: Seconds until account unlocks

### During Lockout Period

- All login attempts return HTTP 423 (Locked)
- Even correct passwords are rejected
- Lock timer continues until expiration

### After Lockout Expires

- Failed attempts counter resets to 0
- User can attempt login normally
- Account automatically unlocks

### Successful Login

- Resets failed attempts counter to 0
- Clears any lockout status
- Clears `last_failed_login` timestamp

## Database Schema

New columns added to `users` table:

```sql
failed_login_attempts    INTEGER      DEFAULT 0
account_locked_until     TIMESTAMP    NULL
last_failed_login        TIMESTAMP    NULL
```

## API Response Examples

### Failed Login (Attempts Remaining)

**Request:**
```json
POST /api/auth/login
{
  "username": "testuser",
  "password": "wrong_password"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid username or password",
  "remaining_attempts": 2
}
```

### Account Locked

**Request:**
```json
POST /api/auth/login
{
  "username": "testuser",
  "password": "any_password"
}
```

**Response (423 Locked):**
```json
{
  "error": "Account locked due to multiple failed login attempts",
  "locked_until": "2025-12-05T15:30:00.000000",
  "retry_after": 900
}
```

## Security Logging

All lockout events are logged to the `logs` table:

- `LOGIN_FAILED`: Each failed login attempt with counter
- `ACCOUNT_LOCKED`: When account is locked with timestamp
- `LOGIN_BLOCKED`: When login is attempted on locked account
- `USER_LOGIN`: Successful login (resets counter)

## Testing

Run the comprehensive test suite:

```bash
python tests/test_account_lockout.py
```

### Test Coverage

1. **Account Lockout Test**
   - Verifies 3 failed attempts trigger lockout
   - Confirms HTTP 423 status code
   - Validates locked_until timestamp
   - Ensures correct password doesn't bypass lockout

2. **Counter Reset Test**
   - Confirms successful login resets counter
   - Verifies counter starts fresh after successful login

## Frontend Integration

### Live Countdown Timer (Implemented)

The frontend includes a **live countdown timer** that automatically updates every 60 seconds:

**Features:**
- ✅ Displays remaining lockout time in minutes/seconds
- ✅ Updates automatically every 60 seconds
- ✅ Disables login button during lockout
- ✅ Re-enables button when timer expires
- ✅ Shows visual feedback (grayed out button)

**User Experience:**
```
Initial: "🔒 Account locked. Please try again in 15 minutes."
After 1 min: "🔒 Account locked. Please try again in 14 minutes."
After 14 min: "🔒 Account locked. Please try again in 1 minute."
After 15 min: "✓ Account lockout period has ended. You may try logging in again."
```

### Implementation Code

```javascript
// State management
let lockoutTimer = null;
let lockoutEndTime = null;

// Handle account lockout with countdown
function handleAccountLockout(username, data) {
    lockoutEndTime = new Date(data.locked_until);
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.style.opacity = '0.5';
    
    // Show initial lockout message
    updateLockoutDisplay();
    
    // Update display every 60 seconds
    lockoutTimer = setInterval(() => {
        updateLockoutDisplay();
    }, 60000);
}

function updateLockoutDisplay() {
    const remainingMs = lockoutEndTime - new Date();
    
    if (remainingMs <= 0) {
        clearLockoutTimer();
        showAlert('Account unlocked. You may try again.', 'success');
        return;
    }
    
    const remainingMinutes = Math.ceil(remainingMs / 60000);
    showAlert(`Account locked. Try again in ${remainingMinutes} minutes.`, 'error');
}
```

### Handling Failed Login

```javascript
try {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  if (response.status === 401) {
    // Failed login
    const remaining = data.remaining_attempts;
    if (remaining) {
      alert(`Invalid credentials. ${remaining} attempts remaining.`);
    } else {
      alert('Invalid username or password.');
    }
  } else if (response.status === 423) {
    // Account locked - start countdown timer
    handleAccountLockout(username, data);
  }
} catch (error) {
  console.error('Login error:', error);
}
```

## Security Considerations

### Benefits

✅ **Brute Force Protection**: Prevents automated password guessing
✅ **Account Safety**: Protects legitimate users from unauthorized access
✅ **User Feedback**: Informs users about remaining attempts and lockout time
✅ **Automatic Recovery**: No admin intervention needed
✅ **Audit Trail**: All events logged for security monitoring
✅ **Live Updates**: Users see real-time countdown of lockout period

### Best Practices

1. **Monitor Logs**: Review `ACCOUNT_LOCKED` events regularly
2. **User Communication**: Inform users about the security policy
3. **Admin Tools**: Consider adding unlock capability for support
4. **Rate Limiting**: Combine with IP-based rate limiting for enhanced security
5. **Notification**: Consider email alerts for locked accounts

## Configuration

To adjust lockout parameters, modify in `app.py`:

```python
# Change lockout duration (default: 15 minutes)
lockout_duration = timedelta(minutes=15)

# Change failed attempts threshold (default: 3)
if failed_attempts >= 3:
```

## Migration

Run the migration script to add lockout columns:

```bash
# Migration happens automatically on container startup
# Or run manually:
psql -h localhost -U gameuser -d battlecards -f microservices/database/06-add-account-lockout.sql
```

## Troubleshooting

### Manually Unlock an Account

```sql
-- Check lockout status
SELECT username, failed_login_attempts, account_locked_until 
FROM users 
WHERE username = 'locked_user';

-- Manually unlock
UPDATE users 
SET failed_login_attempts = 0, 
    account_locked_until = NULL,
    last_failed_login = NULL
WHERE username = 'locked_user';
```

### View Lockout Events

```sql
-- Recent lockout events
SELECT timestamp, action, username, details 
FROM logs 
WHERE action IN ('ACCOUNT_LOCKED', 'LOGIN_BLOCKED', 'LOGIN_FAILED')
ORDER BY timestamp DESC 
LIMIT 20;
```

## Future Enhancements

Potential improvements:

1. **Progressive Delays**: Increase lockout duration with repeated violations
2. **IP-Based Tracking**: Track attempts by IP address
3. **CAPTCHA**: Require CAPTCHA after first failed attempt
4. **Email Notifications**: Alert users when account is locked
5. **Admin Dashboard**: View and manage locked accounts
6. **Whitelist**: Allow certain IPs to bypass restrictions
7. **Customizable Duration**: Let admins configure lockout time

## Compliance

This implementation supports:

- **OWASP**: Authentication best practices
- **GDPR**: User account protection requirements
- **SOC 2**: Access control and monitoring requirements
- **ISO 27001**: Information security management
