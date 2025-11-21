I've created comprehensive unit tests for the authentication service with **45 test cases** covering:

## Test Coverage:

**1. Registration Tests (9 tests)**
- Successful registration
- Missing username/password
- Username too short (<3 chars)
- Password too short (<4 chars)
- Duplicate username (409 conflict)
- Whitespace trimming

**2. Login Tests (8 tests)**
- Successful login
- Wrong password
- Non-existent user
- Missing credentials
- Case-sensitive username validation

**3. Profile Management Tests (11 tests)**
- Get profile with valid token
- Get profile without/invalid token
- Update password successfully
- Password too short validation
- No data provided error
- Verify old password stops working after update

**4. Token Validation Tests (4 tests)**
- Valid token validation
- Invalid token rejection
- Missing token handling
- Malformed authorization header

**5. Edge Cases (5 tests)**
- Special characters in username
- Multiple concurrent sessions
- Empty string password
- Very long username
- Unicode/encoding handling

You can run these tests with:

```bash
python tests\test_auth_service.py
```

Or with pytest:

```bash
pytest tests\test_auth_service.py -v
```

The tests use unique timestamps to avoid conflicts and validate all response codes, error messages, and data structures returned by each endpoint.

Made changes.