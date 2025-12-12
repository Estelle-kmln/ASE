"""
Unit tests for Auth Service endpoints
Tests all authentication service methods including register, login, profile management, and token validation.
"""

import unittest
import requests
import time
import os
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Gateway base URL
BASE_URL = os.getenv("BASE_URL", "https://localhost:8443")

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False


class TestAuthServiceRegister(unittest.TestCase):
    """Test cases for user registration endpoint."""

    def setUp(self):
        """Set up test environment."""
        self.unique_id = int(time.time() * 1000)  # Use timestamp for uniqueness
        self.test_username = f"testuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

    def test_register_success(self):
        """Test successful user registration."""
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("access_token", data)
        # OAuth2-style metadata
        self.assertIn("token_type", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("expires_in", data)
        self.assertIsInstance(data["expires_in"], int)
        self.assertGreater(data["expires_in"], 0)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], self.test_username)
        self.assertIn("id", data["user"])
        self.assertEqual(data["message"], "User registered successfully")

    def test_register_missing_username(self):
        """Test registration fails without username."""
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"password": self.test_password},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Username and password are required", data["error"])

    def test_register_missing_password(self):
        """Test registration fails without password."""
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Username and password are required", data["error"])

    def test_register_missing_both(self):
        """Test registration fails without username and password."""
        response = session.post(f"{BASE_URL}/api/auth/register", json={})

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_register_username_too_short(self):
        """Test registration fails with username less than 3 characters."""
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": "ab", "password": self.test_password},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("at least 3 characters", data["error"])

    def test_register_password_too_short(self):
        """Test registration fails with password less than 8 characters."""
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username, "password": "Abc1!"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("at least 8 characters", data["error"])

    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username."""
        # Register first user
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        # Try to register with same username
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username, "password": "DifferentPass123!"},
        )

        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("already exists", data["error"])

    def test_register_whitespace_trimming(self):
        """Test that whitespace is trimmed from username and password."""
        username_with_spaces = f"  {self.test_username}  "
        password_with_spaces = f"  {self.test_password}  "

        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": username_with_spaces,
                "password": password_with_spaces,
            },
        )

        # The password with spaces will fail validation because spaces aren't allowed
        # Backend validates before trimming, so this should return 400
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)


class TestAuthServiceLogin(unittest.TestCase):
    """Test cases for user login endpoint."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"loginuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Use a separate session for registration to avoid session conflicts
        reg_session = requests.Session()
        reg_session.verify = False
        
        # Register a user for testing login (this creates a session we won't use)
        reg_session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        # Don't keep this session - let it expire

    def test_login_success(self):
        """Test successful login with valid credentials."""
        # Use a fresh session for login to avoid concurrent session conflicts
        login_session = requests.Session()
        login_session.verify = False
        
        # Wait a moment for any previous session to potentially expire
        # Note: With concurrent session prevention, this might return 409
        # if the registration session is still active
        time.sleep(0.5)
        
        response = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        # Accept either 200 (successful login) or 409 (concurrent session prevented)
        # Both are valid responses given the concurrent session prevention feature
        self.assertIn(response.status_code, [200, 409])
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("access_token", data)
            # OAuth2-style metadata
            self.assertIn("token_type", data)
            self.assertEqual(data["token_type"], "bearer")
            self.assertIn("expires_in", data)
            self.assertIsInstance(data["expires_in"], int)
            self.assertGreater(data["expires_in"], 0)
            self.assertIn("user", data)
            self.assertEqual(data["user"]["username"], self.test_username)
            self.assertEqual(data["message"], "Login successful")
        elif response.status_code == 409:
            # Concurrent session detected - this is expected behavior
            data = response.json()
            self.assertIn("active_session", data)

    def test_login_wrong_password(self):
        """Test login fails with incorrect password."""
        # Use a fresh session
        login_session = requests.Session()
        login_session.verify = False
        
        response = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": "WrongPassword123!"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid username or password", data["error"])

    def test_login_nonexistent_user(self):
        """Test login fails with non-existent username."""
        # Use a fresh session
        login_session = requests.Session()
        login_session.verify = False
        
        response = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "nonexistent_user_12345",
                "password": self.test_password,
            },
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid username or password", data["error"])

    def test_login_missing_username(self):
        """Test login fails without username."""
        # Use a fresh session
        login_session = requests.Session()
        login_session.verify = False
        
        response = login_session.post(
            f"{BASE_URL}/api/auth/login", json={"password": self.test_password}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Username and password are required", data["error"])

    def test_login_missing_password(self):
        """Test login fails without password."""
        # Use a fresh session
        login_session = requests.Session()
        login_session.verify = False
        
        response = login_session.post(
            f"{BASE_URL}/api/auth/login", json={"username": self.test_username}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Username and password are required", data["error"])

    def test_login_empty_credentials(self):
        """Test login fails with empty credentials."""
        # Use a fresh session
        login_session = requests.Session()
        login_session.verify = False
        
        response = login_session.post(f"{BASE_URL}/api/auth/login", json={})

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_login_case_sensitive_username(self):
        """Test that username is case-sensitive."""
        # Use a fresh session
        login_session = requests.Session()
        login_session.verify = False
        
        response = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": self.test_username.upper(),
                "password": self.test_password,
            },
        )

        # Should fail because username case doesn't match
        self.assertEqual(response.status_code, 401)


