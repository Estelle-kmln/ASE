"""Repository for persisting game state to database."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from models.card import Card
from models.deck import Deck
from models.game import Game, Hand


class GameRepository:
    """Repository for game persistence."""
    
    def __init__(self, db_path: str = "game.db"):
        """Initialize the repository.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Games table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    turn INTEGER NOT NULL,
                    is_active INTEGER NOT NULL,
                    deck_cards TEXT NOT NULL,
                    hand_cards TEXT,
                    played_card TEXT,
                    discarded_cards TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _card_to_dict(self, card: Card) -> dict:
        """Convert a card to a dictionary."""
        return {"value": card.value, "suit": card.suit}
    
    def _dict_to_card(self, card_dict: dict) -> Card:
        """Convert a dictionary to a card."""
        return Card(card_dict["value"], card_dict["suit"])
    
    def _serialize_cards(self, cards: list[Card]) -> str:
        """Serialize a list of cards to JSON string."""
        return json.dumps([self._card_to_dict(card) for card in cards])
    
    def _deserialize_cards(self, cards_json: str) -> list[Card]:
        """Deserialize a JSON string to a list of cards."""
        if not cards_json:
            return []
        cards_data = json.loads(cards_json)
        return [self._dict_to_card(card_dict) for card_dict in cards_data]
    
    def save_game(self, game: Game):
        """Save a game to the database.
        
        Args:
            game: The game to save
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Serialize deck cards
            deck_cards_json = self._serialize_cards(game.deck.cards)
            
            # Serialize hand if it exists
            hand_cards_json = None
            played_card_json = None
            discarded_cards_json = None
            
            if game.hand:
                hand_cards_json = self._serialize_cards(game.hand.cards)
                if game.hand.played_card:
                    played_card_json = json.dumps(self._card_to_dict(game.hand.played_card))
                if game.hand.discarded_cards:
                    discarded_cards_json = self._serialize_cards(game.hand.discarded_cards)
            
            cursor.execute("""
                INSERT OR REPLACE INTO games
                (game_id, turn, is_active, deck_cards, hand_cards, played_card, discarded_cards, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                game.game_id,
                game.turn,
                1 if game.is_active else 0,
                deck_cards_json,
                hand_cards_json,
                played_card_json,
                discarded_cards_json
            ))
            
            conn.commit()
    
    def load_game(self, game_id: str) -> Optional[Game]:
        """Load a game from the database.
        
        Args:
            game_id: The ID of the game to load
        
        Returns:
            The loaded Game, or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT game_id, turn, is_active, deck_cards, hand_cards, played_card, discarded_cards
                FROM games
                WHERE game_id = ?
            """, (game_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            game_id_db, turn, is_active, deck_cards_json, hand_cards_json, played_card_json, discarded_cards_json = row
            
            # Deserialize deck
            deck_cards = self._deserialize_cards(deck_cards_json)
            deck = Deck(deck_cards)
            deck.shuffled = True  # Assume saved decks are shuffled
            
            # Create game
            game = Game(deck, game_id=game_id_db)
            game.turn = turn
            game.is_active = bool(is_active)
            
            # Deserialize hand if it exists
            if hand_cards_json:
                hand_cards = self._deserialize_cards(hand_cards_json)
                if len(hand_cards) == Hand.HAND_SIZE:
                    game.hand = Hand(hand_cards)
                    
                    if played_card_json:
                        played_card_dict = json.loads(played_card_json)
                        game.hand.played_card = self._dict_to_card(played_card_dict)
                        # If card was played, discard the remaining
                        if len(game.hand.cards) > 0:
                            game.hand.discarded_cards = game.hand.cards.copy()
                            game.hand.cards.clear()
                    
                    if discarded_cards_json:
                        game.hand.discarded_cards = self._deserialize_cards(discarded_cards_json)
            
            return game
    
    def list_games(self, active_only: bool = False) -> list[dict]:
        """List all games.
        
        Args:
            active_only: If True, only return active games
        
        Returns:
            List of game information dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT game_id, turn, is_active, created_at FROM games"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [
                {
                    "game_id": row[0],
                    "turn": row[1],
                    "is_active": bool(row[2]),
                    "created_at": row[3]
                }
                for row in rows
            ]
    
    def delete_game(self, game_id: str) -> bool:
        """Delete a game from the database.
        
        Args:
            game_id: The ID of the game to delete
        
        Returns:
            True if game was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
            conn.commit()
            
            return cursor.rowcount > 0

