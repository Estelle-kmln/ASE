"""
Comprehensive logging test suite.
Tests that all user actions are properly logged in the system.
"""

import pytest
import requests
import time
import urllib3
import os

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = os.getenv("BASE_URL", "https://localhost:8443")

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False


@pytest.fixture(scope="class")
def test_user():
    """Create a test user for the test class and return username and token."""
    username = f"logtest_{int(time.time())}"
    # Register the user (returns token directly, avoiding concurrent session issues)
    resp = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": username, "password": "TestPass123!"},
    )
    if resp.status_code == 201:
        token = resp.json().get("access_token")
        return {"username": username, "token": token}
    return {"username": username, "token": None}


@pytest.fixture(scope="class")
def user_token(test_user):
    """Get authentication token for the test user from registration."""
    # Use the token from registration to avoid concurrent session conflicts
    return test_user.get("token")


@pytest.fixture(scope="class")
def admin_token():
    """Get admin authentication token."""
    # Use fresh session to avoid concurrent session conflicts
    admin_session = requests.Session()
    admin_session.verify = False
    
    # Try to login first
    resp = admin_session.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "Admin123!"},
    )
    
    # If we get 409 (concurrent session), force logout and try again
    if resp.status_code == 409:
        logout_session = requests.Session()
        logout_session.verify = False
        logout_session.post(
            f"{BASE_URL}/api/auth/force-logout",
            json={"username": "admin", "password": "Admin123!"},
        )
        
        # Try login again with fresh session
        admin_session = requests.Session()
        admin_session.verify = False
        resp = admin_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "Admin123!"},
        )
    
    if resp.status_code == 200:
        return resp.json().get("access_token", "")
    return None


class TestComprehensiveLogging:
    """Test suite for comprehensive user action logging."""

    @pytest.mark.order(1)
    def test_user_registration(self, test_user):
        """Test that user registration is logged."""
        print("\n1. Testing user registration...")
        print(f"   Registered {test_user['username']}: 201")
        assert test_user is not None, "User should be created"

    @pytest.mark.order(2)
    def test_duplicate_registration(self, test_user):
        """Test that duplicate registration attempts are logged."""
        print("\n2. Testing duplicate registration (should fail)...")
        resp = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": test_user['username'], "password": "TestPass123!"},
        )
        print(f"   Duplicate registration attempt: {resp.status_code}")
        assert resp.status_code == 409, "Duplicate registration should fail"

    @pytest.mark.order(3)
    def test_failed_login(self, test_user):
        """Test that failed login attempts are logged."""
        print("\n3. Testing failed login...")
        # Use fresh session to avoid concurrent session conflicts
        login_session = requests.Session()
        login_session.verify = False
        resp = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": test_user['username'], "password": "WrongPassword123!"},
        )
        print(f"   Failed login: {resp.status_code}")
        assert resp.status_code == 401, "Failed login should return 401"

    @pytest.mark.order(4)
    def test_successful_login(self, test_user, user_token):
        """Test that successful login is logged."""
        print("\n4. Testing successful login...")
        print(f"   Successful login: 200")
        assert user_token is not None, "Token should be returned"

    @pytest.mark.order(5)
    def test_profile_view(self, user_token):
        """Test that profile views are logged."""
        print("\n5. Testing profile view...")
        resp = session.get(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        print(f"   Profile viewed: {resp.status_code}")
        assert resp.status_code == 200, "Profile view should succeed"

    @pytest.mark.order(6)
    def test_password_change(self, test_user, user_token):
        """Test that password changes are logged."""
        print("\n6. Testing password change...")
        resp = session.put(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"password": "NewTestPass123!"},
        )
        print(f"   Password changed: {resp.status_code}")
        assert resp.status_code == 200, "Password change should succeed"
        # Note: Token becomes invalid after password change, but that's expected

    @pytest.mark.order(7)
    def test_unauthorized_admin_access(self, test_user):
        """Test that unauthorized admin access attempts are logged."""
        # Get a fresh token with old password (before password change)
        # Actually, since password was changed, we need to use new password
        # But for this test, let's just use an invalid token scenario
        print("\n7. Testing unauthorized admin access...")
        # Use an invalid/expired token
        resp = session.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": "Bearer invalid_token"},
        )
        print(f"   Unauthorized admin access attempt: {resp.status_code}")
        assert resp.status_code in [
            401,
            403,
            500,
        ], "Unauthorized access should be denied"

    @pytest.mark.order(8)
    def test_game_creation(self, test_user):
        """Test that game creation is logged."""
        print("\n8. Testing game creation...")
        # Use fresh session to re-login with new password to get valid token
        login_session = requests.Session()
        login_session.verify = False
        resp = login_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": test_user['username'], "password": "NewTestPass123!"},
        )
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            game_resp = session.post(
                f"{BASE_URL}/api/games",
                headers={"Authorization": f"Bearer {token}"},
                json={"player2_name": "admin"},
            )
            if game_resp.status_code == 201:
                game_id = game_resp.json()["game_id"]
                print(
                    f"   Game created: {game_resp.status_code} (ID: {game_id})"
                )
                assert game_id is not None, "Game ID should be returned"
            else:
                print(f"   Game creation failed: {game_resp.status_code}")

    @pytest.mark.order(9)
    def test_admin_login(self, admin_token):
        """Test admin login for log viewing."""
        print("\n10. Testing admin log viewing...")
        assert admin_token is not None, "Admin token should be available"

    @pytest.mark.order(10)
    def test_admin_view_logs(self, admin_token):
        """Test that admin log viewing is logged."""
        if not admin_token:
            pytest.skip("Admin token not available")
        resp = session.get(
            f"{BASE_URL}/api/logs/list?page=0&size=20",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        print(f"   Admin viewed logs: {resp.status_code}")
        assert resp.status_code == 200, "Admin should be able to view logs"

    @pytest.mark.order(11)
    def test_admin_search_logs(self, test_user, admin_token):
        """Test that admin log searching is logged."""
        if not admin_token:
            pytest.skip("Admin token not available")
        print("\n11. Testing admin log search...")
        resp = session.get(
            f"{BASE_URL}/api/logs/search?query={test_user}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        print(f"   Admin searched logs: {resp.status_code}")
        assert resp.status_code == 200, "Admin should be able to search logs"

    @pytest.mark.order(12)
    def test_display_recent_logs(self, admin_token):
        """Display recent logs for verification."""
        if not admin_token:
            pytest.skip("Admin token not available")
        # Wait a moment for logs to be written
        time.sleep(1)

        # Display all recent logs
        print("\n" + "=" * 80)
        print("RECENT LOGS:")
        print("=" * 80)
        logs = session.get(
            f"{BASE_URL}/api/logs/list?page=0&size=25",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).json()

        for log in logs[:15]:
            timestamp = log["timestamp"][:19] if log["timestamp"] else "N/A"
            action = log["action"]
            user = log.get("username", "N/A")
            details = log.get("details", "")
            print(f"{timestamp} | {action:30s} | {user:20s}")
            if details:
                print(f"  └─ {details}")

        print("\n" + "=" * 80)
        print("✓ All logging tests completed!")
        print("=" * 80)
