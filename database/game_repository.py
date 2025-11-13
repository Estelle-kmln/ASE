"""Repository for persisting game state to database.

This module implements the Repository pattern for game persistence, providing
an abstraction layer between the game domain models and the SQLite database.
It handles serialization and deserialization of game objects (cards, decks, hands)
to/from JSON format for storage in the database.

The repository manages a 'games' table that stores complete game state including:
    - Game metadata (ID, turn number, active status, current player)
    - Player information (names, decks, hands, played cards, discarded cards)
    - Timestamps for creation and updates

The module includes automatic database schema migration to handle schema changes
between versions of the application.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from models.card import Card
from models.deck import Deck
from models.game import Game, Hand


class GameRepository:
    """Repository for game persistence.

    This class provides methods to save, load, list, and delete game instances
    from a SQLite database. It handles the conversion between game domain objects
    and their database representation using JSON serialization.

    The repository automatically initializes the database schema on instantiation,
    creating the necessary tables if they don't exist. It also handles schema
    migrations when the database structure changes.

    Attributes:
        db_path (str): Path to the SQLite database file.
    """

    def __init__(self, db_path: str = "game.db"):
        """Initialize the repository.

        Args:
            db_path (str, optional): Path to the SQLite database file.
                                   Defaults to "game.db" in the current directory.
        """
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Create database and tables if they don't exist.

        This method ensures the database schema is properly initialized. It:
        1. Checks if the 'games' table exists
        2. Performs schema migration if the table exists but has an outdated schema
        3. Creates the table with the current schema if it doesn't exist

        The current schema includes:
            - game_id: Unique identifier for the game (primary key)
            - turn: Current turn number
            - is_active: Boolean flag (stored as INTEGER: 0 or 1)
            - current_player: Player number (1 or 2) whose turn it is
            - player1_name, player2_name: Player names
            - player1_deck_cards, player2_deck_cards: JSON-serialized deck cards
            - player1_hand_cards, player2_hand_cards: JSON-serialized hand cards
            - player1_played_card, player2_played_card: JSON-serialized played card
            - player1_discarded_cards, player2_discarded_cards: JSON-serialized discarded cards
            - created_at, updated_at: Timestamps for tracking game lifecycle

        Note:
            The migration logic drops the old table if it lacks the 'current_player'
            column. This will result in data loss for existing games, which is
            acceptable for development but should be handled more carefully in production.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='games'
            """
            )

            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Check if we need to migrate (old schema doesn't have current_player)
                cursor.execute("PRAGMA table_info(games)")
                columns = [row[1] for row in cursor.fetchall()]

                if "current_player" not in columns:
                    # Migrate: drop old table and create new one
                    # Note: This will lose old game data, but that's okay for development
                    cursor.execute("DROP TABLE games")
                    table_exists = False
                else:
                    # Add missing columns if they don't exist
                    if "winner" not in columns:
                        cursor.execute("ALTER TABLE games ADD COLUMN winner TEXT")
                    if "player1_score" not in columns:
                        cursor.execute("ALTER TABLE games ADD COLUMN player1_score INTEGER DEFAULT 0")
                    if "player2_score" not in columns:
                        cursor.execute("ALTER TABLE games ADD COLUMN player2_score INTEGER DEFAULT 0")
                    conn.commit()

            if not table_exists:
                # Games table - updated for 2-player games
                cursor.execute(
                    """
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
                        winner TEXT,
                        player1_score INTEGER DEFAULT 0,
                        player2_score INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

            conn.commit()

    def _card_to_dict(self, card: Card) -> dict:
        """Convert a card to a dictionary.

        Converts a Card domain object into a dictionary representation suitable
        for JSON serialization. The dictionary contains the card's value and suit.

        Args:
            card (Card): The card object to convert.

        Returns:
            dict: Dictionary with 'value' and 'suit' keys containing the card's data.
        """
        return {"value": card.value, "suit": card.suit}

    def _dict_to_card(self, card_dict: dict) -> Card:
        """Convert a dictionary to a card.

        Reconstructs a Card domain object from a dictionary representation.
        This is the inverse operation of _card_to_dict.

        Args:
            card_dict (dict): Dictionary containing 'value' and 'suit' keys.

        Returns:
            Card: A Card object with the specified value and suit.

        Raises:
            KeyError: If the dictionary is missing required keys ('value' or 'suit').
        """
        return Card(card_dict["value"], card_dict["suit"])

    def _serialize_cards(self, cards: list[Card]) -> str:
        """Serialize a list of cards to JSON string.

        Converts a list of Card objects into a JSON string for database storage.
        This method handles the conversion of the entire list by first converting
        each card to a dictionary, then serializing the list to JSON.

        Args:
            cards (list[Card]): List of Card objects to serialize.

        Returns:
            str: JSON string representation of the cards list.
        """
        return json.dumps([self._card_to_dict(card) for card in cards])

    def _deserialize_cards(self, cards_json: str) -> list[Card]:
        """Deserialize a JSON string to a list of cards.

        Reconstructs a list of Card objects from a JSON string stored in the database.
        This is the inverse operation of _serialize_cards. Handles empty or None
        input gracefully by returning an empty list.

        Args:
            cards_json (str): JSON string representation of a list of cards.
                             Can be None or empty string.

        Returns:
            list[Card]: List of Card objects reconstructed from the JSON string.
                       Returns empty list if input is None or empty.

        Raises:
            json.JSONDecodeError: If the JSON string is malformed.
        """
        if not cards_json:
            return []
        cards_data = json.loads(cards_json)
        return [self._dict_to_card(card_dict) for card_dict in cards_data]

    def save_game(self, game: Game, winner: Optional[str] = None):
        """Save a game to the database.

        Persists the complete state of a Game object to the database. This includes:
            - Game metadata (ID, turn number, active status, current player)
            - Both players' names, decks, hands, played cards, and discarded cards
            - Winner name (if game is finished)
            - Timestamp update for tracking modifications

        The method uses INSERT OR REPLACE, so it will update an existing game
        with the same game_id or create a new record if it doesn't exist.

        All card data is serialized to JSON format before storage. Hand data is
        only saved if a hand exists for the player. Played and discarded cards
        are saved separately to preserve the game state accurately.

        Args:
            game (Game): The Game object to persist to the database.
            winner (Optional[str]): Name of the winner if game is finished, None otherwise.

        Note:
            The current_player is stored as an integer (1 for player1, 2 for player2)
            based on which player object matches game.current_player.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Determine current player (1 or 2)
            current_player_num = 1 if game.current_player == game.player1 else 2
            
            # Get scores
            p1s = getattr(game, "player1_score", 0)
            p2s = getattr(game, "player2_score", 0)
            
            # Determine winner if game is not active and winner not provided
            if not game.is_active and winner is None:
                if p1s > p2s:
                    winner = game.player1.name
                elif p2s > p1s:
                    winner = game.player2.name
                # If scores are equal, check remaining cards as tiebreaker
                elif len(game.player1.deck) > len(game.player2.deck):
                    winner = game.player1.name
                elif len(game.player2.deck) > len(game.player1.deck):
                    winner = game.player2.name
                # Otherwise, winner remains None (tie)

            # Serialize player1 data
            player1_deck_json = self._serialize_cards(game.player1.deck.cards)
            player1_hand_json = None
            player1_played_json = None
            player1_discarded_json = None

            if game.player1.hand:
                player1_hand_json = self._serialize_cards(
                    game.player1.hand.cards
                )
                if game.player1.hand.played_card:
                    player1_played_json = json.dumps(
                        self._card_to_dict(game.player1.hand.played_card)
                    )
                if game.player1.hand.discarded_cards:
                    player1_discarded_json = self._serialize_cards(
                        game.player1.hand.discarded_cards
                    )

            # Serialize player2 data
            player2_deck_json = self._serialize_cards(game.player2.deck.cards)
            player2_hand_json = None
            player2_played_json = None
            player2_discarded_json = None

            if game.player2.hand:
                player2_hand_json = self._serialize_cards(
                    game.player2.hand.cards
                )
                if game.player2.hand.played_card:
                    player2_played_json = json.dumps(
                        self._card_to_dict(game.player2.hand.played_card)
                    )
                if game.player2.hand.discarded_cards:
                    player2_discarded_json = self._serialize_cards(
                        game.player2.hand.discarded_cards
                    )

            cursor.execute(
                """
                INSERT OR REPLACE INTO games
                (game_id, turn, is_active, current_player, 
                 player1_name, player1_deck_cards, player1_hand_cards, player1_played_card, player1_discarded_cards,
                 player2_name, player2_deck_cards, player2_hand_cards, player2_played_card, player2_discarded_cards,
                 winner, player1_score, player2_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
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
                    player2_discarded_json,
                    winner,
                    p1s,
                    p2s,
                ),
            )

            conn.commit()

    def load_game(self, game_id: str) -> Optional[Game]:
        """Load a game from the database.

        Reconstructs a Game object from its stored database representation.
        This method performs the inverse operation of save_game, deserializing
        all JSON data back into domain objects (Card, Deck, Hand, Game).

        The method handles:
            - Reconstructing both players' decks from JSON
            - Reconstructing hands if they exist (must be exactly HAND_SIZE cards)
            - Restoring played cards and discarded cards
            - Setting the correct current player based on stored player number
            - Restoring game state (turn number, active status)

        When a card has been played, the remaining hand cards are moved to
        discarded_cards to maintain the correct game state.

        Args:
            game_id (str): The unique identifier of the game to load.

        Returns:
            Optional[Game]: The reconstructed Game object if found, None if
                          no game with the given game_id exists in the database.

        Note:
            Decks are marked as shuffled when loaded, as they should already
            be shuffled when the game was created. Hands are only reconstructed
            if they contain exactly HAND_SIZE (3) cards.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT game_id, turn, is_active, current_player,
                       player1_name, player1_deck_cards, player1_hand_cards, player1_played_card, player1_discarded_cards,
                       player2_name, player2_deck_cards, player2_hand_cards, player2_played_card, player2_discarded_cards
                FROM games
                WHERE game_id = ?
            """,
                (game_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            (
                game_id_db,
                turn,
                is_active,
                current_player_num,
                player1_name,
                player1_deck_json,
                player1_hand_json,
                player1_played_json,
                player1_discarded_json,
                player2_name,
                player2_deck_json,
                player2_hand_json,
                player2_played_json,
                player2_discarded_json,
            ) = row

            # Deserialize player1 deck
            player1_deck_cards = self._deserialize_cards(player1_deck_json)
            player1_deck = Deck(player1_deck_cards)
            player1_deck.shuffled = True

            # Deserialize player2 deck
            player2_deck_cards = self._deserialize_cards(player2_deck_json)
            player2_deck = Deck(player2_deck_cards)
            player2_deck.shuffled = True

            # Create game
            game = Game(
                player1_name,
                player1_deck,
                player2_name,
                player2_deck,
                game_id=game_id_db,
            )
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
                        game.player1.hand.played_card = self._dict_to_card(
                            played_card_dict
                        )
                        # If card was played, discard the remaining
                        if len(game.player1.hand.cards) > 0:
                            game.player1.hand.discarded_cards = (
                                game.player1.hand.cards.copy()
                            )
                            game.player1.hand.cards.clear()

                    if player1_discarded_json:
                        game.player1.hand.discarded_cards = (
                            self._deserialize_cards(player1_discarded_json)
                        )

            # Deserialize player2 hand if it exists
            if player2_hand_json:
                player2_hand_cards = self._deserialize_cards(player2_hand_json)
                if len(player2_hand_cards) == Hand.HAND_SIZE:
                    game.player2.hand = Hand(player2_hand_cards)

                    if player2_played_json:
                        played_card_dict = json.loads(player2_played_json)
                        game.player2.hand.played_card = self._dict_to_card(
                            played_card_dict
                        )
                        # If card was played, discard the remaining
                        if len(game.player2.hand.cards) > 0:
                            game.player2.hand.discarded_cards = (
                                game.player2.hand.cards.copy()
                            )
                            game.player2.hand.cards.clear()

                    if player2_discarded_json:
                        game.player2.hand.discarded_cards = (
                            self._deserialize_cards(player2_discarded_json)
                        )

            return game

    def list_games(self, active_only: bool = False) -> list[dict]:
        """List all games.

        Retrieves a list of all games stored in the database, optionally filtered
        to only include active games. Returns summary information for each game
        without loading the full game state, making it efficient for listing
        purposes.

        Args:
            active_only (bool, optional): If True, only return games where
                                         is_active is True. Defaults to False.

        Returns:
            list[dict]: List of dictionaries, each containing:
                - game_id (str): Unique game identifier
                - turn (int): Current turn number
                - is_active (bool): Whether the game is currently active
                - created_at (str): Timestamp when the game was created

            Games are ordered by creation time, most recent first.
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
                    "created_at": row[3],
                }
                for row in rows
            ]

    def delete_game(self, game_id: str) -> bool:
        """Delete a game from the database.

        Removes a game record from the database. This operation is permanent
        and cannot be undone. All game state associated with the game_id will
        be lost.

        Args:
            game_id (str): The unique identifier of the game to delete.

        Returns:
            bool: True if a game was found and deleted (rowcount > 0),
                 False if no game with the given game_id exists.

        Note:
            The method uses cursor.rowcount to determine if a deletion occurred.
            If the game_id doesn't exist, rowcount will be 0 and the method
            returns False.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
            conn.commit()

            return cursor.rowcount > 0

    def get_leaderboard(self) -> list[dict]:
        """Get leaderboard statistics for all players.

        Calculates win/loss/tie statistics for each player based on completed games.
        Only includes games where is_active = 0 (finished games).

        Returns:
            list[dict]: List of dictionaries, each containing:
                - player_name (str): Name of the player
                - wins (int): Number of games won
                - losses (int): Number of games lost
                - ties (int): Number of games tied
                - total_games (int): Total number of games played
                - win_rate (float): Win rate as a percentage (0-100)

            Players are sorted by wins (descending), then by win_rate (descending).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all completed games (is_active = 0)
            cursor.execute("""
                SELECT player1_name, player2_name, winner
                FROM games
                WHERE is_active = 0
            """)

            rows = cursor.fetchall()

            # Aggregate statistics per player
            stats = {}
            for player1_name, player2_name, winner in rows:
                # Initialize stats for both players if not exists
                if player1_name not in stats:
                    stats[player1_name] = {"wins": 0, "losses": 0, "ties": 0, "total_games": 0}
                if player2_name not in stats:
                    stats[player2_name] = {"wins": 0, "losses": 0, "ties": 0, "total_games": 0}

                # Update statistics
                stats[player1_name]["total_games"] += 1
                stats[player2_name]["total_games"] += 1

                if winner == player1_name:
                    stats[player1_name]["wins"] += 1
                    stats[player2_name]["losses"] += 1
                elif winner == player2_name:
                    stats[player2_name]["wins"] += 1
                    stats[player1_name]["losses"] += 1
                else:
                    # Tie (winner is None or empty)
                    stats[player1_name]["ties"] += 1
                    stats[player2_name]["ties"] += 1

            # Convert to list and calculate win rates
            leaderboard = []
            for player_name, player_stats in stats.items():
                total = player_stats["total_games"]
                wins = player_stats["wins"]
                win_rate = (wins / total * 100) if total > 0 else 0.0

                leaderboard.append({
                    "player_name": player_name,
                    "wins": wins,
                    "losses": player_stats["losses"],
                    "ties": player_stats["ties"],
                    "total_games": total,
                    "win_rate": round(win_rate, 1)
                })

            # Sort by wins (descending), then by win_rate (descending)
            leaderboard.sort(key=lambda x: (x["wins"], x["win_rate"]), reverse=True)

            return leaderboard
