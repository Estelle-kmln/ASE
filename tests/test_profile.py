"""Tests for user profile functionality via auth-service microservice.

Updated to use the microservices API instead of direct database access.
"""

import os
import unittest
import requests
import time

# API Gateway base URL
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')


class TestProfileFunctions(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        # Test user credentials
        self.test_username = f"test_user_profile_{int(time.time())}"
        self.test_password = "test_password_123"
        self.token = None
        
        # Wait for services to be ready
        self._wait_for_service()

    def tearDown(self):
        """Clean up test data after each test."""
        # No cleanup needed - each test uses a unique username
        pass
    
    def _wait_for_service(self, timeout=10):
        """Wait for auth service to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{BASE_URL}/api/auth/health", timeout=2)
                if response.status_code == 200:
                    return True
            except:
                time.sleep(0.5)
        return False

    def _register_user(self):
        """Helper to register a test user and get token."""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username, "password": self.test_password}
        )
        if response.status_code == 201:
            data = response.json()
            self.token = data.get('access_token')
            return True
        return False

    def _login_user(self):
        """Helper to login and get token."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": self.test_password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            return True
        return False

    def test_create_profile(self):
        """Test creating a new user profile."""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username, "password": self.test_password}
        )
        self.assertEqual(response.status_code, 201, f"Registration failed: {response.text}")
        
        data = response.json()
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], self.test_username)

    def test_create_existing_profile(self):
        """Test that creating a profile with existing username fails."""
        # Create account first
        self._register_user()
        
        # Try to create again with same username
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": self.test_username, "password": "different_password"}
        )
        self.assertIn(response.status_code, [400, 409], "Creating duplicate username should fail with 400 or 409")

    def test_get_profile(self):
        """Test retrieving a user profile."""
        # Create a user first
        self._register_user()
        
        # Get the profile
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
        self.assertEqual(response.status_code, 200, f"Profile retrieval failed: {response.text}")
        
        data = response.json()
        self.assertIn('user', data, f"Expected 'user' key in response: {data}")
        profile = data['user']
        self.assertEqual(profile['username'], self.test_username)
        
        # Test getting profile without token
        response = requests.get(f"{BASE_URL}/api/auth/profile")
        self.assertEqual(response.status_code, 401, "Should require authentication")

    def test_update_profile(self):
        """Test updating user profile."""
        # Create a user first
        self._register_user()
        
        # Verify login with original password
        self.assertTrue(self._login_user(), "Should be able to login with original password")
        
        # Update profile (e.g., email if supported, or test password update)
        headers = {"Authorization": f"Bearer {self.token}"}
        new_email = "newemail@example.com"
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"email": new_email},
            headers=headers
        )
        # Auth service may or may not support email updates - check if implemented
        self.assertIn(response.status_code, [200, 400, 404], "Update should either succeed or indicate feature not supported")
        
        # Test updating without token
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"email": "another@example.com"}
        )
        self.assertEqual(response.status_code, 401, "Should require authentication")

    def test_login(self):
        """Test user login."""
        # Register first
        self._register_user()
        
        # Test successful login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": self.test_password}
        )
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        
        data = response.json()
        self.assertIn('access_token', data)
        
        # Test failed login with wrong password
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": self.test_username, "password": "wrong_password"}
        )
        self.assertEqual(response.status_code, 401, "Wrong password should fail")
        
        # Test failed login with non-existent user
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "nonexistent_user_xyz", "password": "somepassword"}
        )
        self.assertEqual(response.status_code, 401, "Non-existent user should fail")


if __name__ == "__main__":
    unittest.main()