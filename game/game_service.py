"""Game service for initializing and managing games."""

import uuid
from typing import List, Optional

from database.game_repository import GameRepository
from models.card import Card, CardCollection
from models.deck import Deck
from models.game import Game


class GameService:
    """Service for managing game initialization and operations."""
    
    def __init__(self, repository: Optional[GameRepository] = None):
        """Initialize the game service.
        
        Args:
            repository: Optional game repository for persistence
        """
        self.collection = CardCollection()
        self.repository = repository or GameRepository()
    
    def get_card_collection(self) -> CardCollection:
        """Get the full card collection.
        
        Returns:
            CardCollection with all 39 cards
        """
        return self.collection
    
    def create_deck(self, selected_cards: List[Card]) -> Deck:
        """Create a deck from selected cards.
        
        Args:
            selected_cards: List of 22 cards to include in the deck
        
        Returns:
            A new Deck instance
        
        Raises:
            ValueError: If the number of cards is not 22 or if there are duplicates
        """
        return Deck(selected_cards)
    
    def start_new_game(self, deck: Deck, save: bool = True) -> Game:
        """Start a new game with the given deck.
        
        Args:
            deck: The player's deck of 22 cards
            save: Whether to save the game to the database
        
        Returns:
            A new Game instance with the deck shuffled and ready to play
        
        Raises:
            ValueError: If deck is invalid
        """
        if len(deck) != Deck.DECK_SIZE:
            raise ValueError(f"Deck must have {Deck.DECK_SIZE} cards")
        
        game_id = str(uuid.uuid4())
        game = Game(deck, game_id=game_id)
        
        if save:
            self.repository.save_game(game)
        
        return game
    
    def validate_deck_selection(self, selected_cards: List[Card]) -> tuple:
        """Validate a deck selection.
        
        Args:
            selected_cards: List of selected cards
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(selected_cards) != Deck.DECK_SIZE:
            return False, f"Deck must contain exactly {Deck.DECK_SIZE} cards, got {len(selected_cards)}"
        
        # Check for duplicates
        if len(set(selected_cards)) != len(selected_cards):
            return False, "Deck cannot contain duplicate cards"
        
        # Check all cards are valid
        for card in selected_cards:
            if card not in self.collection.cards:
                return False, f"Card {card} is not in the available collection"
        
        return True, ""

