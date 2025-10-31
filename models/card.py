"""Card models for the battle card game."""

from typing import List


class Card:
    """Represents a single card with a value and suit."""
    
    SUITS = ["rock", "paper", "scissors"]
    MIN_VALUE = 1
    MAX_VALUE = 13
    
    def __init__(self, value: int, suit: str):
        """Initialize a card.
        
        Args:
            value: Card value from 1 to 13
            suit: Card suit ("rock", "paper", or "scissors")
        
        Raises:
            ValueError: If value is out of range or suit is invalid
        """
        if not (self.MIN_VALUE <= value <= self.MAX_VALUE):
            raise ValueError(f"Card value must be between {self.MIN_VALUE} and {self.MAX_VALUE}")
        if suit not in self.SUITS:
            raise ValueError(f"Suit must be one of {self.SUITS}")
        
        self.value = value
        self.suit = suit
    
    def __repr__(self) -> str:
        return f"Card({self.value}, '{self.suit}')"
    
    def __str__(self) -> str:
        return f"{self.value} of {self.suit}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.value == other.value and self.suit == other.suit
    
    def __hash__(self) -> int:
        return hash((self.value, self.suit))


class CardCollection:
    """Collection of all available cards (39 cards total)."""
    
    TOTAL_CARDS = 39  # 13 values × 3 suits
    
    def __init__(self):
        """Initialize the card collection with all 39 cards."""
        self.cards: List[Card] = []
        self._generate_collection()
    
    def _generate_collection(self):
        """Generate all 39 cards (1-13 for each suit)."""
        for suit in Card.SUITS:
            for value in range(Card.MIN_VALUE, Card.MAX_VALUE + 1):
                self.cards.append(Card(value, suit))
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __iter__(self):
        return iter(self.cards)
    
    def __getitem__(self, index: int) -> Card:
        return self.cards[index]
    
    def get_card(self, value: int, suit: str) -> Card:
        """Get a specific card from the collection.
        
        Args:
            value: Card value
            suit: Card suit
        
        Returns:
            The card if found
        
        Raises:
            ValueError: If card not found
        """
        card = Card(value, suit)
        if card in self.cards:
            return card
        raise ValueError(f"Card {card} not found in collection")
    
    def get_all_cards(self) -> List[Card]:
        """Get all cards in the collection.
        
        Returns:
            List of all cards
        """
        return self.cards.copy()

