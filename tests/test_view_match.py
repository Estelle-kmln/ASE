import unittest
from io import StringIO
from unittest.mock import patch, MagicMock
from view_match import view_match_details


class TestViewMatchDetails(unittest.TestCase):

    @patch("sys.stdout", new_callable=StringIO)
    @patch("view_match.GameRepository")
    def test_no_games_in_database(self, mock_repo, mock_stdout):
        """Testira slučaj kada u bazi nema nijedne igre."""
        mock_repo.return_value.list_games.return_value = []

        view_match_details()

        output = mock_stdout.getvalue()
        self.assertIn("No games found", output)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("builtins.input", return_value="5")
    @patch("view_match.GameRepository")
    def test_invalid_selection(self, mock_repo, mock_input, mock_stdout):
        """Testira unos broja koji ne postoji u listi mečeva."""
        mock_repo.return_value.list_games.return_value = [
            {"game_id": 1, "turn": 3, "is_active": True, "created_at": "2024-06-12 10:00:00"}
        ]

        view_match_details()

        output = mock_stdout.getvalue()
        self.assertIn("Invalid selection", output)

    @patch("sys.stdout", new_callable=StringIO)
    @patch("builtins.input", return_value="1")
    @patch("view_match.GameRepository")
    def test_valid_selection(self, mock_repo, mock_input, mock_stdout):
        """Testira normalan tok kada korisnik izabere postojeći meč."""
        # Fake podaci o igrama
        mock_repo.return_value.list_games.return_value = [
            {"game_id": 1, "turn": 5, "is_active": True, "created_at": "2024-06-12 10:00:00"}
        ]

        # Kreiraj lažni objekat igre
        fake_game = MagicMock()
        fake_game.game_id = 1
        fake_game.turn = 5
        fake_game.is_active = True
        fake_game.current_player.name = "Alice"
        fake_game.player1.name = "Alice"
        fake_game.player2.name = "Bob"

        # Minimalni set potrebnih atributa
        fake_game.player1.deck.cards = [1, 2, 3]
        fake_game.player2.deck.cards = [4, 5, 6]

        fake_game.player1.hand.cards = []
        fake_game.player2.hand.cards = []
        fake_game.player1.hand.played_card = None
        fake_game.player2.hand.played_card = None
        fake_game.player1.hand.discarded_cards = []
        fake_game.player2.hand.discarded_cards = []

        mock_repo.return_value.load_game.return_value = fake_game

        view_match_details()

        output = mock_stdout.getvalue()
        self.assertIn("Match Details", output)
        self.assertIn("Alice", output)
        self.assertIn("Bob", output)
        self.assertIn("Turn: 5", output)
        self.assertIn("✅ End of match details", output)


if __name__ == "__main__":
    unittest.main()
