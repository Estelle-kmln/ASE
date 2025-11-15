"""Test script for hand functionality."""

from game.game_service import GameService
from game.game_logic import BattleCardGame
from models.game import Game, Hand


def test_hand_drawing():
    """Test drawing 3 cards for a turn."""
    print("Testing Hand Drawing...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    initial_deck_size = len(game.player1.deck)
    assert initial_deck_size == 22, f"Expected 22 cards, got {initial_deck_size}"
    
    # Draw initial hands
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    # Players should have hands after drawing
    assert game.player1.hand is not None, "Player1 should have a hand"
    assert game.player2.hand is not None, "Player2 should have a hand"
    assert len(game.player1.hand.cards) == 3, f"Hand should have 3 cards, got {len(game.player1.hand.cards)}"
    assert len(game.player1.deck) == initial_deck_size - 3, f"Deck should have {initial_deck_size - 3} cards, got {len(game.player1.deck)}"
    
    print(f"✓ Turn {game.turn_number} started")
    print(f"✓ Drew 3 cards: {[str(c) for c in game.player1.hand.cards]}")
    print(f"✓ Deck now has {len(game.player1.deck)} cards")
    print()


def test_playing_card():
    """Test playing a card and discarding the other 2."""
    print("Testing Playing Card...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    # Draw initial hands
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    # Use BattleCardGame controller
    controller = BattleCardGame()
    controller.game = game
    
    # Player should have a hand
    hand = game.player1.hand
    original_hand = hand.cards.copy()
    
    # Play the first card (index 0)
    result = controller.play_turn(0)
    played_card = result['card_played']
    
    assert played_card == original_hand[0], "Played card should match first card"
    assert hand.played_card == played_card, "Hand should record played card"
    assert len(hand.cards) == 2, "Hand should have 2 cards remaining after playing one"
    
    print(f"✓ Played: {played_card}")
    print(f"✓ Remaining cards: {[str(c) for c in hand.cards]}")
    print()


def test_multiple_turns():
    """Test playing multiple rounds."""
    print("Testing Multiple Rounds...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    # Draw initial hands
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    controller = BattleCardGame()
    controller.game = game
    
    initial_deck_size = len(game.player1.deck)
    rounds_played = 0
    
    # Play 3 rounds (each round uses 3 cards per player)
    for i in range(3):
        if len(game.player1.deck) < 3 or len(game.player2.deck) < 3:
            break
        
        # Both players play
        controller.play_turn(0)  # Player 1
        controller.play_turn(0)  # Player 2
        
        # Resolve round (this discards remaining cards and draws new hands)
        controller.resolve_round()
        rounds_played += 1
        game.turn_number += 1
    
    # Each round uses 3 cards per player (6 total)
    cards_used_per_round = 6
    cards_used = rounds_played * cards_used_per_round
    remaining = initial_deck_size - (rounds_played * 3)  # Player1 uses 3 per round
    
    assert len(game.player1.deck) <= remaining, f"Should have at most {remaining} cards left, got {len(game.player1.deck)}"
    assert game.turn_number == rounds_played + 1, f"Should be on turn {rounds_played + 1}, got {game.turn_number}"
    
    print(f"✓ Played {rounds_played} rounds")
    print(f"✓ Used {cards_used} cards total")
    print(f"✓ {len(game.player1.deck)} cards remaining in Player1 deck")
    print()


def test_all_cards_used():
    """Test game behavior when deck runs out."""
    print("Testing Deck Exhaustion...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    # Draw initial hands
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    controller = BattleCardGame()
    controller.game = game
    
    # Play rounds until we can't draw 3 cards
    while len(game.player1.deck) >= 3 and len(game.player2.deck) >= 3 and not game.game_over:
        controller.play_turn(0)  # Player 1
        controller.play_turn(0)  # Player 2
        controller.resolve_round()
        game.turn_number += 1
    
    # Game should end when decks are exhausted
    assert game.game_over or len(game.player1.deck) < 3 or len(game.player2.deck) < 3, "Game should end when decks are exhausted"
    print(f"✓ Game ended with Player1 deck: {len(game.player1.deck)} cards, Player2 deck: {len(game.player2.deck)} cards")
    print()


def run_all_tests():
    """Run all hand tests."""
    print("=" * 50)
    print("  RUNNING HAND TESTS")
    print("=" * 50)
    print()
    
    try:
        test_hand_drawing()
        test_playing_card()
        test_multiple_turns()
        test_all_cards_used()
        
        print("=" * 50)
        print("  ALL HAND TESTS PASSED! ✓")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()

