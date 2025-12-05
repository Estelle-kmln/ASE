"""
Test script for concurrent session detection and prevention (strict mode)
"""

import requests
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080/api/auth"
TEST_USERNAME = f"concurrent_test_{int(time.time())}"
TEST_PASSWORD = "TestPass123!"

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_step(number, text):
    """Print a formatted step."""
    print(f"{BOLD}{YELLOW}{number}️⃣  {text}{RESET}")


def print_success(text):
    """Print a success message."""
    print(f"   {GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print an error message."""
    print(f"   {RED}❌ {text}{RESET}")


def print_info(text):
    """Print an info message."""
    print(f"   {BLUE}ℹ️  {text}{RESET}")


def register_user(username, password, user_agent="Test Client 1"):
    """Register a new test user."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": user_agent
    }
    response = requests.post(
        f"{BASE_URL}/register",
        json={"username": username, "password": password},
        headers=headers
    )
    return response


def login_user(username, password, user_agent="Test Client 1"):
    """Login a user."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": user_agent
    }
    response = requests.post(
        f"{BASE_URL}/login",
        json={"username": username, "password": password},
        headers=headers
    )
    return response


def get_active_sessions(token):
    """Get active sessions for the user."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.get(
        f"{BASE_URL}/sessions",
        headers=headers
    )
    return response


def revoke_session(token, session_id):
    """Revoke a specific session."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.delete(
        f"{BASE_URL}/sessions/{session_id}",
        headers=headers
    )
    return response


def logout_user(token, refresh_token=None):
    """Logout a user."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {}
    if refresh_token:
        body["refresh_token"] = refresh_token
    
    response = requests.post(
        f"{BASE_URL}/logout",
        json=body,
        headers=headers
    )
    return response


def main():
    """Run concurrent session tests."""
    print_header("🧪 Testing Concurrent Session Detection (Strict Mode)")
    
    # Test 1: Register user
    print_step(1, "Registering test user...")
    response = register_user(TEST_USERNAME, TEST_PASSWORD, "Chrome on Windows")
    
    if response.status_code != 201:
        print_error(f"Registration failed: {response.json()}")
        return
    
    data = response.json()
    token1 = data["access_token"]
    refresh_token1 = data["refresh_token"]
    print_success("User registered successfully")
    print_info(f"Username: {TEST_USERNAME}")
    print_info(f"Device: Chrome on Windows")
    
    # Test 2: Check active sessions
    print_step(2, "Checking active sessions...")
    response = get_active_sessions(token1)
    
    if response.status_code != 200:
        print_error(f"Failed to get sessions: {response.json()}")
        return
    
    sessions_data = response.json()
    print_success(f"Active sessions: {sessions_data['total']}")
    
    if sessions_data['total'] > 0:
        session = sessions_data['sessions'][0]
        print_info(f"Session ID: {session['id']}")
        print_info(f"Device: {session['device']}")
        print_info(f"IP: {session['ip_address']}")
        print_info(f"Created: {session['created_at']}")
    
    # Test 3: Attempt concurrent login (should be rejected)
    print_step(3, "Attempting concurrent login from different device...")
    print_info("This should be REJECTED (strict mode)")
    
    response = login_user(TEST_USERNAME, TEST_PASSWORD, "Safari on Mac")
    
    if response.status_code == 409:
        print_success("Concurrent login correctly REJECTED ✓")
        error_data = response.json()
        print_info(f"Error: {error_data.get('error')}")
        
        if 'active_session' in error_data:
            active = error_data['active_session']
            print_info(f"Active session device: {active.get('device')}")
            print_info(f"Active session IP: {active.get('ip_address')}")
    else:
        print_error(f"Concurrent login was NOT rejected! Status: {response.status_code}")
        print_error("STRICT MODE FAILED!")
        return
    
    # Test 4: Logout from first device
    print_step(4, "Logging out from first device...")
    response = logout_user(token1, refresh_token1)
    
    if response.status_code != 200:
        print_error(f"Logout failed: {response.json()}")
        return
    
    print_success("Logged out successfully")
    
    # Test 5: Verify no active sessions
    print_step(5, "Verifying all sessions are closed...")
    # Note: Can't check with old token, so we'll just try to login again
    
    # Test 6: Login again (should succeed now)
    print_step(6, "Attempting login after logout...")
    print_info("This should SUCCEED")
    
    response = login_user(TEST_USERNAME, TEST_PASSWORD, "Safari on Mac")
    
    if response.status_code == 200:
        print_success("Login successful after logout ✓")
        data = response.json()
        token2 = data["access_token"]
        refresh_token2 = data["refresh_token"]
        print_info("New session created successfully")
    else:
        print_error(f"Login failed: {response.json()}")
        return
    
    # Test 7: Check active sessions again
    print_step(7, "Checking active sessions for new session...")
    response = get_active_sessions(token2)
    
    if response.status_code != 200:
        print_error(f"Failed to get sessions: {response.json()}")
        return
    
    sessions_data = response.json()
    print_success(f"Active sessions: {sessions_data['total']}")
    
    if sessions_data['total'] > 0:
        session = sessions_data['sessions'][0]
        print_info(f"Session ID: {session['id']}")
        print_info(f"Device: {session['device']}")
        session_id_to_revoke = session['id']
    
    # Test 8: Test session revocation by ID
    print_step(8, "Testing session revocation by ID...")
    response = revoke_session(token2, session_id_to_revoke)
    
    if response.status_code == 200:
        print_success("Session revoked successfully by ID ✓")
    else:
        print_error(f"Failed to revoke session: {response.json()}")
        return
    
    # Test 9: Verify session is revoked (should be able to login now)
    print_step(9, "Verifying session revocation...")
    response = login_user(TEST_USERNAME, TEST_PASSWORD, "Firefox on Linux")
    
    if response.status_code == 200:
        print_success("Login successful after session revocation ✓")
        data = response.json()
        token3 = data["access_token"]
        print_info("Session management working correctly")
    else:
        print_error(f"Login failed after revocation: {response.json()}")
        return
    
    # Cleanup: Logout
    print_step("🧹", "Cleaning up...")
    logout_user(token3)
    print_success("Test cleanup completed")
    
    # Final summary
    print_header("✅ All Concurrent Session Tests PASSED!")
    print(f"{GREEN}Strict mode is working correctly:{RESET}")
    print(f"  • Users can only have ONE active session")
    print(f"  • Concurrent login attempts are rejected")
    print(f"  • Session tracking captures device info")
    print(f"  • Manual session revocation works")
    print(f"  • Login succeeds after logout/revocation")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to the auth service.")
        print_info("Make sure the services are running: docker compose up")
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
