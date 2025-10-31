"""Game service for initializing and managing games."""

import random
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
    
    def create_random_deck(self) -> Deck:
        """Create a random deck of 22 cards from the collection.
        
        Returns:
            A new Deck instance with 22 randomly selected cards
        """
        all_cards = self.collection.get_all_cards()
        selected_cards = random.sample(all_cards, Deck.DECK_SIZE)
        return Deck(selected_cards)
    
    def start_new_game(self, player1_name: str, player1_deck: Deck, player2_name: str, player2_deck: Deck, save: bool = True) -> Game:
        """Start a new game with 2 players.
        
        Args:
            player1_name: Name of the first player
            player1_deck: First player's deck of 22 cards
            player2_name: Name of the second player
            player2_deck: Second player's deck of 22 cards
            save: Whether to save the game to the database
        
        Returns:
            A new Game instance with both players ready to play
        
        Raises:
            ValueError: If either deck is invalid
        """
        if len(player1_deck) != Deck.DECK_SIZE:
            raise ValueError(f"Player 1 deck must have {Deck.DECK_SIZE} cards")
        if len(player2_deck) != Deck.DECK_SIZE:
            raise ValueError(f"Player 2 deck must have {Deck.DECK_SIZE} cards")
        
        game_id = str(uuid.uuid4())
        game = Game(player1_name, player1_deck, player2_name, player2_deck, game_id=game_id)
        
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

