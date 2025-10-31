"""Test script for hand functionality."""

from game.game_service import GameService
from models.game import Game, Hand


def test_hand_drawing():
    """Test drawing 3 cards for a turn."""
    print("Testing Hand Drawing...")
    service = GameService()
    deck = service.create_random_deck()
    game = service.start_new_game(deck, save=False)
    
    initial_deck_size = len(game.deck)
    assert initial_deck_size == 22, f"Expected 22 cards, got {initial_deck_size}"
    
    # Start turn - should draw 3 cards
    hand = game.start_turn()
    
    assert game.turn == 1, f"Turn should be 1, got {game.turn}"
    assert len(hand.cards) == 3, f"Hand should have 3 cards, got {len(hand.cards)}"
    assert len(game.deck) == initial_deck_size - 3, f"Deck should have {initial_deck_size - 3} cards, got {len(game.deck)}"
    
    print(f"✓ Turn {game.turn} started")
    print(f"✓ Drew 3 cards: {[str(c) for c in hand.cards]}")
    print(f"✓ Deck now has {len(game.deck)} cards")
    print()


def test_playing_card():
    """Test playing a card and discarding the other 2."""
    print("Testing Playing Card...")
    service = GameService()
    deck = service.create_random_deck()
    game = service.start_new_game(deck, save=False)
    
    # Start turn
    hand = game.start_turn()
    original_hand = hand.cards.copy()
    
    # Play the first card (index 0)
    played_card = game.play_turn(0)
    
    assert played_card == original_hand[0], "Played card should match first card"
    assert hand.played_card == played_card, "Hand should record played card"
    assert len(hand.cards) == 0, "Hand should be empty after playing"
    assert len(hand.discarded_cards) == 2, "Should have 2 discarded cards"
    assert hand.discarded_cards == original_hand[1:], "Discarded cards should be the other 2"
    assert hand.is_complete(), "Hand should be complete after playing and discarding"
    
    print(f"✓ Played: {played_card}")
    print(f"✓ Discarded: {[str(c) for c in hand.discarded_cards]}")
    print(f"✓ Hand is complete")
    print()


def test_multiple_turns():
    """Test playing multiple turns."""
    print("Testing Multiple Turns...")
    service = GameService()
    deck = service.create_random_deck()
    game = service.start_new_game(deck, save=False)
    
    initial_deck_size = len(game.deck)
    turns_played = 0
    
    # Play 5 turns (should use 15 cards)
    for i in range(5):
        if len(game.deck) < 3:
            break
        
        hand = game.start_turn()
        assert len(hand.cards) == 3, f"Turn {game.turn}: Hand should have 3 cards"
        
        # Play first card
        played = game.play_turn(0)
        assert hand.is_complete(), f"Turn {game.turn}: Hand should be complete"
        
        turns_played += 1
    
    cards_used = turns_played * 3
    remaining = initial_deck_size - cards_used
    
    assert len(game.deck) == remaining, f"Should have {remaining} cards left, got {len(game.deck)}"
    assert game.turn == turns_played, f"Should be on turn {turns_played}, got {game.turn}"
    
    print(f"✓ Played {turns_played} turns")
    print(f"✓ Used {cards_used} cards")
    print(f"✓ {len(game.deck)} cards remaining")
    print()


def test_all_cards_used():
    """Test game behavior when deck runs out."""
    print("Testing Deck Exhaustion...")
    service = GameService()
    deck = service.create_random_deck()
    game = service.start_new_game(deck, save=False)
    
    # Play turns until we can't draw 3 cards
    while len(game.deck) >= 3:
        hand = game.start_turn()
        game.play_turn(0)  # Play first card
    
    # Should have less than 3 cards remaining
    assert len(game.deck) < 3, "Should have less than 3 cards remaining"
    print(f"✓ Deck exhausted with {len(game.deck)} cards remaining")
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

