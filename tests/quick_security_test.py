#!/usr/bin/env python3
"""
Quick Security Test
Verify input sanitization is working correctly
"""

import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'microservices', 'utils'))

from input_sanitizer import InputSanitizer

def test_security():
    """Run basic security tests."""
    print("🔒 Testing Input Sanitization...")
    print("=" * 40)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Safe username
    try:
        result = InputSanitizer.validate_username('testuser123')
        print(f"✅ Safe username validation: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error with safe username: {str(e)}")
        tests_failed += 1
    
    # Test 2: SQL injection attempt
    try:
        InputSanitizer.validate_username("admin'; DROP TABLE users; --")
        print("❌ FAILED to block SQL injection!")
        tests_failed += 1
    except ValueError as e:
        print(f"✅ Blocked SQL injection: {str(e)[:50]}...")
        tests_passed += 1
    
    # Test 3: XSS attempt
    try:
        InputSanitizer.sanitize_string('<script>alert("xss")</script>')
        print("❌ FAILED to block XSS!")
        tests_failed += 1
    except ValueError as e:
        print(f"✅ Blocked XSS attempt: {str(e)[:50]}...")
        tests_passed += 1
    
    # Test 4: Command injection
    try:
        InputSanitizer.sanitize_string('; rm -rf /')
        print("❌ FAILED to block command injection!")
        tests_failed += 1
    except ValueError as e:
        print(f"✅ Blocked command injection: {str(e)[:50]}...")
        tests_passed += 1
    
    # Test 5: Game ID validation
    try:
        result = InputSanitizer.validate_game_id('550e8400-e29b-41d4-a716-446655440000')
        print(f"✅ Valid game ID accepted: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Error with valid game ID: {str(e)}")
        tests_failed += 1
    
    # Test 7: Invalid game ID
    try:
        InputSanitizer.validate_game_id('../../etc/passwd')
        print("❌ FAILED to block path traversal!")
        tests_failed += 1
    except ValueError as e:
        print(f"✅ Blocked path traversal: {str(e)[:50]}...")
        tests_passed += 1
    
    print("=" * 40)
    print(f"🛡️  Security tests completed!")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("🎉 All security tests PASSED! Your application is protected.")
        return 0
    else:
        print("⚠️  Some security tests FAILED! Please review the implementation.")
        return 1

if __name__ == '__main__':
    exit_code = test_security()
    sys.exit(exit_code)