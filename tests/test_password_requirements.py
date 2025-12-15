"""
Test Password Requirements Enhancement
Tests that password validation enforces:
- Minimum 8 characters
- At least one number
- At least one special character
"""

import sys
import os

# Add the auth-service directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'microservices', 'auth-service'))

from input_sanitizer import InputSanitizer


def test_password_minimum_length():
    """Test that passwords must be at least 8 characters"""
    # Too short passwords
    try:
        InputSanitizer.validate_password("Pass1!")
        assert False, "Should have rejected password shorter than 8 characters"
    except ValueError as e:
        assert "at least 8 characters" in str(e)
    
    # Exactly 8 characters with all requirements
    try:
        result = InputSanitizer.validate_password("Pass123!")
        assert result == "Pass123!"
        print("✓ 8-character password with requirements accepted")
    except ValueError as e:
        assert False, f"Should have accepted valid 8-character password: {e}"


def test_password_requires_number():
    """Test that passwords must contain at least one number"""
    # No number
    try:
        InputSanitizer.validate_password("Password!")
        assert False, "Should have rejected password without a number"
    except ValueError as e:
        assert "at least one number" in str(e)
        print("✓ Password without number rejected")
    
    # With number
    try:
        result = InputSanitizer.validate_password("Password1!")
        assert result == "Password1!"
        print("✓ Password with number accepted")
    except ValueError as e:
        assert False, f"Should have accepted password with number: {e}"


def test_password_requires_special_character():
    """Test that passwords must contain at least one special character"""
    # No special character
    try:
        InputSanitizer.validate_password("Password123")
        assert False, "Should have rejected password without special character"
    except ValueError as e:
        assert "special character" in str(e)
        print("✓ Password without special character rejected")
    
    # With special character - only test allowed characters
    special_chars = "!@$%^&*()_+={}[]:;,.?/<>-"
    for char in special_chars[:5]:  # Test a few different special characters
        try:
            test_pwd = f"Pass123{char}"
            result = InputSanitizer.validate_password(test_pwd)
            assert result == test_pwd
        except ValueError as e:
            assert False, f"Should have accepted password with special character '{char}': {e}"
    
    print(f"✓ Passwords with various special characters accepted")


def test_password_all_requirements_combined():
    """Test various valid passwords that meet all requirements"""
    valid_passwords = [
        "MyP@ssw0rd",
        "Secure123!",
        "Test1234$",
        "C0mpl3x!Pass",
        "Valid_Pass123",
        "Str0ng+Password"
    ]
    
    for pwd in valid_passwords:
        try:
            result = InputSanitizer.validate_password(pwd)
            assert result == pwd
        except ValueError as e:
            assert False, f"Should have accepted valid password '{pwd}': {e}"
    
    print(f"✓ All {len(valid_passwords)} valid passwords accepted")


def test_password_edge_cases():
    """Test edge cases and boundary conditions"""
    # Empty password
    try:
        InputSanitizer.validate_password("")
        assert False, "Should have rejected empty password"
    except ValueError as e:
        assert "cannot be empty" in str(e)
        print("✓ Empty password rejected")
    
    # Password too long (>128 characters)
    try:
        long_password = "A1!" + "x" * 130
        InputSanitizer.validate_password(long_password)
        assert False, "Should have rejected password over 128 characters"
    except ValueError as e:
        assert "too long" in str(e)
        print("✓ Overly long password rejected")
    
    # Exactly at maximum length (128 chars) with requirements
    try:
        max_password = "A1!" + "x" * 125
        result = InputSanitizer.validate_password(max_password)
        assert result == max_password
        print("✓ Maximum length password (128 chars) accepted")
    except ValueError as e:
        assert False, f"Should have accepted 128-character password: {e}"


def test_password_invalid_patterns():
    """Test that SQL injection patterns are still rejected"""
    # These should still be rejected due to SQL injection patterns
    dangerous_passwords = [
        "Pass123!SELECT",
        "Test123!DROP",
    ]
    
    for pwd in dangerous_passwords:
        try:
            InputSanitizer.validate_password(pwd)
            assert False, f"Should have rejected password with dangerous pattern: '{pwd}'"
        except ValueError as e:
            assert "invalid patterns" in str(e)
    
    print("✓ Passwords with SQL injection patterns rejected")


def test_password_invalid_characters():
    """Test that passwords with disallowed characters are rejected"""
    # These should be rejected due to invalid characters (not in allowed list)
    invalid_passwords = [
        "Pass123#word",  # # not allowed
        "Test123|word",  # | not allowed
        "Valid1'word",   # ' not allowed
        "Good2\"word",   # " not allowed
        "Best3`word",    # ` not allowed
        "Nice4~word",    # ~ not allowed
    ]
    
    for pwd in invalid_passwords:
        try:
            InputSanitizer.validate_password(pwd)
            assert False, f"Should have rejected password with invalid character: '{pwd}'"
        except ValueError as e:
            error_msg = str(e).lower()
            assert ("invalid characters" in error_msg or "special character" in error_msg)
    
    print("✓ Passwords with invalid characters rejected")


def run_all_tests():
    """Run all password requirement tests"""
    print("\n" + "="*60)
    print("Testing Enhanced Password Requirements")
    print("="*60 + "\n")
    
    try:
        test_password_minimum_length()
        print()
        test_password_requires_number()
        print()
        test_password_requires_special_character()
        print()
        test_password_all_requirements_combined()
        print()
        test_password_edge_cases()
        print()
        test_password_invalid_patterns()
        print()
        test_password_invalid_characters()
        
        print("\n" + "="*60)
        print("✅ All password requirement tests passed!")
        print("="*60 + "\n")
        
        print("Password Requirements Summary:")
        print("  ✓ Minimum 8 characters")
        print("  ✓ At least one number")
        print("  ✓ At least one special character")
        print("  ✓ Maximum 128 characters")
        print("  ✓ No SQL injection patterns")
        print()
        
        return True
        
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ Test failed: {e}")
        print("="*60 + "\n")
        return False
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Unexpected error: {e}")
        print("="*60 + "\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
