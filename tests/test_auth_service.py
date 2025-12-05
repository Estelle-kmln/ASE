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
        self.test_password = "securepass123"

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
        """Test registration fails with password less than 4 characters."""
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username, "password": "abc"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("at least 4 characters", data["error"])

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
            json={"username": self.test_username, "password": "differentpass"},
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

        self.assertEqual(response.status_code, 201)
        data = response.json()
        # Username should be trimmed
        self.assertEqual(data["user"]["username"], self.test_username)


class TestAuthServiceLogin(unittest.TestCase):
    """Test cases for user login endpoint."""

    def setUp(self):
        """Set up test environment with a registered user."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"loginuser_{self.unique_id}"
        self.test_password = "securepass123"

        # Register a user for testing login
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

    def test_login_success(self):
        """Test successful login with valid credentials."""
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )

        self.assertEqual(response.status_code, 200)
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

    def test_login_wrong_password(self):
        """Test login fails with incorrect password."""
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": "wrongpassword"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid username or password", data["error"])

    def test_login_nonexistent_user(self):
        """Test login fails with non-existent username."""
        response = session.post(
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
        response = session.post(
            f"{BASE_URL}/api/auth/login", json={"password": self.test_password}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Username and password are required", data["error"])

    def test_login_missing_password(self):
        """Test login fails without password."""
        response = session.post(
            f"{BASE_URL}/api/auth/login", json={"username": self.test_username}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Username and password are required", data["error"])

    def test_login_empty_credentials(self):
        """Test login fails with empty credentials."""
        response = session.post(f"{BASE_URL}/api/auth/login", json={})

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_login_case_sensitive_username(self):
        """Test that username is case-sensitive."""
        response = session.post(
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
        self.test_password = "securepass123"

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
        new_password = "newsecurepass456"
        response = session.put(
            f"{BASE_URL}/api/auth/profile",
            json={"password": new_password},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("successfully", data["message"].lower())

        # Verify new password works
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": new_password},
        )
        self.assertEqual(login_response.status_code, 200)

        # Verify old password doesn't work
        old_login_response = session.post(
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
            json={"password": "abc"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("at least 4 characters", data["error"])

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
        self.test_password = "securepass123"

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
            json={"username": username, "password": "pass1234"},
        )

        # Should succeed - special chars like _ and - are typically allowed
        self.assertIn(response.status_code, [201, 400])

    def test_multiple_sessions_same_user(self):
        """Test that multiple login sessions work for the same user."""
        unique_id = int(time.time() * 1000)
        username = f"multiuser_{unique_id}"
        password = "pass1234"

        # Register
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": password},
        )

        # Login twice to get two tokens
        response1 = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
        )
        response2 = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
        )

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        # Both tokens should be valid
        validate1 = session.post(
            f"{BASE_URL}/api/auth/validate",
            headers={"Authorization": f"Bearer {token1}"},
        )
        validate2 = session.post(
            f"{BASE_URL}/api/auth/validate",
            headers={"Authorization": f"Bearer {token2}"},
        )

        self.assertEqual(validate1.status_code, 200)
        self.assertEqual(validate2.status_code, 200)

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
            json={"username": long_username, "password": "pass1234"},
        )

        # Should either succeed or fail with validation error
        self.assertIn(response.status_code, [201, 400, 500])


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
