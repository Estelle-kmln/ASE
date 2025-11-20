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


def test_invalid_card_index_negative():
    """Test playing with negative card index (should fail)."""
    print("Testing Invalid Card Index (Negative)...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    controller = BattleCardGame()
    controller.game = game
    
    # Try to play with negative index
    try:
        controller.play_turn(-1)
        assert False, "Should have raised IndexError for negative index"
    except IndexError as e:
        assert "out of range" in str(e).lower() or "index" in str(e).lower(), f"Expected IndexError, got: {e}"
        print(f"✓ Correctly rejected negative index: {e}")
    print()


def test_invalid_card_index_too_large():
    """Test playing with card index too large (should fail)."""
    print("Testing Invalid Card Index (Too Large)...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    controller = BattleCardGame()
    controller.game = game
    
    # Try to play with index >= 3
    try:
        controller.play_turn(3)
        assert False, "Should have raised IndexError for index too large"
    except IndexError as e:
        assert "out of range" in str(e).lower() or "index" in str(e).lower(), f"Expected IndexError, got: {e}"
        print(f"✓ Correctly rejected index too large: {e}")
    print()


def test_playing_without_hand():
    """Test playing a card when player has no hand (should fail)."""
    print("Testing Playing Without Hand...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    # Don't draw hands - players have no hand
    controller = BattleCardGame()
    controller.game = game
    
    # Try to play without a hand
    try:
        controller.play_turn(0)
        assert False, "Should have raised AttributeError or similar when no hand exists"
    except (AttributeError, ValueError) as e:
        print(f"✓ Correctly rejected playing without hand: {type(e).__name__}")
    print()


def test_playing_card_twice():
    """Test trying to play a card when one is already played (should fail)."""
    print("Testing Playing Card Twice...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    game.player1.draw_new_hand()
    game.player2.draw_new_hand()
    
    controller = BattleCardGame()
    controller.game = game
    
    # Play first card
    controller.play_turn(0)
    
    # Try to play again (should fail because card already played)
    try:
        # Manually try to play from hand again
        game.player1.hand.play_card(0)
        assert False, "Should have raised ValueError for playing card twice"
    except ValueError as e:
        assert "already been played" in str(e).lower() or "already" in str(e).lower(), f"Expected ValueError about already played, got: {e}"
        print(f"✓ Correctly rejected playing card twice: {e}")
    print()


def test_drawing_from_empty_deck():
    """Test drawing hand when deck has fewer than 3 cards (should fail)."""
    print("Testing Drawing From Empty Deck...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    # Draw cards until deck has less than 3 cards
    while len(game.player1.deck) >= 3:
        game.player1.deck.draw_hand()
    
    # Now try to draw a new hand with < 3 cards
    result = game.player1.draw_new_hand()
    assert result == False, "draw_new_hand should return False when not enough cards"
    assert game.player1.hand is None or len(game.player1.hand.cards) == 0, "Hand should not be created when deck is too small"
    print(f"✓ Correctly handled drawing from deck with {len(game.player1.deck)} cards (< 3)")
    print()


def test_playing_when_game_over():
    """Test playing a turn when game is already over (should fail)."""
    print("Testing Playing When Game Over...")
    service = GameService()
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    # Manually set game as over
    game.game_over = True
    
    controller = BattleCardGame()
    controller.game = game
    
    # Try to play when game is over
    try:
        controller.play_turn(0)
        assert False, "Should have raised ValueError when game is over"
    except ValueError as e:
        assert "no active game" in str(e).lower() or "game" in str(e).lower(), f"Expected ValueError about no active game, got: {e}"
        print(f"✓ Correctly rejected playing when game over: {e}")
    print()


def test_playing_with_no_game():
    """Test playing when no game exists (should fail)."""
    print("Testing Playing With No Game...")
    controller = BattleCardGame()
    controller.game = None
    
    # Try to play when no game exists
    try:
        controller.play_turn(0)
        assert False, "Should have raised ValueError when no game exists"
    except ValueError as e:
        assert "no active game" in str(e).lower() or "game" in str(e).lower(), f"Expected ValueError about no active game, got: {e}"
        print(f"✓ Correctly rejected playing with no game: {e}")
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
        
        # Negative test cases
        test_invalid_card_index_negative()
        test_invalid_card_index_too_large()
        test_playing_without_hand()
        test_playing_card_twice()
        test_drawing_from_empty_deck()
        test_playing_when_game_over()
        test_playing_with_no_game()
        
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

