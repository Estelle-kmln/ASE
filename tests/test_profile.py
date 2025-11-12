import unittest
import profile


class TestProfileFunctions(unittest.TestCase):

    def setUp(self):
        # Reset the db before each test
        profile.users.clear()
        profile.users["player1"] = {"username": "player1", "email": "player1@example.com"}
        profile.current_user = "player1"  # ✅ This now updates the real variable inside profile.py

    def test_get_profile(self):
        profile_data = profile.get_profile()
        self.assertEqual(profile_data["username"], "player1")
        self.assertEqual(profile_data["email"], "player1@example.com")

    def test_update_profile(self):
        new_data = {"username": "new_name", "email": "new_email@example.com"}
        updated = profile.update_profile(new_data)
        self.assertEqual(updated["username"], "new_name")
        self.assertEqual(updated["email"], "new_email@example.com")

    def test_create_profile(self):
        created = profile.create_profile("player2", "player2@example.com")
        self.assertIn("player2", profile.users)
        self.assertEqual(profile.users["player2"]["email"], "player2@example.com")
        self.assertIsNotNone(created)

    def test_create_existing_profile(self):
        created = profile.create_profile("player1", "duplicate@example.com")
        self.assertIsNone(created)


if __name__ == "__main__":
    unittest.main()