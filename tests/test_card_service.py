"""
Unit tests for Card Service endpoints
Tests all card service methods with valid and invalid inputs.
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


class TestCardServiceSetup(unittest.TestCase):
    """Setup class to get authentication token for tests."""

    @classmethod
    def setUpClass(cls):
        """Set up authentication token for all card service tests."""
        cls.unique_id = int(time.time() * 1000)
        cls.test_username = f"carduser_{cls.unique_id}"
        cls.test_password = "CardPass123!"

        # Register and get token
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": cls.test_username, "password": cls.test_password},
        )
        cls.token = response.json().get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}


class TestCardServiceGetAllCards(TestCardServiceSetup):
    """Test cases for GET /api/cards endpoint."""

    def test_get_all_cards_success(self):
        """Test successfully retrieving all cards with valid token."""
        response = session.get(f"{BASE_URL}/api/cards", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("cards", data)
        self.assertIsInstance(data["cards"], list)

        # Verify card structure if cards exist
        if len(data["cards"]) > 0:
            card = data["cards"][0]
            self.assertIn("id", card)
            self.assertIn("type", card)
            self.assertIn("power", card)

    def test_get_all_cards_no_token(self):
        """Test getting all cards fails without authentication token."""
        response = session.get(f"{BASE_URL}/api/cards")

        self.assertEqual(response.status_code, 401)

    def test_get_all_cards_invalid_token(self):
        """Test getting all cards fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(f"{BASE_URL}/api/cards", headers=invalid_headers)

        self.assertEqual(response.status_code, 401)


