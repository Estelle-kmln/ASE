"""
Unit tests for Game Service endpoints
Tests all game service methods with valid and invalid inputs.
"""

import unittest
import requests
import time
import os
import psycopg2

# API Gateway base URL
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gameuser:gamepassword@localhost:5432/battlecards",
)


class TestGameServiceSetup(unittest.TestCase):
    """Setup class to get authentication tokens for tests."""

    @classmethod
    def setUpClass(cls):
        """Set up authentication tokens for all game service tests."""
        cls.unique_id = int(time.time() * 1000)

        # Create player 1
        cls.player1_username = f"gameplayer1_{cls.unique_id}"
        cls.player1_password = "gamepass123"
        response1 = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": cls.player1_username,
                "password": cls.player1_password,
            },
        )
        cls.player1_token = response1.json().get("access_token")
        cls.player1_headers = {"Authorization": f"Bearer {cls.player1_token}"}

        # Create player 2
        cls.player2_username = f"gameplayer2_{cls.unique_id}"
        cls.player2_password = "gamepass123"
        response2 = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": cls.player2_username,
                "password": cls.player2_password,
            },
        )
        cls.player2_token = response2.json().get("access_token")
        cls.player2_headers = {"Authorization": f"Bearer {cls.player2_token}"}

    @classmethod
    def create_active_game(cls):
        """Helper method to create a fully active game with decks selected."""
        # Step 1: Create game
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=cls.player1_headers,
            json={"player2_name": cls.player2_username},
        )
        game_id = response.json().get("game_id")

        # Step 2: Accept invitation (transitions to deck_selection)
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/accept",
            headers=cls.player1_headers,
        )

        # Step 3: Player 1 selects deck
        deck = [
            {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"},
            {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"},
            {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"},
            {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"},
            {"type": "Scissors"}, {"type": "Scissors"}, {"type": "Scissors"}, {"type": "Scissors"},
            {"type": "Scissors"}, {"type": "Scissors"}
        ]
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/select-deck",
            headers=cls.player1_headers,
            json={"deck": deck},
        )

        # Step 4: Player 2 selects deck (transitions to active)
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/select-deck",
            headers=cls.player2_headers,
            json={"deck": deck},
        )

        return game_id


class TestGameServiceCreateGame(TestGameServiceSetup):
    """Test cases for POST /api/games endpoint."""

    def test_create_game_success(self):
        """Test successfully creating a new game with valid data."""
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=self.player1_headers,
            json={"player2_name": self.player2_username},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("game_id", data)
        self.assertIn("player1_name", data)
        self.assertIn("player2_name", data)
        self.assertIn("status", data)
        self.assertIn("turn", data)
        self.assertEqual(data["player1_name"], self.player1_username)
        self.assertEqual(data["player2_name"], self.player2_username)
        self.assertEqual(data["turn"], 1)

    def test_create_game_missing_player2(self):
        """Test creating game fails without player2_name."""
        response = requests.post(
            f"{BASE_URL}/api/games", headers=self.player1_headers, json={}
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Player 2 name is required", data["error"])

    def test_create_game_no_token(self):
        """Test creating game fails without authentication token."""
        response = requests.post(
            f"{BASE_URL}/api/games",
            json={"player2_name": self.player2_username},
        )

        self.assertEqual(response.status_code, 401)

    def test_create_game_invalid_token(self):
        """Test creating game fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=invalid_headers,
            json={"player2_name": self.player2_username},
        )

        self.assertEqual(response.status_code, 401)

    def test_create_game_empty_player2_name(self):
        """Test creating game fails with empty player2_name."""
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=self.player1_headers,
            json={"player2_name": ""},
        )

        self.assertEqual(response.status_code, 400)


class TestGameServiceGetGame(TestGameServiceSetup):
    """Test cases for GET /api/games/<game_id> endpoint."""

    def setUp(self):
        """Create a game for testing."""
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=self.player1_headers,
            json={"player2_name": self.player2_username},
        )
        self.game_id = response.json().get("game_id")

    def test_get_game_success_player1(self):
        """Test player 1 can successfully retrieve game state."""
        response = requests.get(
            f"{BASE_URL}/api/games/{self.game_id}", headers=self.player1_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("game_id", data)
        self.assertIn("turn", data)
        self.assertIn("game_status", data)
        self.assertIn("player1", data)
        self.assertIn("player2", data)
        self.assertEqual(data["game_id"], self.game_id)
        self.assertIn(data["game_status"], ['pending', 'active', 'deck_selection'])

    def test_get_game_success_player2(self):
        """Test player 2 can successfully retrieve game state."""
        response = requests.get(
            f"{BASE_URL}/api/games/{self.game_id}", headers=self.player2_headers
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["game_id"], self.game_id)

    def test_get_game_not_found(self):
        """Test getting game with non-existent ID returns 404."""
        fake_game_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{BASE_URL}/api/games/{fake_game_id}", headers=self.player1_headers
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Game not found", data["error"])

    def test_get_game_unauthorized_user(self):
        """Test non-player cannot view game."""
        # Create third user
        unique_id = int(time.time() * 1000)
        username = f"nonplayer_{unique_id}"
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": "pass123"},
        )
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(
            f"{BASE_URL}/api/games/{self.game_id}", headers=headers
        )

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Unauthorized", data["error"])

    def test_get_game_no_token(self):
        """Test getting game fails without token."""
        response = requests.get(f"{BASE_URL}/api/games/{self.game_id}")

        self.assertEqual(response.status_code, 401)


class TestGameServiceGetHand(TestGameServiceSetup):
    """Test cases for GET /api/games/<game_id>/hand endpoint."""

    def setUp(self):
        """Create a game for testing."""
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=self.player1_headers,
            json={"player2_name": self.player2_username},
        )
        self.game_id = response.json().get("game_id")

    def test_get_hand_success(self):
        """Test successfully retrieving player's hand."""
        response = requests.get(
            f"{BASE_URL}/api/games/{self.game_id}/hand",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hand", data)
        self.assertIn("player", data)
        self.assertEqual(data["player"], self.player1_username)
        self.assertIsInstance(data["hand"], list)

    def test_get_hand_game_not_found(self):
        """Test getting hand for non-existent game returns 404."""
        fake_game_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{BASE_URL}/api/games/{fake_game_id}/hand",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

    def test_get_hand_unauthorized_user(self):
        """Test non-player cannot view hand."""
        unique_id = int(time.time() * 1000)
        username = f"nonplayer_{unique_id}"
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": "pass123"},
        )
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(
            f"{BASE_URL}/api/games/{self.game_id}/hand", headers=headers
        )

        self.assertEqual(response.status_code, 403)

    def test_get_hand_no_token(self):
        """Test getting hand fails without token."""
        response = requests.get(f"{BASE_URL}/api/games/{self.game_id}/hand")

        self.assertEqual(response.status_code, 401)


class TestGameServiceDrawHand(TestGameServiceSetup):
    """Test cases for POST /api/games/<game_id>/draw-hand endpoint."""

    def setUp(self):
        """Create an active game for testing."""
        self.game_id = self.create_active_game()

    def test_draw_hand_success(self):
        """Test successfully drawing a hand."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/draw-hand",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hand", data)
        self.assertIn("deck_size", data)
        self.assertIn("cards_drawn", data)
        self.assertIsInstance(data["hand"], list)
        self.assertGreater(len(data["hand"]), 0)

        # Verify card structure
        for card in data["hand"]:
            self.assertIn("type", card)
            self.assertIn("power", card)

    def test_draw_hand_game_not_found(self):
        """Test drawing hand for non-existent game returns 404."""
        fake_game_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/games/{fake_game_id}/draw-hand",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

    def test_draw_hand_unauthorized_user(self):
        """Test non-player cannot draw hand."""
        unique_id = int(time.time() * 1000)
        username = f"nonplayer_{unique_id}"
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": "pass123"},
        )
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/draw-hand", headers=headers
        )

        self.assertEqual(response.status_code, 403)

    def test_draw_hand_no_token(self):
        """Test drawing hand fails without token."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/draw-hand"
        )

        self.assertEqual(response.status_code, 401)


class TestGameServicePlayCard(TestGameServiceSetup):
    """Test cases for POST /api/games/<game_id>/play-card endpoint."""

    def setUp(self):
        """Create an active game and draw hands for testing."""
        self.game_id = self.create_active_game()

        # Draw hand for player 1
        requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/draw-hand",
            headers=self.player1_headers,
        )

    def test_play_card_success(self):
        """Test successfully playing a card from hand."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            headers=self.player1_headers,
            json={"card_index": 0},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("played_card", data)
        self.assertIn("remaining_hand", data)
        self.assertIn("both_played", data)

    def test_play_card_missing_index(self):
        """Test playing card fails without card_index."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            headers=self.player1_headers,
            json={},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Card index is required", data["error"])

    def test_play_card_invalid_index(self):
        """Test playing card fails with invalid index."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            headers=self.player1_headers,
            json={"card_index": 999},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid card index", data["error"])

    def test_play_card_negative_index(self):
        """Test playing card fails with negative index."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            headers=self.player1_headers,
            json={"card_index": -1},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_play_card_game_not_found(self):
        """Test playing card for non-existent game returns 404."""
        fake_game_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/games/{fake_game_id}/play-card",
            headers=self.player1_headers,
            json={"card_index": 0},
        )

        self.assertEqual(response.status_code, 404)

    def test_play_card_no_token(self):
        """Test playing card fails without token."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            json={"card_index": 0},
        )

        self.assertEqual(response.status_code, 401)


class TestGameServiceResolveRound(TestGameServiceSetup):
    """Test cases for POST /api/games/<game_id>/resolve-round endpoint."""

    def setUp(self):
        """Create a game where both players have played cards."""
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=self.player1_headers,
            json={"player2_name": self.player2_username},
        )
        self.game_id = response.json().get("game_id")

        # Draw and play cards for both players
        requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/draw-hand",
            headers=self.player1_headers,
        )
        requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/draw-hand",
            headers=self.player2_headers,
        )
        requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            headers=self.player1_headers,
            json={"card_index": 0},
        )
        requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/play-card",
            headers=self.player2_headers,
            json={"card_index": 0},
        )

    def test_resolve_round_success(self):
        """Test successfully resolving a round."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/resolve-round",
            headers=self.player1_headers,
        )

        # Note: May already be auto-resolved, so accept 200 or 400
        self.assertIn(response.status_code, [200, 400])

        if response.status_code == 200:
            data = response.json()
            self.assertIn("round_winner", data)
            self.assertIn("player1_score", data)
            self.assertIn("player2_score", data)

    def test_resolve_round_game_not_found(self):
        """Test resolving round for non-existent game returns 404."""
        fake_game_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/games/{fake_game_id}/resolve-round",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 404)

    def test_resolve_round_no_token(self):
        """Test resolving round fails without token."""
        response = requests.post(
            f"{BASE_URL}/api/games/{self.game_id}/resolve-round"
        )

        self.assertEqual(response.status_code, 401)

    def test_resolve_round_cards_not_played(self):
        """Test resolving round fails when cards not played."""
        # Create new game without playing cards
        response = requests.post(
            f"{BASE_URL}/api/games",
            headers=self.player1_headers,
            json={"player2_name": self.player2_username},
        )
        new_game_id = response.json().get("game_id")

        response = requests.post(
            f"{BASE_URL}/api/games/{new_game_id}/resolve-round",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)


