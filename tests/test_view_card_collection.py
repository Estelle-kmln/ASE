import unittest
from io import StringIO
from unittest.mock import patch
from view_card_collection import get_full_card_collection, display_card_collection


class TestViewCardCollection(unittest.TestCase):
    def test_get_full_card_collection_returns_39_cards(self):
        cards = get_full_card_collection()
        self.assertEqual(len(cards), 39)
        # Cards are dictionaries from the database
        types = {c['type'] for c in cards}
        powers = {c['power'] for c in cards}
        self.assertSetEqual(types, {"Rock", "Paper", "Scissors"})
        self.assertSetEqual(powers, set(range(1, 14)))

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_card_collection_prints_output(self, mock_stdout):
        display_card_collection()
        output = mock_stdout.getvalue()
        # Basic structure checks
        self.assertIn("CARD COLLECTION", output)
        self.assertIn("ROCK CARDS", output)
        self.assertIn("PAPER CARDS", output)
        self.assertIn("SCISSORS CARDS", output)
        # Check some example cards
        self.assertIn("Rock 1", output)
        self.assertIn("Paper 13", output)
        self.assertIn("Scissors 5", output)


if __name__ == "__main__":
    unittest.main()
