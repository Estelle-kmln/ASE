"""Unit tests for round-win scoring logic."""

import io
import sys
import unittest

from game.game_service import GameService
from models.card import Card, CardCollection
from models.deck import Deck
from cli.main import CLI


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.service = GameService()
        self.collection = CardCollection()

    def _build_deck_with_top(self, top_three):
        """Build a 22-card deck where the first three cards are top_three.

        Ensures there are no duplicates within the deck.
        """
        cards = list(top_three)
        # Fill remaining with cards from collection not already used
        for c in self.collection.get_all_cards():
            if c in cards:
                continue
            cards.append(c)
            if len(cards) == Deck.DECK_SIZE:
                break
        if len(cards) != Deck.DECK_SIZE:
            raise RuntimeError("Not enough unique cards to build deck")
        return Deck(cards)

    def test_battle_increments_score(self):
        # Player1 will play rock (5 of rock) and player2 will play scissors (4 of scissors)
        p1_top = [Card(5, "rock"), Card(2, "paper"), Card(3, "scissors")]
        p2_top = [Card(4, "scissors"), Card(6, "paper"), Card(7, "rock")]

        p1_deck = self._build_deck_with_top(p1_top)
        p2_deck = self._build_deck_with_top(p2_top)

        game = self.service.start_new_game("A", p1_deck, "B", p2_deck, save=False)

        # Player 1 draws and plays first card
        game.current_player = game.player1
        hand1 = game.start_turn()
        played1 = game.play_card_for_current_player(0)

        # Player 2 draws and plays first card
        game.current_player = game.player2
        hand2 = game.start_turn()
        played2 = game.play_card_for_current_player(0)

        result = game.battle()

        # Exactly one player should have their per-round score incremented.
        winner = result["winner"]
        self.assertIn(winner, ("A", "B"))
        # Total rounds won should be 1
        self.assertEqual(game.player1_score + game.player2_score, 1)

        if winner == "A":
            self.assertEqual(game.player1_score, 1)
            self.assertEqual(game.player2_score, 0)
        else:
            self.assertEqual(game.player2_score, 1)
            self.assertEqual(game.player1_score, 0)

    def test_cli_keep_score_output(self):
        # Reuse same decks as above to get deterministic winner
        p1_top = [Card(5, "rock"), Card(2, "paper"), Card(3, "scissors")]
        p2_top = [Card(4, "scissors"), Card(6, "paper"), Card(7, "rock")]

        p1_deck = self._build_deck_with_top(p1_top)
        p2_deck = self._build_deck_with_top(p2_top)

        game = self.service.start_new_game("Alice", p1_deck, "Bob", p2_deck, save=False)

        game.current_player = game.player1
        game.start_turn()
        game.play_card_for_current_player(0)

        game.current_player = game.player2
        game.start_turn()
        game.play_card_for_current_player(0)

        game.battle()

        cli = CLI()
        captured = io.StringIO()
        sys_stdout = sys.stdout
        try:
            sys.stdout = captured
            cli.keep_score(game)
        finally:
            sys.stdout = sys_stdout

        output = captured.getvalue()
        # The battle winner may vary depending on card logic; assert the
        # printed output matches the game's recorded scores.
        self.assertIn(f"Alice: {game.player1_score}", output)
        self.assertIn(f"Bob: {game.player2_score}", output)


if __name__ == "__main__":
    unittest.main()