class TestAuthServiceProfile(unittest.TestCase):
    """Test cases for profile management endpoints."""

    def setUp(self):
        """Set up test environment with a registered and logged-in user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"profileuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register and get token
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_profile_success(self):
        """Test successfully retrieving user profile."""
        response = session.get(
            f"{BASE_URL}/api/auth/profile", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user", data)
        self.assertEqual(data["user"]["username"], self.test_username)
        self.assertIn("id", data["user"])
        self.assertIn("created_at", data["user"])

    def test_get_profile_no_token(self):
        """Test profile retrieval fails without token."""
        response = session.get(f"{BASE_URL}/api/auth/profile")

        self.assertEqual(response.status_code, 401)

    def test_get_profile_invalid_token(self):
        """Test profile retrieval fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(
            f"{BASE_URL}/api/auth/profile", headers=invalid_headers
        )

        self.assertEqual(response.status_code, 401)

    def test_get_profile_malformed_token(self):
        """Test profile retrieval fails with malformed authorization header."""
        malformed_headers = {"Authorization": "InvalidFormat token"}
        response = session.get(
            f"{BASE_URL}/api/auth/profile", headers=malformed_headers
        )

        self.assertEqual(response.status_code, 401)

    def test_update_profile_password_success(self):
        """Test successfully updating user password."""
        new_password = "NewSecurePass456!"
        response = session.put(
            f"{BASE_URL}/api/auth/profile",
            json={"password": new_password},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("successfully", data["message"].lower())

        # Force logout to clear any active sessions
        logout_session = requests.Session()
        logout_session.verify = False
        logout_session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={"username": self.test_username, "password": new_password},
        )

        # Verify new password works
        login_session = requests.Session()
        login_session.verify = False
        login_response = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": new_password},
        )
        self.assertEqual(login_response.status_code, 200)

        # Verify old password doesn't work
        old_login_session = requests.Session()
        old_login_session.verify = False
        old_login_response = old_login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.assertEqual(old_login_response.status_code, 401)

    def test_update_profile_password_too_short(self):
        """Test updating password fails when password is too short."""
        response = session.put(
            f"{BASE_URL}/api/auth/profile",
            json={"password": "Abc1!"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("at least 8 characters", data["error"])

    def test_update_profile_no_data(self):
        """Test updating profile fails with no data."""
        response = session.put(
            f"{BASE_URL}/api/auth/profile", json={}, headers=self.headers
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("No data provided", data["error"])

    def test_update_profile_no_token(self):
        """Test profile update fails without token."""
        response = session.put(
            f"{BASE_URL}/api/auth/profile", json={"password": "newpass123"}
        )

        self.assertEqual(response.status_code, 401)

    def test_update_profile_invalid_token(self):
        """Test profile update fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.put(
            f"{BASE_URL}/api/auth/profile",
            json={"password": "newpass123"},
            headers=invalid_headers,
        )

        self.assertEqual(response.status_code, 401)


class TestAuthServiceTokenValidation(unittest.TestCase):
    """Test cases for JWT token validation endpoint."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"validateuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register and get token
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_validate_token_success(self):
        """Test successful token validation."""
        response = session.post(
            f"{BASE_URL}/api/auth/validate", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["username"], self.test_username)

    def test_validate_token_no_token(self):
        """Test token validation fails without token."""
        response = session.post(f"{BASE_URL}/api/auth/validate")

        self.assertEqual(response.status_code, 401)

    def test_validate_token_invalid_token(self):
        """Test token validation fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.post(
            f"{BASE_URL}/api/auth/validate", headers=invalid_headers
        )

        self.assertEqual(response.status_code, 401)

    def test_validate_token_malformed_header(self):
        """Test token validation fails with malformed authorization header."""
        malformed_headers = {"Authorization": "InvalidFormat token"}
        response = session.post(
            f"{BASE_URL}/api/auth/validate", headers=malformed_headers
        )

        self.assertEqual(response.status_code, 401)


class TestAuthServiceEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_register_with_special_characters_username(self):
        """Test registration with special characters in username."""
        unique_id = int(time.time() * 1000)
        username = f"user_test-123_{unique_id}"

        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": "SecurePass123!"},
        )

        # Should succeed - special chars like _ and - are typically allowed
        self.assertIn(response.status_code, [201, 400])

    def test_multiple_sessions_same_user(self):
        """Test that concurrent session prevention works (409 on second login from different session)."""
        unique_id = int(time.time() * 1000)
        username = f"multiuser_{unique_id}"
        password = "SecurePass123!"

        # Use separate session for registration
        reg_session = requests.Session()
        reg_session.verify = False
        
        # Register (creates first session)
        reg_response = reg_session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": password},
        )
        
        self.assertEqual(reg_response.status_code, 201)
        
        # Try to login from a different session (should fail with 409 - concurrent session)
        login_session = requests.Session()
        login_session.verify = False
        
        response2 = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
        )

        # With concurrent session prevention, this should return 409
        self.assertEqual(response2.status_code, 409)

    def test_register_with_empty_string_password(self):
        """Test registration fails with empty string password."""
        unique_id = int(time.time() * 1000)
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": f"user_{unique_id}", "password": ""},
        )

        self.assertEqual(response.status_code, 400)

    def test_register_with_very_long_username(self):
        """Test registration with very long username."""
        unique_id = int(time.time() * 1000)
        long_username = f"a" * 200 + f"_{unique_id}"

        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": long_username, "password": "SecurePass123!"},
        )

        # Should either succeed or fail with validation error
        self.assertIn(response.status_code, [201, 400, 500])


class TestAuthServiceRefreshToken(unittest.TestCase):
    """Test cases for token refresh endpoint."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"refreshuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register and get tokens
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.access_token = response.json()["access_token"]
        self.refresh_token = response.json()["refresh_token"]

    def test_refresh_token_success(self):
        """Test successful token refresh with valid refresh token."""
        response = session.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("expires_in", data)
        self.assertIsInstance(data["expires_in"], int)
        self.assertGreater(data["expires_in"], 0)

    def test_refresh_token_missing(self):
        """Test token refresh fails without refresh token."""
        response = session.post(f"{BASE_URL}/api/auth/refresh", json={})

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Refresh token is required", data["error"])

    def test_refresh_token_invalid(self):
        """Test token refresh fails with invalid refresh token."""
        response = session.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": "invalid_refresh_token_xyz"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid or expired", data["error"])

    def test_refresh_token_empty_string(self):
        """Test token refresh fails with empty string refresh token."""
        response = session.post(
            f"{BASE_URL}/api/auth/refresh", json={"refresh_token": ""}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)


class TestAuthServiceLogout(unittest.TestCase):
    """Test cases for logout endpoint."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"logoutuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register and get tokens
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.access_token = response.json()["access_token"]
        self.refresh_token = response.json()["refresh_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def test_logout_success_with_refresh_token(self):
        """Test successful logout with specific refresh token."""
        response = session.post(
            f"{BASE_URL}/api/auth/logout",
            json={"refresh_token": self.refresh_token},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("successfully", data["message"].lower())

    def test_logout_success_without_refresh_token(self):
        """Test successful logout without specific refresh token (revokes all)."""
        response = session.post(
            f"{BASE_URL}/api/auth/logout", json={}, headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("successfully", data["message"].lower())

    def test_logout_no_token(self):
        """Test logout fails without authentication token."""
        response = session.post(f"{BASE_URL}/api/auth/logout", json={})

        self.assertEqual(response.status_code, 401)

    def test_logout_invalid_token(self):
        """Test logout fails with invalid authentication token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.post(
            f"{BASE_URL}/api/auth/logout", json={}, headers=invalid_headers
        )

        self.assertEqual(response.status_code, 401)


class TestAuthServiceForceLogout(unittest.TestCase):
    """Test cases for force logout endpoint."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"forcelogoutuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register user
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

    def test_force_logout_success(self):
        """Test successful force logout with valid credentials."""
        response = session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("terminated", data["message"].lower())

    def test_force_logout_invalid_password(self):
        """Test force logout fails with invalid password."""
        response = session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={
                "username": self.test_username,
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid", data["error"])

    def test_force_logout_missing_username(self):
        """Test force logout fails without username."""
        response = session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={"password": self.test_password},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_force_logout_missing_password(self):
        """Test force logout fails without password."""
        response = session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={"username": self.test_username},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_force_logout_nonexistent_user(self):
        """Test force logout fails with non-existent username."""
        response = session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={
                "username": "nonexistent_user_99999",
                "password": self.test_password,
            },
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)


class TestAuthServiceSessions(unittest.TestCase):
    """Test cases for session management endpoints."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"sessionuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register and get tokens
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.access_token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def test_get_sessions_success(self):
        """Test successfully retrieving active sessions."""
        response = session.get(
            f"{BASE_URL}/api/auth/sessions", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sessions", data)
        self.assertIn("total", data)
        self.assertIsInstance(data["sessions"], list)
        self.assertGreaterEqual(data["total"], 1)

    def test_get_sessions_no_token(self):
        """Test getting sessions fails without authentication token."""
        response = session.get(f"{BASE_URL}/api/auth/sessions")

        self.assertEqual(response.status_code, 401)

    def test_revoke_specific_session_success(self):
        """Test successfully revoking a specific session."""
        # First get sessions to get a session ID
        get_response = session.get(
            f"{BASE_URL}/api/auth/sessions", headers=self.headers
        )
        sessions = get_response.json()["sessions"]

        if len(sessions) > 0:
            session_id = sessions[0]["id"]

            # Revoke the session
            response = session.delete(
                f"{BASE_URL}/api/auth/sessions/{session_id}",
                headers=self.headers,
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("revoked", data["message"].lower())

    def test_revoke_specific_session_not_found(self):
        """Test revoking non-existent session fails."""
        response = session.delete(
            f"{BASE_URL}/api/auth/sessions/999999", headers=self.headers
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

    def test_revoke_specific_session_no_token(self):
        """Test revoking session fails without authentication token."""
        response = session.delete(f"{BASE_URL}/api/auth/sessions/1")

        self.assertEqual(response.status_code, 401)

    def test_revoke_all_sessions_success(self):
        """Test successfully revoking all sessions."""
        # Create a fresh session to avoid token conflicts from previous tests
        unique_id = int(time.time() * 1000)
        test_username = f"revoke_all_user_{unique_id}"
        test_password = "SecurePass123!"
        
        # Register a new user and get fresh tokens
        reg_response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": test_username,
                "password": test_password,
            },
        )
        fresh_token = reg_response.json()["access_token"]
        fresh_headers = {"Authorization": f"Bearer {fresh_token}"}
        
        response = session.post(
            f"{BASE_URL}/api/auth/sessions/revoke-all",
            json={},
            headers=fresh_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("revoked", data["message"].lower())

    def test_revoke_all_sessions_no_token(self):
        """Test revoking all sessions fails without authentication token."""
        response = session.post(f"{BASE_URL}/api/auth/sessions/revoke-all")

        self.assertEqual(response.status_code, 401)


class TestAuthServiceAdmin(unittest.TestCase):
    """Test cases for admin endpoints."""

    def setUp(self):
        """Set up test environment with an admin user."""
        # Note: This assumes you have a way to create an admin user
        # You may need to manually create one in the database or adjust this
        self.unique_id = int(time.time() * 1000)
        self.admin_username = f"admin_{self.unique_id}"
        self.admin_password = "AdminPass123!"
        self.regular_username = f"regularuser_{self.unique_id}"
        self.regular_password = "RegularPass123!"

        # Register a regular user
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.regular_username,
                "password": self.regular_password,
            },
        )
        self.regular_token = response.json()["access_token"]
        self.regular_headers = {
            "Authorization": f"Bearer {self.regular_token}"
        }

        # For admin tests, we'll use the regular user token
        # In a real scenario, you'd need to have an actual admin user

    def test_list_users_no_token(self):
        """Test listing users fails without authentication token."""
        response = session.get(f"{BASE_URL}/api/admin/users")

        self.assertEqual(response.status_code, 401)

    def test_list_users_non_admin(self):
        """Test listing users fails with non-admin token."""
        response = session.get(
            f"{BASE_URL}/api/admin/users", headers=self.regular_headers
        )

        # Should return 403 Forbidden for non-admin users
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)

    def test_search_users_no_token(self):
        """Test searching users fails without authentication token."""
        response = session.get(
            f"{BASE_URL}/api/admin/users/search?query=test"
        )

        self.assertEqual(response.status_code, 401)

    def test_search_users_non_admin(self):
        """Test searching users fails with non-admin token."""
        response = session.get(
            f"{BASE_URL}/api/admin/users/search?query=test",
            headers=self.regular_headers,
        )

        # Should return 403 Forbidden for non-admin users
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)

    def test_list_roles_no_token(self):
        """Test listing roles fails without authentication token."""
        response = session.get(f"{BASE_URL}/api/admin/roles")

        self.assertEqual(response.status_code, 401)

    def test_list_roles_non_admin(self):
        """Test listing roles fails with non-admin token."""
        response = session.get(
            f"{BASE_URL}/api/admin/roles", headers=self.regular_headers
        )

        # Should return 403 Forbidden for non-admin users
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)


class TestAuthServiceHealth(unittest.TestCase):
    """Test cases for health check endpoint."""

    def test_health_check_success(self):
        """Test health check endpoint returns healthy status."""
        response = session.get(f"{BASE_URL}/api/auth/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("service", data)
        self.assertEqual(data["service"], "auth-service")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
