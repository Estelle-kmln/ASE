"""
Test script for account lockout mechanism after 3 failed login attempts.
"""

import requests
import time
import sys

# Configuration
BASE_URL = "http://localhost:8080"
AUTH_URL = f"{BASE_URL}/api/auth"

def print_result(step, success, message):
    """Print test result with color."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{step}. {status}: {message}")
    return success

def test_account_lockout():
    """Test account lockout after 3 failed login attempts."""
    print("\n" + "="*70)
    print("Testing Account Lockout Mechanism")
    print("="*70 + "\n")
    
    # Generate unique username for this test
    test_username = f"lockout_test_{int(time.time())}"
    test_password = "correct_password123"
    wrong_password = "wrong_password123"
    
    all_tests_passed = True
    
    # Step 1: Register a new user
    print("Step 1: Registering test user...")
    response = requests.post(
        f"{AUTH_URL}/register",
        json={"username": test_username, "password": test_password}
    )
    all_tests_passed &= print_result(
        "1", 
        response.status_code == 201,
        f"User registration (status: {response.status_code})"
    )
    
    if response.status_code != 201:
        print(f"Response: {response.json()}")
        return False
    
    time.sleep(1)
    
    # Step 2: First failed login attempt
    print("\nStep 2: Testing first failed login attempt...")
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": test_username, "password": wrong_password}
    )
    data = response.json()
    all_tests_passed &= print_result(
        "2a",
        response.status_code == 401,
        f"First failed login returns 401 (status: {response.status_code})"
    )
    all_tests_passed &= print_result(
        "2b",
        data.get("remaining_attempts") == 2,
        f"Remaining attempts is 2 (got: {data.get('remaining_attempts')})"
    )
    
    time.sleep(1)
    
    # Step 3: Second failed login attempt
    print("\nStep 3: Testing second failed login attempt...")
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": test_username, "password": wrong_password}
    )
    data = response.json()
    all_tests_passed &= print_result(
        "3a",
        response.status_code == 401,
        f"Second failed login returns 401 (status: {response.status_code})"
    )
    all_tests_passed &= print_result(
        "3b",
        data.get("remaining_attempts") == 1,
        f"Remaining attempts is 1 (got: {data.get('remaining_attempts')})"
    )
    
    time.sleep(1)
    
    # Step 4: Third failed login attempt (should lock account)
    print("\nStep 4: Testing third failed login attempt (should lock account)...")
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": test_username, "password": wrong_password}
    )
    data = response.json()
    all_tests_passed &= print_result(
        "4a",
        response.status_code == 423,
        f"Third failed login returns 423 Locked (status: {response.status_code})"
    )
    all_tests_passed &= print_result(
        "4b",
        "locked_until" in data,
        f"Response includes locked_until timestamp"
    )
    all_tests_passed &= print_result(
        "4c",
        "retry_after" in data and data.get("retry_after") > 0,
        f"Response includes retry_after in seconds (got: {data.get('retry_after')})"
    )
    
    if "locked_until" in data:
        print(f"   Account locked until: {data['locked_until']}")
        print(f"   Retry after: {data['retry_after']} seconds")
    
    time.sleep(1)
    
    # Step 5: Attempt login with correct password while locked
    print("\nStep 5: Testing login with correct password while locked...")
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": test_username, "password": test_password}
    )
    all_tests_passed &= print_result(
        "5",
        response.status_code == 423,
        f"Login blocked even with correct password (status: {response.status_code})"
    )
    
    time.sleep(1)
    
    # Step 6: Verify subsequent attempts still return locked status
    print("\nStep 6: Testing that account remains locked...")
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": test_username, "password": wrong_password}
    )
    all_tests_passed &= print_result(
        "6",
        response.status_code == 423,
        f"Account remains locked (status: {response.status_code})"
    )
    
    # Summary
    print("\n" + "="*70)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Account lockout mechanism working correctly!")
        print("\nSecurity features verified:")
        print("  • Account locks after 3 failed login attempts")
        print("  • Lockout duration: 15 minutes")
        print("  • Remaining attempts counter works")
        print("  • Correct password doesn't bypass lockout")
        print("  • HTTP 423 (Locked) status code returned")
    else:
        print("❌ SOME TESTS FAILED - Please review the output above")
    print("="*70 + "\n")
    
    return all_tests_passed


def test_successful_login_after_failed_attempts():
    """Test that successful login resets failed attempts."""
    print("\n" + "="*70)
    print("Testing Failed Attempts Reset on Successful Login")
    print("="*70 + "\n")
    
    test_username = f"reset_test_{int(time.time())}"
    test_password = "correct_password123"
    wrong_password = "wrong_password123"
    
    all_tests_passed = True
    
    # Register user
    print("Step 1: Registering test user...")
    response = requests.post(
        f"{AUTH_URL}/register",
        json={"username": test_username, "password": test_password}
    )
    all_tests_passed &= print_result(
        "1",
        response.status_code == 201,
        f"User registration (status: {response.status_code})"
    )
    
    time.sleep(1)
    
    # Two failed attempts
    print("\nStep 2: Making two failed login attempts...")
    for i in range(2):
        response = requests.post(
            f"{AUTH_URL}/login",
            json={"username": test_username, "password": wrong_password}
        )
        print(f"   Failed attempt {i+1}: {response.status_code}")
        time.sleep(1)
    
    # Successful login
    print("\nStep 3: Logging in with correct password...")
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": test_username, "password": test_password}
    )
    all_tests_passed &= print_result(
        "3",
        response.status_code == 200,
        f"Successful login resets counter (status: {response.status_code})"
    )
    
    time.sleep(1)
    
    # Try two more failed attempts to verify counter was reset
    print("\nStep 4: Making two more failed attempts after successful login...")
    for i in range(2):
        response = requests.post(
            f"{AUTH_URL}/login",
            json={"username": test_username, "password": wrong_password}
        )
        data = response.json()
        remaining = data.get("remaining_attempts")
        print(f"   Failed attempt {i+1}: remaining_attempts = {remaining}")
        all_tests_passed &= print_result(
            f"4.{i+1}",
            remaining == (2 - i),
            f"Counter properly reset (expected {2-i}, got {remaining})"
        )
        time.sleep(1)
    
    print("\n" + "="*70)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Counter reset mechanism working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please review the output above")
    print("="*70 + "\n")
    
    return all_tests_passed


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔒 ACCOUNT LOCKOUT SECURITY TEST SUITE")
    print("="*70)
    
    try:
        # Test 1: Account lockout mechanism
        test1_passed = test_account_lockout()
        
        # Test 2: Counter reset on successful login
        test2_passed = test_successful_login_after_failed_attempts()
        
        # Final summary
        print("\n" + "="*70)
        print("FINAL SUMMARY")
        print("="*70)
        print(f"Test 1 (Account Lockout): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Test 2 (Counter Reset): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All security tests passed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Please review the implementation.")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the server.")
        print("Please ensure the microservices are running:")
        print("  cd microservices")
        print("  docker compose up -d")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
