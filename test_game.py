"""Test script for the game functionality."""

from game.game_service import GameService
from models.card import Card, CardCollection
from models.deck import Deck


def test_card_collection():
    """Test that card collection has 39 cards."""
    print("Testing Card Collection...")
    collection = CardCollection()
    assert len(collection) == 39, f"Expected 39 cards, got {len(collection)}"
    print(f"✓ Card collection has {len(collection)} cards")
    
    # Verify all suits and values
    suits = {"rock", "paper", "scissors"}
    for suit in suits:
        cards = [c for c in collection.cards if c.suit == suit]
        assert len(cards) == 13, f"Expected 13 cards for {suit}, got {len(cards)}"
    print("✓ All suits have 13 cards (1-13)")
    print()


def test_deck_creation():
    """Test deck creation with 22 cards."""
    print("Testing Deck Creation...")
    collection = CardCollection()
    all_cards = collection.get_all_cards()
    
    # Select first 22 cards
    selected_cards = all_cards[:22]
    deck = Deck(selected_cards)
    
    assert len(deck) == 22, f"Expected deck size 22, got {len(deck)}"
    print(f"✓ Deck created with {len(deck)} cards")
    
    # Test shuffle
    original_order = deck.cards.copy()
    deck.shuffle()
    assert deck.shuffled, "Deck should be marked as shuffled"
    # Note: shuffle might result in same order, so we just check shuffled flag
    print("✓ Deck can be shuffled")
    print()


def test_random_deck():
    """Test random deck creation."""
    print("Testing Random Deck Creation...")
    service = GameService()
    
    # Create multiple random decks to ensure they're different
    deck1 = service.create_random_deck()
    deck2 = service.create_random_deck()
    
    assert len(deck1) == 22, f"Random deck 1 should have 22 cards, got {len(deck1)}"
    assert len(deck2) == 22, f"Random deck 2 should have 22 cards, got {len(deck2)}"
    
    # Verify no duplicates within each deck
    assert len(set(deck1.cards)) == 22, "Deck 1 should have no duplicates"
    assert len(set(deck2.cards)) == 22, "Deck 2 should have no duplicates"
    
    print(f"✓ Random deck created with {len(deck1)} cards")
    print("✓ Random decks have no duplicates")
    
    # Decks will likely be different (very low probability of being the same)
    # But we don't assert on this as it's probabilistic
    print("✓ Random deck generation works")
    print()


def test_game_start():
    """Test starting a new game."""
    print("Testing Game Start...")
    service = GameService()
    
    # Create decks for both players
    collection = CardCollection()
    selected_cards1 = collection.get_all_cards()[:22]
    selected_cards2 = collection.get_all_cards()[5:27]  # Different cards
    deck1 = service.create_deck(selected_cards1)
    deck2 = service.create_deck(selected_cards2)
    
    # Start game
    game = service.start_new_game("Player1", deck1, "Player2", deck2, save=False)
    
    assert game.game_id is not None, "Game should have an ID"
    assert game.turn == 0, f"Game should start at turn 0, got {game.turn}"
    assert game.is_active, "Game should be active"
    assert len(game.player1.deck) == 22, f"Player1 deck should have 22 cards, got {len(game.player1.deck)}"
    assert len(game.player2.deck) == 22, f"Player2 deck should have 22 cards, got {len(game.player2.deck)}"
    assert game.player1.deck.shuffled, "Player1 deck should be shuffled"
    assert game.player2.deck.shuffled, "Player2 deck should be shuffled"
    assert game.current_player == game.player1, "Player1 should start"
    
    print(f"✓ Game started successfully")
    print(f"  Game ID: {game.game_id}")
    print(f"  Turn: {game.turn}")
    print(f"  Player1 deck: {len(game.player1.deck)} cards")
    print(f"  Player2 deck: {len(game.player2.deck)} cards")
    print(f"  Starting player: {game.current_player.name}")
    print()


def test_deck_validation():
    """Test deck validation."""
    print("Testing Deck Validation...")
    service = GameService()
    collection = CardCollection()
    all_cards = collection.get_all_cards()
    
    # Test valid deck
    valid_cards = all_cards[:22]
    is_valid, error = service.validate_deck_selection(valid_cards)
    assert is_valid, f"Valid deck should pass validation: {error}"
    print("✓ Valid deck (22 unique cards) passes validation")
    
    # Test invalid size
    invalid_size = all_cards[:21]  # Only 21 cards
    is_valid, error = service.validate_deck_selection(invalid_size)
    assert not is_valid, "Deck with 21 cards should fail validation"
    assert "22" in error, "Error should mention required deck size"
    print(f"✓ Invalid deck size correctly rejected: {error}")
    
    # Test duplicates
    duplicate_cards = all_cards[:21] + [all_cards[0]]  # 21 unique + 1 duplicate
    is_valid, error = service.validate_deck_selection(duplicate_cards)
    assert not is_valid, "Deck with duplicates should fail validation"
    assert "duplicate" in error.lower(), "Error should mention duplicates"
    print(f"✓ Duplicate cards correctly rejected: {error}")
    print()


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("  RUNNING TESTS")
    print("=" * 50)
    print()
    
    try:
        test_card_collection()
        test_deck_creation()
        test_random_deck()
        test_deck_validation()
        test_game_start()
        
        print("=" * 50)
        print("  ALL TESTS PASSED! ✓")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()

