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
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='games'
            """)
            
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if we need to migrate (old schema doesn't have current_player)
                cursor.execute("PRAGMA table_info(games)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'current_player' not in columns:
                    # Migrate: drop old table and create new one
                    # Note: This will lose old game data, but that's okay for development
                    cursor.execute("DROP TABLE games")
                    table_exists = False
            
            if not table_exists:
                # Games table - updated for 2-player games
                cursor.execute("""
                    CREATE TABLE games (
                        game_id TEXT PRIMARY KEY,
                        turn INTEGER NOT NULL,
                        is_active INTEGER NOT NULL,
                        current_player INTEGER NOT NULL,
                        player1_name TEXT NOT NULL,
                        player1_deck_cards TEXT NOT NULL,
                        player1_hand_cards TEXT,
                        player1_played_card TEXT,
                        player1_discarded_cards TEXT,
                        player2_name TEXT NOT NULL,
                        player2_deck_cards TEXT NOT NULL,
                        player2_hand_cards TEXT,
                        player2_played_card TEXT,
                        player2_discarded_cards TEXT,
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
            
            # Determine current player (1 or 2)
            current_player_num = 1 if game.current_player == game.player1 else 2
            
            # Serialize player1 data
            player1_deck_json = self._serialize_cards(game.player1.deck.cards)
            player1_hand_json = None
            player1_played_json = None
            player1_discarded_json = None
            
            if game.player1.hand:
                player1_hand_json = self._serialize_cards(game.player1.hand.cards)
                if game.player1.hand.played_card:
                    player1_played_json = json.dumps(self._card_to_dict(game.player1.hand.played_card))
                if game.player1.hand.discarded_cards:
                    player1_discarded_json = self._serialize_cards(game.player1.hand.discarded_cards)
            
            # Serialize player2 data
            player2_deck_json = self._serialize_cards(game.player2.deck.cards)
            player2_hand_json = None
            player2_played_json = None
            player2_discarded_json = None
            
            if game.player2.hand:
                player2_hand_json = self._serialize_cards(game.player2.hand.cards)
                if game.player2.hand.played_card:
                    player2_played_json = json.dumps(self._card_to_dict(game.player2.hand.played_card))
                if game.player2.hand.discarded_cards:
                    player2_discarded_json = self._serialize_cards(game.player2.hand.discarded_cards)
            
            cursor.execute("""
                INSERT OR REPLACE INTO games
                (game_id, turn, is_active, current_player, 
                 player1_name, player1_deck_cards, player1_hand_cards, player1_played_card, player1_discarded_cards,
                 player2_name, player2_deck_cards, player2_hand_cards, player2_played_card, player2_discarded_cards,
                 updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                game.game_id,
                game.turn,
                1 if game.is_active else 0,
                current_player_num,
                game.player1.name,
                player1_deck_json,
                player1_hand_json,
                player1_played_json,
                player1_discarded_json,
                game.player2.name,
                player2_deck_json,
                player2_hand_json,
                player2_played_json,
                player2_discarded_json
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
                SELECT game_id, turn, is_active, current_player,
                       player1_name, player1_deck_cards, player1_hand_cards, player1_played_card, player1_discarded_cards,
                       player2_name, player2_deck_cards, player2_hand_cards, player2_played_card, player2_discarded_cards
                FROM games
                WHERE game_id = ?
            """, (game_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            (game_id_db, turn, is_active, current_player_num,
             player1_name, player1_deck_json, player1_hand_json, player1_played_json, player1_discarded_json,
             player2_name, player2_deck_json, player2_hand_json, player2_played_json, player2_discarded_json) = row
            
            # Deserialize player1 deck
            player1_deck_cards = self._deserialize_cards(player1_deck_json)
            player1_deck = Deck(player1_deck_cards)
            player1_deck.shuffled = True
            
            # Deserialize player2 deck
            player2_deck_cards = self._deserialize_cards(player2_deck_json)
            player2_deck = Deck(player2_deck_cards)
            player2_deck.shuffled = True
            
            # Create game
            game = Game(player1_name, player1_deck, player2_name, player2_deck, game_id=game_id_db)
            game.turn = turn
            game.is_active = bool(is_active)
            
            # Set current player
            if current_player_num == 2:
                game.current_player = game.player2
            
            # Deserialize player1 hand if it exists
            if player1_hand_json:
                player1_hand_cards = self._deserialize_cards(player1_hand_json)
                if len(player1_hand_cards) == Hand.HAND_SIZE:
                    game.player1.hand = Hand(player1_hand_cards)
                    
                    if player1_played_json:
                        played_card_dict = json.loads(player1_played_json)
                        game.player1.hand.played_card = self._dict_to_card(played_card_dict)
                        # If card was played, discard the remaining
                        if len(game.player1.hand.cards) > 0:
                            game.player1.hand.discarded_cards = game.player1.hand.cards.copy()
                            game.player1.hand.cards.clear()
                    
                    if player1_discarded_json:
                        game.player1.hand.discarded_cards = self._deserialize_cards(player1_discarded_json)
            
            # Deserialize player2 hand if it exists
            if player2_hand_json:
                player2_hand_cards = self._deserialize_cards(player2_hand_json)
                if len(player2_hand_cards) == Hand.HAND_SIZE:
                    game.player2.hand = Hand(player2_hand_cards)
                    
                    if player2_played_json:
                        played_card_dict = json.loads(player2_played_json)
                        game.player2.hand.played_card = self._dict_to_card(played_card_dict)
                        # If card was played, discard the remaining
                        if len(game.player2.hand.cards) > 0:
                            game.player2.hand.discarded_cards = game.player2.hand.cards.copy()
                            game.player2.hand.cards.clear()
                    
                    if player2_discarded_json:
                        game.player2.hand.discarded_cards = self._deserialize_cards(player2_discarded_json)
            
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