class TestCardServiceGetCardsByType(TestCardServiceSetup):
    """Test cases for GET /api/cards/by-type/<type> endpoint."""

    def test_get_cards_by_type_rock_success(self):
        """Test successfully retrieving cards by type 'rock'."""
        response = session.get(
            f"{BASE_URL}/api/cards/by-type/rock", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("cards", data)
        self.assertIn("type", data)
        self.assertEqual(data["type"].lower(), "rock")

        # Verify all returned cards are of correct type
        for card in data["cards"]:
            self.assertEqual(card["type"].lower(), "rock")

    def test_get_cards_by_type_paper_success(self):
        """Test successfully retrieving cards by type 'paper'."""
        response = session.get(
            f"{BASE_URL}/api/cards/by-type/paper", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type"].lower(), "paper")

    def test_get_cards_by_type_scissors_success(self):
        """Test successfully retrieving cards by type 'scissors'."""
        response = session.get(
            f"{BASE_URL}/api/cards/by-type/scissors", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type"].lower(), "scissors")

    def test_get_cards_by_type_invalid_type(self):
        """Test getting cards by invalid type fails."""
        response = session.get(
            f"{BASE_URL}/api/cards/by-type/invalid_type", headers=self.headers
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid card type", data["error"])

    def test_get_cards_by_type_no_token(self):
        """Test getting cards by type fails without token."""
        response = session.get(f"{BASE_URL}/api/cards/by-type/rock")

        self.assertEqual(response.status_code, 401)

    def test_get_cards_by_type_case_insensitive(self):
        """Test card type lookup is case insensitive."""
        response = session.get(
            f"{BASE_URL}/api/cards/by-type/ROCK", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type"].lower(), "rock")


class TestCardServiceGetCardById(TestCardServiceSetup):
    """Test cases for GET /api/cards/<id> endpoint."""

    def test_get_card_by_id_success(self):
        """Test successfully retrieving a card by valid ID."""
        # First get all cards to find a valid ID
        response = session.get(f"{BASE_URL}/api/cards", headers=self.headers)
        cards = response.json()["cards"]

        if len(cards) > 0:
            card_id = cards[0]["id"]

            response = session.get(
                f"{BASE_URL}/api/cards/{card_id}", headers=self.headers
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("card", data)
            self.assertEqual(data["card"]["id"], card_id)

    def test_get_card_by_id_not_found(self):
        """Test getting card by non-existent ID returns 404."""
        response = session.get(
            f"{BASE_URL}/api/cards/999999", headers=self.headers
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Card not found", data["error"])

    def test_get_card_by_id_no_token(self):
        """Test getting card by ID fails without token."""
        response = session.get(f"{BASE_URL}/api/cards/1")

        self.assertEqual(response.status_code, 401)

    def test_get_card_by_id_invalid_id_format(self):
        """Test getting card with invalid ID format."""
        response = session.get(
            f"{BASE_URL}/api/cards/invalid_id", headers=self.headers
        )

        # Should return 404 or 400 depending on routing
        self.assertIn(response.status_code, [400, 404])


class TestCardServiceRandomDeck(TestCardServiceSetup):
    """Test cases for POST /api/cards/random-deck endpoint."""

    def test_create_random_deck_default_size(self):
        """Test creating random deck with default size (22)."""
        response = session.post(
            f"{BASE_URL}/api/cards/random-deck", headers=self.headers, json={}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("deck", data)
        self.assertIn("size", data)
        self.assertEqual(data["size"], 22)
        self.assertEqual(len(data["deck"]), 22)

        # Verify deck structure
        for card in data["deck"]:
            self.assertIn("id", card)
            self.assertIn("type", card)
            self.assertIn("power", card)

    def test_create_random_deck_custom_size(self):
        """Test creating random deck with custom size."""
        custom_size = 10
        response = session.post(
            f"{BASE_URL}/api/cards/random-deck",
            headers=self.headers,
            json={"size": custom_size},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["size"], custom_size)
        self.assertEqual(len(data["deck"]), custom_size)

    def test_create_random_deck_size_too_small(self):
        """Test creating deck with size less than 1 fails."""
        response = session.post(
            f"{BASE_URL}/api/cards/random-deck",
            headers=self.headers,
            json={"size": 0},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("between 1 and 50", data["error"])

    def test_create_random_deck_size_too_large(self):
        """Test creating deck with size greater than 50 fails."""
        response = session.post(
            f"{BASE_URL}/api/cards/random-deck",
            headers=self.headers,
            json={"size": 51},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("between 1 and 50", data["error"])

    def test_create_random_deck_negative_size(self):
        """Test creating deck with negative size fails."""
        response = session.post(
            f"{BASE_URL}/api/cards/random-deck",
            headers=self.headers,
            json={"size": -5},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_create_random_deck_no_token(self):
        """Test creating random deck fails without token."""
        response = session.post(
            f"{BASE_URL}/api/cards/random-deck", json={"size": 10}
        )

        self.assertEqual(response.status_code, 401)

    def test_create_random_deck_randomness(self):
        """Test that multiple deck generations produce different results."""
        response1 = session.post(
            f"{BASE_URL}/api/cards/random-deck",
            headers=self.headers,
            json={"size": 10},
        )
        response2 = session.post(
            f"{BASE_URL}/api/cards/random-deck",
            headers=self.headers,
            json={"size": 10},
        )

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        deck1 = response1.json()["deck"]
        deck2 = response2.json()["deck"]

        # Convert to comparable format
        deck1_ids = [card["id"] for card in deck1]
        deck2_ids = [card["id"] for card in deck2]

        # At least some cards should be different (randomness check)
        # Note: There's a small chance they could be identical, but highly unlikely
        self.assertNotEqual(deck1_ids, deck2_ids)


class TestCardServiceStatistics(TestCardServiceSetup):
    """Test cases for GET /api/cards/statistics endpoint."""

    def test_get_statistics_success(self):
        """Test successfully retrieving card statistics."""
        response = session.get(
            f"{BASE_URL}/api/cards/statistics", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_cards", data)
        self.assertIn("type_distribution", data)
        self.assertIn("power_distribution", data)
        self.assertIn("available_types", data)
        self.assertIn("power_range", data)

        # Verify structure
        self.assertIn("counts", data["type_distribution"])
        self.assertIn("percentages", data["type_distribution"])
        self.assertIn("min", data["power_range"])
        self.assertIn("max", data["power_range"])

    def test_get_statistics_no_token(self):
        """Test getting statistics fails without token."""
        response = session.get(f"{BASE_URL}/api/cards/statistics")

        self.assertEqual(response.status_code, 401)

    def test_get_statistics_percentages_sum(self):
        """Test that type percentages roughly sum to 100."""
        response = session.get(
            f"{BASE_URL}/api/cards/statistics", headers=self.headers
        )

        if response.status_code == 200:
            data = response.json()
            percentages = data["type_distribution"]["percentages"]
            total_percentage = sum(percentages.values())

            # Should be close to 100 (allowing for rounding errors)
            self.assertAlmostEqual(total_percentage, 100.0, delta=1.0)


class TestCardServiceTypes(TestCardServiceSetup):
    """Test cases for GET /api/cards/types endpoint."""

    def test_get_card_types_success(self):
        """Test successfully retrieving available card types."""
        response = session.get(
            f"{BASE_URL}/api/cards/types", headers=self.headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("types", data)
        self.assertIn("powers", data)
        self.assertIsInstance(data["types"], list)
        self.assertIsInstance(data["powers"], list)

    def test_get_card_types_no_token(self):
        """Test getting card types fails without token."""
        response = session.get(f"{BASE_URL}/api/cards/types")

        self.assertEqual(response.status_code, 401)

    def test_get_card_types_contains_valid_types(self):
        """Test that returned types include expected game types."""
        response = session.get(
            f"{BASE_URL}/api/cards/types", headers=self.headers
        )

        if response.status_code == 200:
            data = response.json()
            types_lower = [t.lower() for t in data["types"]]

            # Check for rock, paper, scissors
            expected_types = ["rock", "paper", "scissors"]
            for expected in expected_types:
                self.assertIn(expected, types_lower)


if __name__ == "__main__":
    unittest.main(verbosity=2)
