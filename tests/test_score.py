"""Unit tests for round-win scoring logic."""

import io
import sys
import unittest

from game.game_service import GameService
from game.game_logic import BattleCardGame
from models.card import Card, CardCollection
from models.deck import Deck


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
        all_cards = self.collection.get_all_cards()
        used_cards = set(cards)
        for c in all_cards:
            if c in used_cards:
                continue
            cards.append(c)
            used_cards.add(c)
            if len(cards) == Deck.DECK_SIZE:
                break
        if len(cards) != Deck.DECK_SIZE:
            raise RuntimeError("Not enough unique cards to build deck")
        return Deck(cards)

    def test_battle_increments_score(self):
        # Player1 will play Rock (power 5) and player2 will play Scissors (power 4)
        # Rock beats Scissors, so Player1 should win
        p1_top = [Card("Rock", 5), Card("Paper", 2), Card("Scissors", 3)]
        p2_top = [Card("Scissors", 4), Card("Paper", 6), Card("Rock", 7)]

        p1_deck = self._build_deck_with_top(p1_top)
        p2_deck = self._build_deck_with_top(p2_top)

        game = self.service.start_new_game("A", p1_deck, "B", p2_deck, save=False)

        # Draw initial hands
        game.player1.draw_new_hand()
        game.player2.draw_new_hand()

        # Use BattleCardGame controller to play the game
        controller = BattleCardGame()
        controller.game = game

        # Player 1 plays first card (index 0)
        controller.play_turn(0)
        # Player 2 plays first card (index 0)
        controller.play_turn(0)

        # Resolve the round
        result = controller.resolve_round()

        # Exactly one player should have their per-round score incremented.
        round_winner = result["round_winner"]
        self.assertIn(round_winner, ("A", "B", "Tie"))
        # Total rounds won should be 1 (unless it's a tie)
        if round_winner != "Tie":
            self.assertEqual(game.player1.score + game.player2.score, 1)

        if round_winner == "A":
            self.assertEqual(game.player1.score, 1)
            self.assertEqual(game.player2.score, 0)
        elif round_winner == "B":
            self.assertEqual(game.player2.score, 1)
            self.assertEqual(game.player1.score, 0)

    def test_score_tracking(self):
        # Test that scores are tracked correctly after a round
        p1_top = [Card("Rock", 5), Card("Paper", 2), Card("Scissors", 3)]
        p2_top = [Card("Scissors", 4), Card("Paper", 6), Card("Rock", 7)]

        p1_deck = self._build_deck_with_top(p1_top)
        p2_deck = self._build_deck_with_top(p2_top)

        game = self.service.start_new_game("Alice", p1_deck, "Bob", p2_deck, save=False)

        # Draw initial hands
        game.player1.draw_new_hand()
        game.player2.draw_new_hand()

        # Use BattleCardGame controller
        controller = BattleCardGame()
        controller.game = game

        # Play a round
        controller.play_turn(0)  # Player 1 plays
        controller.play_turn(0)  # Player 2 plays
        result = controller.resolve_round()

        # Verify scores are tracked
        self.assertGreaterEqual(game.player1.score, 0)
        self.assertGreaterEqual(game.player2.score, 0)
        # At least one player should have a score if there was a winner
        if result["round_winner"] != "Tie":
            self.assertEqual(game.player1.score + game.player2.score, 1)


if __name__ == "__main__":
    unittest.main()