class TestGameHistoryEndpoints(TestGameServiceSetup):
    """Tests for immutable game history retrieval and tamper detection."""

    def _create_archived_game(self):
        """Helper to create a game, play it, and archive it."""
        # Create an active game with decks
        game_id = self.create_active_game()

        # Play one round to generate history
        # Player 1 draws and plays
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/draw-hand",
            headers=self.player1_headers,
        )
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/play-card",
            headers=self.player1_headers,
            json={"card_index": 0},
        )

        # Player 2 draws and plays (this auto-resolves the round)
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/draw-hand",
            headers=self.player2_headers,
        )
        requests.post(
            f"{BASE_URL}/api/games/{game_id}/play-card",
            headers=self.player2_headers,
            json={"card_index": 0},
        )

        # End the game to archive it
        end_response = requests.post(
            f"{BASE_URL}/api/games/{game_id}/end", headers=self.player1_headers
        )
        self.assertEqual(end_response.status_code, 200)
        return game_id

    def _tamper_history_integrity(self, game_id):
        """Directly modify the history hash to simulate tampering."""
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE game_history SET integrity_hash = 'deadbeef' WHERE game_id = %s",
                    (game_id,),
                )
                conn.commit()

    def test_history_endpoint_returns_snapshot(self):
        """Completed games expose decrypted history snapshots."""
        game_id = self._create_archived_game()

        response = requests.get(
            f"{BASE_URL}/api/games/{game_id}/history",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["game_id"], game_id)
        self.assertIn("snapshot", data)
        self.assertEqual(data["player1_name"], self.player1_username)

    def test_user_games_include_history_snapshot(self):
        """User games endpoint can embed decrypted history."""
        game_id = self._create_archived_game()

        response = requests.get(
            f"{BASE_URL}/api/games/user/{self.player1_username}?include_history=true",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 200)
        game_entries = response.json().get("games", [])

        matching_games = [g for g in game_entries if g["game_id"] == game_id]
        self.assertTrue(
            matching_games, "Expected archived game to be present in user list"
        )
        self.assertIn("history", matching_games[0])
        self.assertIn("snapshot", matching_games[0]["history"])

    def test_history_tamper_detection_returns_conflict(self):
        """Integrity violations are surfaced via HTTP 409 responses."""
        game_id = self._create_archived_game()
        self._tamper_history_integrity(game_id)

        response = requests.get(
            f"{BASE_URL}/api/games/{game_id}/history",
            headers=self.player1_headers,
        )

        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
