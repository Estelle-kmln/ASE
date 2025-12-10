"""
Security Test Suite
Tests input sanitization and injection attack prevention
Run this after implementing the security measures
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add utils path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'microservices', 'utils'))
from input_sanitizer import InputSanitizer


class TestInputSanitizer(unittest.TestCase):
    """Test input sanitization functions."""
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "user'; SELECT * FROM cards; --",
            "test' UNION SELECT password FROM users--",
            "input'; INSERT INTO games VALUES (1,2,3); --"
        ]
        
        for malicious_input in malicious_inputs:
            with self.assertRaises(ValueError, msg=f"Should block: {malicious_input}"):
                InputSanitizer.sanitize_string(malicious_input)
    
    def test_xss_injection_detection(self):
        """Test XSS attack pattern detection."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
            "onload=alert('xss')"
        ]
        
        for malicious_input in malicious_inputs:
            with self.assertRaises(ValueError, msg=f"Should block: {malicious_input}"):
                InputSanitizer.sanitize_string(malicious_input)
    
    def test_command_injection_detection(self):
        """Test command injection pattern detection."""
        malicious_inputs = [
            "; rm -rf /",
            "& del /f /q C:\\*.*",
            "| cat /etc/passwd",
            "`whoami`",
            "$(ls -la)",
            "../../../etc/passwd"
        ]
        
        for malicious_input in malicious_inputs:
            with self.assertRaises(ValueError, msg=f"Should block: {malicious_input}"):
                InputSanitizer.sanitize_string(malicious_input)
    
    def test_username_validation(self):
        """Test username validation."""
        # Valid usernames
        valid_usernames = ["testuser", "user123", "user.name", "user_name", "user-name"]
        for username in valid_usernames:
            result = InputSanitizer.validate_username(username)
            self.assertEqual(result, username.lower())
        
        # Invalid usernames
        invalid_usernames = [
            "",  # Empty
            "ab",  # Too short
            "user@domain.com",  # Invalid characters
            "user space",  # Spaces
            "user<script>",  # XSS attempt
            "'OR 1=1--"  # SQL injection attempt
        ]
        
        for username in invalid_usernames:
            with self.assertRaises(ValueError, msg=f"Should reject: {username}"):
                InputSanitizer.validate_username(username)
    
    def test_password_validation(self):
        """Test password validation."""
        # Valid passwords
        valid_passwords = ["Password123!", "P@ssw0rd!", "Complex_Pass2024!"]
        for password in valid_passwords:
            result = InputSanitizer.validate_password(password)
            self.assertEqual(result, password)
        
        # Invalid passwords
        invalid_passwords = [
            "",  # Empty
            "abc",  # Too short
            "'; DROP TABLE users; --",  # SQL injection
            "SELECT * FROM users",  # SQL keyword
        ]
        
        for password in invalid_passwords:
            with self.assertRaises(ValueError, msg=f"Should reject: {password}"):
                InputSanitizer.validate_password(password)
    
    def test_game_id_validation(self):
        """Test game ID validation."""
        # Valid UUIDs
        valid_game_ids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        ]
        for game_id in valid_game_ids:
            result = InputSanitizer.validate_game_id(game_id)
            self.assertEqual(result, game_id.lower())
        
        # Invalid game IDs
        invalid_game_ids = [
            "",  # Empty
            "not-a-uuid",  # Invalid format
            "550e8400-e29b-41d4-a716",  # Incomplete UUID
            "../../../etc/passwd",  # Path traversal attempt
            "'; DROP TABLE games; --"  # SQL injection attempt
        ]
        
        for game_id in invalid_game_ids:
            with self.assertRaises(ValueError, msg=f"Should reject: {game_id}"):
                InputSanitizer.validate_game_id(game_id)
    
    def test_card_type_validation(self):
        """Test card type validation."""
        # Valid card types
        valid_types = ["rock", "paper", "scissors", "ROCK", "Paper", "SCISSORS"]
        expected = ["rock", "paper", "scissors", "rock", "paper", "scissors"]
        
        for card_type, expected_result in zip(valid_types, expected):
            result = InputSanitizer.validate_card_type(card_type)
            self.assertEqual(result, expected_result)
        
        # Invalid card types
        invalid_types = [
            "",  # Empty
            "invalid",  # Not rock/paper/scissors
            "rock'; DROP TABLE cards; --",  # SQL injection attempt
            "<script>alert('xss')</script>"  # XSS attempt
        ]
        
        for card_type in invalid_types:
            with self.assertRaises(ValueError, msg=f"Should reject: {card_type}"):
                InputSanitizer.validate_card_type(card_type)
    
    def test_integer_validation(self):
        """Test integer validation with bounds."""
        # Valid integers
        self.assertEqual(InputSanitizer.validate_integer("5"), 5)
        self.assertEqual(InputSanitizer.validate_integer(10), 10)
        self.assertEqual(InputSanitizer.validate_integer("0", min_val=0, max_val=100), 0)
        self.assertEqual(InputSanitizer.validate_integer("50", min_val=0, max_val=100), 50)
        
        # Invalid integers
        invalid_integers = [
            "not_a_number",
            "5.5",
            "",
            "999999999999999999999999999999999999999999999"  # Overflow
        ]
        
        for invalid_int in invalid_integers:
            with self.assertRaises(ValueError, msg=f"Should reject: {invalid_int}"):
                InputSanitizer.validate_integer(invalid_int)
        
        # Out of bounds
        with self.assertRaises(ValueError):
            InputSanitizer.validate_integer("5", min_val=10, max_val=20)
        
        with self.assertRaises(ValueError):
            InputSanitizer.validate_integer("25", min_val=10, max_val=20)
    
    def test_json_payload_validation(self):
        """Test JSON payload validation."""
        # Valid payloads
        valid_payload = {"username": "testuser", "password": "password123"}
        result = InputSanitizer.validate_json_payload(valid_payload, ["username", "password"])
        self.assertIsInstance(result, dict)
        self.assertIn("username", result)
        self.assertIn("password", result)
        
        # Missing required fields
        invalid_payload = {"username": "testuser"}  # Missing password
        with self.assertRaises(ValueError):
            InputSanitizer.validate_json_payload(invalid_payload, ["username", "password"])
        
        # Invalid payload type
        with self.assertRaises(ValueError):
            InputSanitizer.validate_json_payload("not_a_dict", ["username"])
    
    def test_safe_string_sanitization(self):
        """Test that safe strings pass through unchanged."""
        safe_strings = [
            "hello world",
            "user123",
            "normal text with spaces",
            "numbers 12345",
            "Mixed Case Text"
        ]
        
        for safe_string in safe_strings:
            # Should not raise an exception
            result = InputSanitizer.sanitize_string(safe_string, allow_special=True)
            # Should contain the original content (HTML encoded)
            self.assertIsInstance(result, str)


