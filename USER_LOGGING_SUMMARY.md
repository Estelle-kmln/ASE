# User Action Logging Implementation

## Overview
Comprehensive logging has been implemented across all microservices to track user actions for security monitoring and control from the game owner's perspective.

## Logged User Actions

### Authentication Service (`auth-service`)

#### User Registration and Login
- **USER_REGISTERED**: Logged when a new user successfully registers
  - Details: User ID of the newly created account
  
- **REGISTRATION_FAILED**: Logged when registration fails (username already exists)
  - Details: Reason for failure
  
- **USER_LOGIN**: Logged on successful user login
  - Details: Confirmation of successful login
  
- **LOGIN_FAILED**: Logged when login attempt fails (incorrect password or invalid username)
  - Details: "Invalid username or password"
  - **Security Note**: This is critical for detecting brute force attacks
  
- **PASSWORD_CHANGED**: Logged when a user changes their password
  - Details: Password change confirmation
  - **Security Note**: Important for detecting unauthorized account access

#### Admin Actions
- **UNAUTHORIZED_ADMIN_ACCESS**: Logged when a non-admin user attempts to access admin endpoints
  - Details: The endpoint name they tried to access
  - **Security Note**: Critical for detecting privilege escalation attempts
  
### Game Service (`game-service`)

#### Game Creation and Invitations
- **GAME_CREATED**: Logged when a player creates a new game
  - Details: Game ID and opponent username
  
- **GAME_INVITATION_ACCEPTED**: Logged when a player accepts a game invitation
  - Details: Game ID
  
- **GAME_INVITATION_DECLINED**: Logged when a player declines/ignores a game invitation
  - Details: Game ID
  
- **GAME_INVITATION_CANCELLED**: Logged when the game creator cancels their invitation
  - Details: Game ID

#### Game Progress
- **DECK_SELECTED**: Logged when a player selects their deck
  - Details: Game ID
  
- **GAME_STARTED**: Logged when both players have selected their decks and the game begins
  - Details: Game ID
  
- **GAME_COMPLETED**: Logged when a game is completed with a winner
  - Details: Game ID and winner
  
- **GAME_ABANDONED**: Logged when a game is ended prematurely without a winner
  - Details: Game ID

### Logs Service (`logs-service`)

## Security Benefits

### Monitoring Capabilities
1. **Failed Login Detection**: Track repeated failed login attempts to identify:
   - Brute force attacks
   - Account compromise attempts
   - Credential stuffing attacks

2. **Unauthorized Access Attempts**: Monitor attempts to access admin functions by non-admin users

3. **User Activity Patterns**: Track user registration, login frequency, and game participation

4. **Admin Activity Auditing**: Full audit trail of all administrative actions

### Key Security Events to Monitor

#### Critical Events (Require Immediate Attention)
- Multiple `LOGIN_FAILED` events from the same IP or for the same username
- `UNAUTHORIZED_ADMIN_ACCESS` attempts
- Unusual patterns in `PASSWORD_CHANGED` events

#### Important Events (Regular Monitoring)
- `REGISTRATION_FAILED` spikes (could indicate automated registration attempts)
- `GAME_ABANDONED` patterns (could indicate griefing behavior)
- Admin activity logs (`ADMIN_*` events)

## Log Structure

All logs are stored in the `logs` table with the following structure:
```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,        -- Action type (e.g., USER_LOGIN)
    username VARCHAR(255),               -- Username who performed the action
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT                         -- Additional context
);
```

## Accessing Logs

Logs can be accessed through the admin panel or via API endpoints:

### API Endpoints
- `GET /api/logs/list` - List all logs with pagination
- `GET /api/logs/search?query=<search_term>` - Search logs
- `POST /api/logs/create` - Create a log entry (for manual logging)

All log endpoints require admin privileges.

## Best Practices

1. **Regular Monitoring**: Review logs daily for suspicious patterns
2. **Failed Login Alerts**: Set up alerts for multiple failed login attempts
3. **Admin Action Review**: Regularly audit admin actions
4. **Retention Policy**: Implement log retention policies based on compliance requirements
5. **Performance**: Logs are indexed on timestamp, username, and action for fast queries

## Future Enhancements

Consider implementing:
1. Real-time alerting for critical security events
2. Automated threat detection based on log patterns
3. IP address logging for better tracking
4. Session tracking and correlation
5. Export functionality for compliance reporting
6. Log aggregation and visualization dashboards
