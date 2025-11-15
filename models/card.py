"""Card model - compatibility layer."""

from game.game_logic import Card

# For backward compatibility, try to create a CardCollection-like class
# Note: The actual Card class uses 'type' and 'power', not 'suit' and 'value'
# This is a compatibility layer that may not work perfectly with all tests

class CardCollection:
    """Card collection compatibility class."""
    
    def __init__(self):
        """Initialize card collection with all 39 cards."""
        self.cards = []
        # Create all 39 cards: 13 powers × 3 types
        for card_type in ['Rock', 'Paper', 'Scissors']:
            for power in range(1, 14):
                self.cards.append(Card(card_type, power))
    
    def __len__(self):
        return len(self.cards)
    
    def get_all_cards(self):
        """Get all cards in the collection."""
        return self.cards.copy()

__all__ = ["Card", "CardCollection"]