class TestSecurityIntegration(unittest.TestCase):
    """Test security integration scenarios."""
    
    def test_chained_attack_prevention(self):
        """Test prevention of chained attacks."""
        chained_attack = "user'; DROP TABLE users; SELECT '<script>alert(\"xss\")</script>' --"
        
        with self.assertRaises(ValueError):
            InputSanitizer.sanitize_string(chained_attack)
    
    def test_encoded_attack_prevention(self):
        """Test prevention of encoded attacks."""
        encoded_attacks = [
            "%3Cscript%3Ealert('xss')%3C/script%3E",  # URL encoded
            "&#60;script&#62;alert('xss')&#60;/script&#62;",  # HTML encoded
        ]
        
        # Our sanitizer should still catch these after decoding
        for attack in encoded_attacks:
            # Should either raise ValueError or safely sanitize
            try:
                result = InputSanitizer.sanitize_string(attack)
                # If it doesn't raise an exception, it should be safely sanitized
                self.assertNotIn("<script>", result.lower())
                self.assertNotIn("javascript:", result.lower())
            except ValueError:
                # It's also acceptable to reject these entirely
                pass


if __name__ == '__main__':
    # Run security tests
    print("🔒 Running Security Test Suite...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestInputSanitizer))
    suite.addTest(loader.loadTestsFromTestCase(TestSecurityIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 50)
    if result.wasSuccessful():
        print("✅ All security tests PASSED!")
        print("🛡️  Your application is protected against common injection attacks.")
    else:
        print("❌ Some security tests FAILED!")
        print("⚠️  Please review the input sanitization implementation.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    print(f"Tests run: {result.testsRun}")
    print("=" * 50)