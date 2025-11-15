import os
import unittest
from database import (
    create_account,
    username_exists,
    verify_login,
    get_user_profile,
    update_user_password,
)
from database.db import get_connection


class TestProfileFunctions(unittest.TestCase):

    def setUp(self):
        """Set up test environment with database connection."""
        # Ensure DATABASE_URL is set to local Docker database
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "postgresql://gameuser:gamepassword@localhost:5432/battlecards"
        
        # Clean up any test users before each test
        self.test_username = "test_user_profile"
        self.test_password = "test_password_123"
        self._cleanup_test_user()

    def tearDown(self):
        """Clean up test data after each test."""
        self._cleanup_test_user()

    def _cleanup_test_user(self):
        """Remove test user from database if it exists."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = %s", (self.test_username,))
            conn.commit()
            conn.close()
        except Exception:
            pass  # Ignore errors during cleanup

    def test_create_profile(self):
        """Test creating a new user profile."""
        # User should not exist initially
        self.assertFalse(username_exists(self.test_username))
        
        # Create the account
        result = create_account(self.test_username, self.test_password)
        self.assertTrue(result, "Account creation should succeed")
        
        # User should now exist
        self.assertTrue(username_exists(self.test_username))

    def test_create_existing_profile(self):
        """Test that creating a profile with existing username fails."""
        # Create account first
        create_account(self.test_username, self.test_password)
        self.assertTrue(username_exists(self.test_username))
        
        # Try to create again with same username
        result = create_account(self.test_username, "different_password")
        self.assertFalse(result, "Creating duplicate username should fail")

    def test_get_profile(self):
        """Test retrieving a user profile."""
        # Create a user first
        create_account(self.test_username, self.test_password)
        
        # Get the profile
        profile = get_user_profile(self.test_username)
        self.assertIsNotNone(profile, "Profile should exist")
        self.assertEqual(profile["username"], self.test_username)
        
        # Test getting non-existent profile
        non_existent = get_user_profile("non_existent_user_12345")
        self.assertIsNone(non_existent, "Non-existent profile should return None")

    def test_update_profile(self):
        """Test updating user password."""
        # Create a user first
        create_account(self.test_username, self.test_password)
        
        # Verify login with original password
        self.assertTrue(verify_login(self.test_username, self.test_password))
        
        # Update password
        new_password = "new_password_456"
        result = update_user_password(self.test_username, new_password)
        self.assertTrue(result, "Password update should succeed")
        
        # Verify old password no longer works
        self.assertFalse(verify_login(self.test_username, self.test_password))
        
        # Verify new password works
        self.assertTrue(verify_login(self.test_username, new_password))
        
        # Test updating password for non-existent user
        result = update_user_password("non_existent_user_12345", "new_pass")
        self.assertFalse(result, "Updating password for non-existent user should fail")


if __name__ == "__main__":
    unittest.main()