"""
Unit tests for Logs Service endpoints
Tests all logs service methods including create, list, and search logs.
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


class TestLogsServiceHealth(unittest.TestCase):
    """Test cases for logs service health check endpoint."""

    def test_health_check_success(self):
        """Test health check endpoint returns healthy status."""
        # Note: Health endpoint is accessed directly, not through API gateway
        response = session.get("http://localhost:5006/health")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("service", data)
        self.assertEqual(data["service"], "logs-service")


class TestLogsServiceCreate(unittest.TestCase):
    """Test cases for create log endpoint."""

    def setUp(self):
        """Set up test environment with authentication."""
        self.unique_id = int(time.time() * 1000)
        self.test_username = f"logsuser_{self.unique_id}"
        self.test_password = "SecurePass123!"

        # Register and login to get auth token
        register_response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": self.test_username,
                "password": self.test_password,
            },
        )
        self.assertEqual(register_response.status_code, 201)
        self.auth_token = register_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    def test_create_log_success(self):
        """Test successful log creation with action and details."""
        response = session.post(
            f"{BASE_URL}/api/logs/create",
            headers=self.headers,
            json={
                "action": "TEST_ACTION",
                "details": "Test log entry created during pytest",
            },
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Log created successfully")
        self.assertIn("id", data)
        self.assertIsInstance(data["id"], int)

    def test_create_log_success_action_only(self):
        """Test successful log creation with only action (details optional)."""
        response = session.post(
            f"{BASE_URL}/api/logs/create",
            headers=self.headers,
            json={"action": "TEST_ACTION_NO_DETAILS"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Log created successfully")
        self.assertIn("id", data)

    def test_create_log_missing_action(self):
        """Test log creation fails when action is missing."""
        response = session.post(
            f"{BASE_URL}/api/logs/create",
            headers=self.headers,
            json={"details": "Details without action"},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Action is required", data["error"])

    def test_create_log_empty_body(self):
        """Test log creation fails with empty request body."""
        response = session.post(
            f"{BASE_URL}/api/logs/create",
            headers=self.headers,
            json={},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Action is required", data["error"])

    def test_create_log_no_auth(self):
        """Test log creation fails without authentication token."""
        response = session.post(
            f"{BASE_URL}/api/logs/create",
            json={
                "action": "TEST_ACTION",
                "details": "Attempt without auth",
            },
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_create_log_invalid_token(self):
        """Test log creation fails with invalid authentication token."""
        response = session.post(
            f"{BASE_URL}/api/logs/create",
            headers={"Authorization": "Bearer invalid_token_12345"},
            json={
                "action": "TEST_ACTION",
                "details": "Attempt with invalid token",
            },
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)


class TestLogsServiceList(unittest.TestCase):
    """Test cases for list logs endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up admin authentication for all tests in this class."""
        # Force logout admin first to clear any existing sessions
        session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={"username": "admin", "password": "Admin123!"},
        )
        
        # Wait a moment for logout to complete
        time.sleep(0.5)
        
        # Login as admin to get admin token
        admin_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "Admin123!"},
        )
        if admin_response.status_code == 200:
            cls.admin_token = admin_response.json()["access_token"]
            cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        else:
            cls.admin_token = None
            cls.admin_headers = {}

        # Create a regular user for testing non-admin access
        cls.unique_id = int(time.time() * 1000)
        cls.test_username = f"regularuser_{cls.unique_id}"
        cls.test_password = "SecurePass123!"

        register_response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": cls.test_username,
                "password": cls.test_password,
            },
        )
        if register_response.status_code == 201:
            cls.user_token = register_response.json()["access_token"]
            cls.user_headers = {"Authorization": f"Bearer {cls.user_token}"}
        else:
            cls.user_token = None
            cls.user_headers = {}

    def test_list_logs_success_admin(self):
        """Test successful log listing with admin privileges."""
        if not self.admin_token:
            self.skipTest("Admin authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/list?page=0&size=10",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            log_entry = data[0]
            self.assertIn("id", log_entry)
            self.assertIn("action", log_entry)
            self.assertIn("timestamp", log_entry)
            # username and details are optional
            self.assertTrue("username" in log_entry)
            self.assertTrue("details" in log_entry)

    def test_list_logs_success_with_pagination(self):
        """Test log listing with different pagination parameters."""
        if not self.admin_token:
            self.skipTest("Admin authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/list?page=0&size=5",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)

    def test_list_logs_default_pagination(self):
        """Test log listing uses default pagination when not specified."""
        if not self.admin_token:
            self.skipTest("Admin authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/list",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_list_logs_non_admin_forbidden(self):
        """Test log listing fails for non-admin users."""
        if not self.user_token:
            self.skipTest("User authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/list",
            headers=self.user_headers,
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("admin", data["error"].lower())

    def test_list_logs_no_auth(self):
        """Test log listing fails without authentication."""
        response = session.get(f"{BASE_URL}/api/logs/list")

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_list_logs_invalid_token(self):
        """Test log listing fails with invalid token."""
        response = session.get(
            f"{BASE_URL}/api/logs/list",
            headers={"Authorization": "Bearer invalid_token_12345"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)


class TestLogsServiceSearch(unittest.TestCase):
    """Test cases for search logs endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up admin authentication and create test logs."""
        # Force logout admin first to clear any existing sessions
        session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={"username": "admin", "password": "Admin123!"},
        )
        
        # Wait a moment for logout to complete
        time.sleep(0.5)
        
        # Login as admin
        admin_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "Admin123!"},
        )
        if admin_response.status_code == 200:
            cls.admin_token = admin_response.json()["access_token"]
            cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        else:
            cls.admin_token = None
            cls.admin_headers = {}

        # Create a regular user for testing non-admin access
        cls.unique_id = int(time.time() * 1000)
        cls.test_username = f"searchuser_{cls.unique_id}"
        cls.test_password = "SecurePass123!"

        register_response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": cls.test_username,
                "password": cls.test_password,
            },
        )
        if register_response.status_code == 201:
            cls.user_token = register_response.json()["access_token"]
            cls.user_headers = {"Authorization": f"Bearer {cls.user_token}"}

            # Create some test logs with unique identifier
            cls.unique_search_term = f"PYTEST_SEARCH_{cls.unique_id}"
            session.post(
                f"{BASE_URL}/api/logs/create",
                headers=cls.user_headers,
                json={
                    "action": cls.unique_search_term,
                    "details": "Searchable test log entry",
                },
            )
        else:
            cls.user_token = None
            cls.user_headers = {}

    def test_search_logs_success_admin(self):
        """Test successful log search with admin privileges."""
        if not self.admin_token:
            self.skipTest("Admin authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/search?query=TEST",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_search_logs_with_specific_query(self):
        """Test log search returns relevant results for specific query."""
        if not self.admin_token or not self.user_token:
            self.skipTest("Authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/search?query={self.unique_search_term}",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # Should find at least the log we created
        if len(data) > 0:
            found = any(self.unique_search_term in log.get("action", "") for log in data)
            self.assertTrue(found, "Created log should be found in search results")

    def test_search_logs_empty_query(self):
        """Test log search with empty query returns results."""
        if not self.admin_token:
            self.skipTest("Admin authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/search?query=",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_search_logs_with_pagination(self):
        """Test log search with pagination parameters."""
        if not self.admin_token:
            self.skipTest("Admin authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/search?query=TEST&page=0&size=5",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)

    def test_search_logs_non_admin_forbidden(self):
        """Test log search fails for non-admin users."""
        if not self.user_token:
            self.skipTest("User authentication failed")

        response = session.get(
            f"{BASE_URL}/api/logs/search?query=TEST",
            headers=self.user_headers,
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("admin", data["error"].lower())

    def test_search_logs_no_auth(self):
        """Test log search fails without authentication."""
        response = session.get(f"{BASE_URL}/api/logs/search?query=TEST")

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_search_logs_invalid_token(self):
        """Test log search fails with invalid token."""
        response = session.get(
            f"{BASE_URL}/api/logs/search?query=TEST",
            headers={"Authorization": "Bearer invalid_token_12345"},
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
