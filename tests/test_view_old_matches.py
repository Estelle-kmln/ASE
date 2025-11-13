import unittest
import sqlite3
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

# Import the functions we’re testing
from view_old_matches import get_old_matches, display_old_matches

TEST_DB_PATH = "test_game.db"


class TestViewOldMatches(unittest.TestCase):
    """Tests for the view_old_matches module."""

    def setUp(self):
        """Set up a temporary test database before each test."""
        # Create a new SQLite DB for testing
        self.conn = sqlite3.connect(TEST_DB_PATH)
        cursor = self.conn.cursor()

        # Create a minimal version of the games table (same structure as production)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id TEXT PRIMARY KEY,
                turn INTEGER NOT NULL,
                is_active INTEGER NOT NULL,
                current_player INTEGER NOT NULL,
                player1_name TEXT NOT NULL,
                player1_deck_cards TEXT NOT NULL,
                player1_hand_cards TEXT,
                player1_played_card TEXT,
                player1_discarded_cards TEXT,
                player2_name TEXT NOT NULL,
                player2_deck_cards TEXT NOT NULL,
                player2_hand_cards TEXT,
                player2_played_card TEXT,
                player2_discarded_cards TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

        # Patch DB_PATH in the module to use our test database
        import view_old_matches
        view_old_matches.DB_PATH = TEST_DB_PATH

    def tearDown(self):
        """Clean up after each test."""
        self.conn.close()
        Path(TEST_DB_PATH).unlink(missing_ok=True)

    def test_get_old_matches_returns_finished_games(self):
        """Test that get_old_matches() returns only completed (inactive) games."""
        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO games (game_id, turn, is_active, current_player,
                               player1_name, player1_deck_cards,
                               player2_name, player2_deck_cards)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("g1", 5, 0, 1, "alex", "[]", "katrine", "[]"),   # finished
            ("g2", 2, 1, 1, "alex", "[]", "bob", "[]"),       # active
            ("g3", 4, 0, 2, "sam", "[]", "alex", "[]"),       # finished
        ])
        self.conn.commit()

        results = get_old_matches("alex")
        self.assertEqual(len(results), 2)
        game_ids = {row[0] for row in results}
        self.assertSetEqual(game_ids, {"g1", "g3"})

    def test_get_old_matches_returns_empty_for_new_player(self):
        """Test that an unknown player gets no results."""
        results = get_old_matches("unknown")
        self.assertEqual(results, [])

    def test_display_old_matches_prints_results(self):
        """Test that display_old_matches() prints formatted results correctly."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO games (game_id, turn, is_active, current_player,
                               player1_name, player1_deck_cards,
                               player2_name, player2_deck_cards, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("g42", 10, 0, 1, "alex", "[]", "chris", "[]", "2025-01-01 12:00:00"))
        self.conn.commit()

        # Capture printed output
        buf = io.StringIO()
        with redirect_stdout(buf):
            display_old_matches("alex")

        output = buf.getvalue()
        self.assertIn("g42", output)
        self.assertIn("alex vs chris", output)
        self.assertIn("COMPLETED", output)

    def test_display_old_matches_handles_no_matches(self):
        """Test that display_old_matches() prints message when no games found."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            display_old_matches("alex")
        output = buf.getvalue()
        self.assertIn("No old matches found for player", output)


if __name__ == "__main__":
    unittest.main()
