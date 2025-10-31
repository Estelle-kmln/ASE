"""Deck model for the battle card game."""

import random
from typing import List, Optional

from .card import Card


class Deck:
    """Represents a player's deck of 22 cards."""
    
    DECK_SIZE = 22
    
    def __init__(self, cards: Optional[List[Card]] = None):
        """Initialize a deck.
        
        Args:
            cards: List of cards for the deck (must be 22 cards)
        
        Raises:
            ValueError: If cards list is not exactly 22 cards
        """
        if cards is None:
            cards = []
        
        if len(cards) != self.DECK_SIZE:
            raise ValueError(f"Deck must contain exactly {self.DECK_SIZE} cards, got {len(cards)}")
        
        # Validate no duplicate cards
        if len(set(cards)) != len(cards):
            raise ValueError("Deck cannot contain duplicate cards")
        
        self.cards = cards.copy()
        self.shuffled = False
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
        self.shuffled = True
    
    def draw(self, count: int = 1) -> List[Card]:
        """Draw cards from the top of the deck.
        
        Args:
            count: Number of cards to draw
        
        Returns:
            List of drawn cards
        
        Raises:
            ValueError: If trying to draw more cards than available
        """
        if count > len(self.cards):
            raise ValueError(f"Cannot draw {count} cards, only {len(self.cards)} available")
        
        drawn = self.cards[:count]
        self.cards = self.cards[count:]
        return drawn
    
    def add_to_bottom(self, cards: List[Card]):
        """Add cards to the bottom of the deck.
        
        Args:
            cards: List of cards to add
        """
        self.cards.extend(cards)
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __repr__(self) -> str:
        return f"Deck({len(self.cards)} cards)"
    
    def get_remaining(self) -> int:
        """Get the number of remaining cards in the deck.
        
        Returns:
            Number of cards remaining
        """
        return len(self.cards)

