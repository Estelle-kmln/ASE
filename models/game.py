"""Game model for the battle card game."""

from typing import List, Optional

from .card import Card
from .deck import Deck


class Hand:
    """Represents a hand of 3 cards for a turn."""
    
    HAND_SIZE = 3
    
    def __init__(self, cards: Optional[List[Card]] = None):
        """Initialize a hand.
        
        Args:
            cards: List of cards for the hand (must be 3 cards)
        
        Raises:
            ValueError: If cards list is not exactly 3 cards
        """
        if cards is None:
            cards = []
        
        if len(cards) != self.HAND_SIZE:
            raise ValueError(f"Hand must contain exactly {self.HAND_SIZE} cards, got {len(cards)}")
        
        self.cards = cards.copy()
        self.played_card: Optional[Card] = None
        self.discarded_cards: List[Card] = []
    
    def play_card(self, card_index: int) -> Card:
        """Play a card from the hand.
        
        Args:
            card_index: Index of the card to play (0-2)
        
        Returns:
            The played card
        
        Raises:
            IndexError: If card_index is out of range
            ValueError: If a card has already been played this turn
        """
        if self.played_card is not None:
            raise ValueError("A card has already been played this turn")
        
        if not (0 <= card_index < len(self.cards)):
            raise IndexError(f"Card index {card_index} is out of range")
        
        self.played_card = self.cards.pop(card_index)
        return self.played_card
    
    def discard_remaining(self) -> List[Card]:
        """Discard the remaining cards in the hand (should be 2 after playing).
        
        Returns:
            List of discarded cards
        """
        discarded = self.cards.copy()
        self.discarded_cards.extend(discarded)
        self.cards.clear()
        return discarded
    
    def is_complete(self) -> bool:
        """Check if the hand has been fully processed (card played, others discarded).
        
        Returns:
            True if hand is complete
        """
        return self.played_card is not None and len(self.cards) == 0
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __repr__(self) -> str:
        return f"Hand({len(self.cards)} cards, played={self.played_card is not None})"


class Game:
    """Represents the main game state."""
    
    def __init__(self, deck: Deck, game_id: Optional[str] = None):
        """Initialize a new game.
        
        Args:
            deck: The player's deck (will be shuffled)
            game_id: Optional unique identifier for the game
        """
        if not deck.shuffled:
            deck.shuffle()
        
        self.game_id = game_id
        self.deck = deck
        self.hand: Optional[Hand] = None
        self.turn = 0
        self.is_active = True
    
    def start_turn(self) -> Hand:
        """Start a new turn by drawing 3 cards.
        
        Returns:
            The new hand
        
        Raises:
            ValueError: If there are not enough cards in the deck
            ValueError: If current hand is not complete
        """
        if self.hand is not None and not self.hand.is_complete():
            raise ValueError("Cannot start new turn until current hand is complete")
        
        if len(self.deck) < Hand.HAND_SIZE:
            raise ValueError(f"Not enough cards in deck to start turn (need {Hand.HAND_SIZE}, have {len(self.deck)})")
        
        drawn_cards = self.deck.draw(Hand.HAND_SIZE)
        self.hand = Hand(drawn_cards)
        self.turn += 1
        
        return self.hand
    
    def play_turn(self, card_index: int) -> Card:
        """Play a card from the current hand.
        
        Args:
            card_index: Index of the card to play
        
        Returns:
            The played card
        
        Raises:
            ValueError: If no hand is available
        """
        if self.hand is None:
            raise ValueError("No hand available. Start a turn first.")
        
        played_card = self.hand.play_card(card_index)
        
        # Automatically discard remaining cards
        if len(self.hand.cards) > 0:
            self.hand.discard_remaining()
        
        return played_card
    
    def __repr__(self) -> str:
        return f"Game(id={self.game_id}, turn={self.turn}, active={self.is_active})"

