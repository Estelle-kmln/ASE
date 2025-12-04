"""
Game Service - Game logic and state management microservice
"""

import os
import sys
import json
import uuid
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from common.db_manager import unit_of_work, db_health
from dotenv import load_dotenv
import requests

from security import get_history_security

# Add utils directory to path for input sanitizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_sanitizer import InputSanitizer, SecurityMiddleware, require_sanitized_input

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-change-in-production"
)

# Initialize extensions
jwt = JWTManager(app)
CORS(app)
security = SecurityMiddleware(app)

# JWT error handlers - convert 422 to 401 for invalid tokens
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    """Handle invalid token errors."""
    return jsonify({"error": "Invalid token"}), 401


@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    """Handle missing token errors."""
    return jsonify({"error": "Missing authorization header"}), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token errors."""
    return jsonify({"error": "Token has expired"}), 401


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gameuser:gamepassword@localhost:5432/battlecards",
)
CARD_SERVICE_URL = os.getenv("CARD_SERVICE_URL", "http://localhost:5002")


class Card:
    """Card class for game logic."""

    def __init__(self, card_type, power):
        self.type = card_type
        self.power = power

    def to_dict(self):
        return {"type": self.type, "power": self.power}

    def beats(self, other):
        """Check if this card beats another card."""
        winning_combinations = {
            "Rock": "Scissors",
            "Paper": "Rock",
            "Scissors": "Paper",
        }
        return winning_combinations.get(self.type) == other.type

    def ties_with(self, other):
        """Check if this card ties with another card (same type and same power)."""
        return self.type == other.type and self.power == other.power


def get_cards_from_service(token):
    """Get cards from card service."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{CARD_SERVICE_URL}/api/cards/random-deck",
            headers=headers,
            json={"size": 22},
        )
        if response.status_code == 200:
            return response.json()["deck"]
        return None
    except:
        return None


def check_auto_resolve_conditions(game):
    """Check if round should be automatically resolved."""
    try:
        player1_played = json.loads(game["player1_played_card"] or "null")
        player2_played = json.loads(game["player2_played_card"] or "null")
        return player1_played is not None and player2_played is not None
    except:
        return False


def get_game_end_status(p1_deck, p2_deck, p1_score, p2_score):
    """Determine game end status and winner."""
    # Check if either player has less than 3 cards (cannot draw another hand)
    p1_can_continue = len(p1_deck) >= 3
    p2_can_continue = len(p2_deck) >= 3

    game_should_end = not p1_can_continue or not p2_can_continue

    if not game_should_end:
        return False, None, False, False

    # Game is ending - determine winner
    if p1_score > p2_score:
        return True, "player1", False, False
    elif p2_score > p1_score:
        return True, "player2", False, False
    else:
        # It's a tie - check if tie-breaker is possible
        p1_has_cards = len(p1_deck) > 0
        p2_has_cards = len(p2_deck) > 0
        tie_breaker_possible = p1_has_cards and p2_has_cards
        return True, None, True, tie_breaker_possible


HISTORY_LOCK_MESSAGE = "Game history is archived and cannot be modified"
HISTORY_TAMPER_MESSAGE = "Stored match history failed integrity verification"


def is_game_archived(game_id):
    """Return True if the immutable history already exists for a game."""
    with unit_of_work() as cur:
        cur.execute("SELECT 1 FROM game_history WHERE game_id = %s", (game_id,))
        return cur.fetchone() is not None


def build_history_snapshot(
    game, player1_score, player2_score, winner_name, p1_deck, p2_deck
):
    """Prepare the payload that gets encrypted for long-term storage."""
    return {
        "game_id": game["game_id"],
        "turns_played": game["turn"],
        "player1": {
            "name": game["player1_name"],
            "score": player1_score,
            "remaining_deck": p1_deck,
        },
        "player2": {
            "name": game["player2_name"],
            "score": player2_score,
            "remaining_deck": p2_deck,
        },
        "winner": winner_name,
        "was_tie": player1_score == player2_score,
        "created_at": (
            game["created_at"].isoformat() if game.get("created_at") else None
        ),
        "archived_at": datetime.utcnow().isoformat(),
    }


def archive_game_history(game, player1_score, player2_score, winner_name, p1_deck, p2_deck):
    """Encrypt and persist the final state for a completed game."""
    security = get_history_security()
    snapshot = build_history_snapshot(
        game, player1_score, player2_score, winner_name, p1_deck, p2_deck
    )
    encrypted_payload, integrity_hash = security.encrypt_snapshot(snapshot)
    # encrypted_payload is bytes-like

    with unit_of_work() as cur:
        cur.execute(
            """
            INSERT INTO game_history (
                game_id, player1_name, player2_name, player1_score, player2_score,
                winner, encrypted_payload, integrity_hash
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id) DO NOTHING
            """,
            (
                game["game_id"],
                game["player1_name"],
                game["player2_name"],
                player1_score,
                player2_score,
                winner_name,
                encrypted_payload,
                integrity_hash,
            ),
        )


def _raw_payload_to_bytes(raw_payload):
    """Normalize the DB-stored encrypted payload to bytes."""
    if isinstance(raw_payload, memoryview):
        return raw_payload.tobytes()
    if isinstance(raw_payload, bytearray):
        return bytes(raw_payload)
    return raw_payload


def decrypt_history_row(row):
    """Return decrypted snapshot for a history row or raise ValueError on tampering."""
    security = get_history_security()
    encrypted_payload = _raw_payload_to_bytes(row["encrypted_payload"])
    if not security.verify_snapshot(encrypted_payload, row["integrity_hash"]):
        raise ValueError(HISTORY_TAMPER_MESSAGE)
    return security.decrypt_snapshot(encrypted_payload)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "game-service"}), 200


@app.route("/api/games", methods=["POST"])
@jwt_required()
@require_sanitized_input({'player2_name': 'username'})
def create_game():
    """Create a new game."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data or not data.get("player2_name"):
            return jsonify({"error": "Player 2 name is required"}), 400

        # Sanitize player names
        try:
            player1_name = InputSanitizer.validate_username(current_user)
            player2_name = InputSanitizer.validate_username(data["player2_name"])
        except ValueError as e:
            return jsonify({'error': f'Invalid player name: {str(e)}'}), 400
        
        # Prevent self-play
        if player1_name == player2_name:
            return jsonify({'error': 'Cannot create game with yourself'}), 400

        # Get JWT token from request
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        # Get random decks from card service
        player1_deck = get_cards_from_service(token)
        player2_deck = get_cards_from_service(token)

        if not player1_deck or not player2_deck:
            return jsonify({"error": "Failed to create decks"}), 500

        # Create game
        game_id = str(uuid.uuid4())

        with unit_of_work() as cur:
            cur.execute(
                """
                INSERT INTO games (
                    game_id, turn, is_active,
                    player1_name, player1_deck_cards, player1_hand_cards, 
                    player1_score, player2_name, player2_deck_cards, 
                    player2_hand_cards, player2_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    game_id,
                    1,
                    True,
                    player1_name,
                    json.dumps(player1_deck),
                    json.dumps([]),
                    0,
                    player2_name,
                    json.dumps(player2_deck),
                    json.dumps([]),
                    0,
                ),
            )

        return (
            jsonify(
                {
                    "game_id": game_id,
                    "player1_name": player1_name,
                    "player2_name": player2_name,
                    "status": "created",
                    "turn": 1,
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to create game: {str(e)}"}), 500


@app.route("/api/games/<game_id>", methods=["GET"])
@jwt_required()
def get_game(game_id):
    """Get game state."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

        with unit_of_work() as cur:
            cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
            game = cur.fetchone()


        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Check if user is a player in this game
        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized to view this game"}), 403

        # Parse JSON fields
        try:
            player1_deck = json.loads(game["player1_deck_cards"] or "[]")
            player1_hand = json.loads(game["player1_hand_cards"] or "[]")
            player2_deck = json.loads(game["player2_deck_cards"] or "[]")
            player2_hand = json.loads(game["player2_hand_cards"] or "[]")
        except:
            player1_deck = player1_hand = player2_deck = player2_hand = []

        return (
            jsonify(
                {
                    "game_id": game["game_id"],
                    "turn": game["turn"],
                    "is_active": game["is_active"],
                    "player1": {
                        "name": game["player1_name"],
                        "deck_size": len(player1_deck),
                        "hand_size": len(player1_hand),
                        "score": game["player1_score"],
                    },
                    "player2": {
                        "name": game["player2_name"],
                        "deck_size": len(player2_deck),
                        "hand_size": len(player2_hand),
                        "score": game["player2_score"],
                    },
                    "winner": game["winner"],
                    "created_at": (
                        game["created_at"].isoformat()
                        if game["created_at"]
                        else None
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get game: {str(e)}"}), 500


@app.route("/api/games/<game_id>/history", methods=["GET"])
@jwt_required()
def get_game_history(game_id):
    """Return the immutable, decrypted history for a completed game."""
    try:
        current_user = get_jwt_identity()

        with unit_of_work() as cur:
            cur.execute(
                """
                SELECT 
                    game_id,
                    player1_name,
                    player2_name,
                    player1_score,
                    player2_score,
                    winner,
                    archived_at,
                    encrypted_payload,
                    integrity_hash
                FROM game_history
                WHERE game_id = %s
                """,
                (game_id,),
            )
            history = cur.fetchone()

        if not history:
            return jsonify({"error": "History not found"}), 404

        if current_user not in [
            history["player1_name"],
            history["player2_name"],
        ]:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            snapshot = decrypt_history_row(history)
        except ValueError:
            return jsonify({"error": HISTORY_TAMPER_MESSAGE}), 409

        return (
            jsonify(
                {
                    "game_id": history["game_id"],
                    "player1_name": history["player1_name"],
                    "player2_name": history["player2_name"],
                    "player1_score": history["player1_score"],
                    "player2_score": history["player2_score"],
                    "winner": history["winner"],
                    "archived_at": (
                        history["archived_at"].isoformat()
                        if history["archived_at"]
                        else None
                    ),
                    "snapshot": snapshot,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get game history: {str(e)}"}), 500


@app.route("/api/games/<game_id>/hand", methods=["GET"])
@jwt_required()
def get_player_hand(game_id):
    """Get current player's hand."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

        with unit_of_work() as cur:
            cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
            game = cur.fetchone()

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Check if user is a player in this game
        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized to view this game"}), 403

        # Determine which player's hand to return
        if current_user == game["player1_name"]:
            hand_data = game["player1_hand_cards"]
        else:
            hand_data = game["player2_hand_cards"]

        try:
            hand = json.loads(hand_data or "[]")
        except:
            hand = []

        return jsonify({"hand": hand, "player": current_user}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get hand: {str(e)}"}), 500


@app.route("/api/games/<game_id>/draw-hand", methods=["POST"])
@jwt_required()
def draw_hand(game_id):
    """Draw a new hand for the current player."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

# Use centralized transaction manager instead of direct DB access 

        # Fetch game state using database manager
        with unit_of_work() as cur:
            cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
            game = cur.fetchone()

        if not game:
            return jsonify({"error": "Game not found"}), 404

        if is_game_archived(game["game_id"]):
            return jsonify({"error": HISTORY_LOCK_MESSAGE}), 409

        if not game["is_active"]:
            return jsonify({"error": "Game is not active"}), 400

        # Determine player
        is_player1 = current_user == game["player1_name"]
        if not is_player1 and current_user != game["player2_name"]:
            
            return jsonify({"error": "Unauthorized to play this game"}), 403

        # Parse deck
        deck_field = (
            "player1_deck_cards" if is_player1 else "player2_deck_cards"
        )
        hand_field = (
            "player1_hand_cards" if is_player1 else "player2_hand_cards"
        )

        try:
            deck = json.loads(game[deck_field] or "[]")
        except:
            deck = []

        # Check for endgame scenarios
        if len(deck) == 0:
            return jsonify({"error": "No cards left in deck"}), 400

        # For normal gameplay, require 3 cards. For endgame, allow fewer.
        if len(deck) < 3:
            # Final hand scenario - take all remaining cards
            hand = deck.copy()
            remaining_deck = []
        else:
            # Normal hand - draw 3 cards randomly
            hand = random.sample(deck, 3)
            remaining_deck = [card for card in deck if card not in hand]

        # Update database
    
        with unit_of_work() as cur:
            if is_player1:
                cur.execute(
                    """
                    UPDATE games
                    SET player1_deck_cards = %s,
                        player1_hand_cards = %s
                    WHERE game_id = %s
                    """,
                    (json.dumps(remaining_deck), json.dumps(hand), game_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE games
                    SET player2_deck_cards = %s,
                        player2_hand_cards = %s
                    WHERE game_id = %s
                    """,
                    (json.dumps(remaining_deck), json.dumps(hand), game_id),
                )

        return (
            jsonify(
                {
                    "hand": hand,
                    "deck_size": len(remaining_deck),
                    "is_final_hand": len(remaining_deck) == 0,
                    "cards_drawn": len(hand),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to draw hand: {str(e)}"}), 500


@app.route("/api/games/<game_id>/play-card", methods=["POST"])
@jwt_required()
@require_sanitized_input({'card_index': 'int'})
def play_card(game_id):
    """Play a card from hand."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data or "card_index" not in data:
            return jsonify({"error": "Card index is required"}), 400

        # Validate card index
        try:
            card_index = InputSanitizer.validate_integer(data["card_index"], min_val=0, max_val=20)
        except ValueError as e:
            return jsonify({'error': f'Invalid card index: {str(e)}'}), 400

        with unit_of_work() as cur:
                cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
                game = cur.fetchone()

        if not game:
            return jsonify({"error": "Game not found"}), 404

        if is_game_archived(game["game_id"]):
            return jsonify({"error": HISTORY_LOCK_MESSAGE}), 409

        if not game["is_active"]:
            return jsonify({"error": "Game is not active"}), 400

        # Determine player
        is_player1 = current_user == game["player1_name"]
        if not is_player1 and current_user != game["player2_name"]:
            return jsonify({"error": "Unauthorized to play this game"}), 403

        # Parse hand
        hand_field = (
            "player1_hand_cards" if is_player1 else "player2_hand_cards"
        )
        played_field = (
            "player1_played_card" if is_player1 else "player2_played_card"
        )

        try:
            hand = json.loads(game[hand_field] or "[]")
        except:
            hand = []

        if not hand or card_index < 0 or card_index >= len(hand):
            return jsonify({"error": "Invalid card index"}), 400

        # Play the card
        played_card = hand[card_index]
        remaining_hand = [
            card for i, card in enumerate(hand) if i != card_index
        ]

        # Update database
        with unit_of_work() as cur:
            if is_player1:
                cur.execute(
                    """
                    UPDATE games
                    SET player1_hand_cards = %s,
                        player1_played_card = %s
                    WHERE game_id = %s
                    """,
                    (json.dumps(remaining_hand), json.dumps(played_card), game_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE games
                    SET player2_hand_cards = %s,
                        player2_played_card = %s
                    WHERE game_id = %s
                    """,
                    (json.dumps(remaining_hand), json.dumps(played_card), game_id),
                )

        # Refresh game state to check if both players have played
        with unit_of_work() as cur:
            cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
            updated_game = cur.fetchone()

        both_played = check_auto_resolve_conditions(updated_game)

        # Check if we should auto-resolve the round
        auto_resolve_result = None

        # Both players have played - automatically resolve the round
        if both_played:
            auto_resolve_result = auto_resolve_round(updated_game)

        response = {
            "played_card": played_card,
            "remaining_hand": remaining_hand,
            "both_played": both_played,
        }

        if auto_resolve_result:
            response["round_resolved"] = True
            response["round_result"] = auto_resolve_result

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Failed to play card: {str(e)}"}), 500


def auto_resolve_round(game):
    """Automatically resolve a round when both players have played cards."""
    try:
        # Parse played cards
        try:
            player1_card_data = json.loads(
                game["player1_played_card"] or "null"
            )
            player2_card_data = json.loads(
                game["player2_played_card"] or "null"
            )
        except:
            return None

        if not player1_card_data or not player2_card_data:
            return None

        # Create card objects
        player1_card = Card(
            player1_card_data["type"], player1_card_data["power"]
        )
        player2_card = Card(
            player2_card_data["type"], player2_card_data["power"]
        )

        # Determine round winner
        round_winner = None
        round_tied = False

        if player1_card.ties_with(player2_card):
            # Perfect tie - same type and power
            round_tied = True
        elif player1_card.beats(player2_card):
            round_winner = 1
        elif player2_card.beats(player1_card):
            round_winner = 2
        else:
            # Same type, different power
            if player1_card.power > player2_card.power:
                round_winner = 1
            elif player2_card.power > player1_card.power:
                round_winner = 2
            else:
                round_tied = True  # Shouldn't happen but safety check

        # Update scores (ties don't add points)
        new_p1_score = game["player1_score"]
        new_p2_score = game["player2_score"]

        if round_winner == 1:
            new_p1_score += 1
        elif round_winner == 2:
            new_p2_score += 1

        # Check game end conditions
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        game_over, winner, is_tie, tie_breaker_possible = get_game_end_status(
            p1_deck, p2_deck, new_p1_score, new_p2_score
        )

        # Prepare winner name if game is over
        winner_name = None
        if game_over and winner:
            if winner == "player1":
                winner_name = game["player1_name"]
            elif winner == "player2":
                winner_name = game["player2_name"]

        # Update database
        with unit_of_work() as cur:
            cur.execute(
                """
                UPDATE games
                SET player1_score = %s,
                    player2_score = %s,
                    player1_played_card = NULL,
                    player2_played_card = NULL,
                    player1_hand_cards = '[]',
                    player2_hand_cards = '[]',
                    is_active = %s,
                    winner = %s,
                    turn = turn + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE game_id = %s
                """,
                (
                    new_p1_score,
                    new_p2_score,
                    not game_over,
                    winner_name,
                    game["game_id"],
                ),
            )

        if game_over:
            archive_game_history(
                game,
                new_p1_score,
                new_p2_score,
                winner_name,
                p1_deck,
                p2_deck,
            )

        return {
            "round_winner": round_winner,
            "round_tied": round_tied,
            "player1_card": player1_card_data,
            "player2_card": player2_card_data,
            "player1_score": new_p1_score,
            "player2_score": new_p2_score,
            "game_over": game_over,
            "winner": winner_name,
            "is_tie": is_tie,
            "tie_breaker_possible": tie_breaker_possible,
        }
    except Exception as e:
        return None


@app.route("/api/games/<game_id>/resolve-round", methods=["POST"])
@jwt_required()
def resolve_round(game_id):
    """Resolve a round after both players have played cards."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({"error": "Game not found"}), 404

        if is_game_archived(conn, game["game_id"]):
            conn.close()
            return jsonify({"error": HISTORY_LOCK_MESSAGE}), 409

        if not game["is_active"]:
            conn.close()
            return jsonify({"error": "Game is not active"}), 400

        # Check if user is a player
        if current_user not in [game["player1_name"], game["player2_name"]]:
            conn.close()
            return jsonify({"error": "Unauthorized"}), 403

        # Parse played cards
        try:
            player1_card_data = json.loads(
                game["player1_played_card"] or "null"
            )
            player2_card_data = json.loads(
                game["player2_played_card"] or "null"
            )
        except:
            player1_card_data = player2_card_data = None

        if not player1_card_data or not player2_card_data:
            conn.close()
            return (
                jsonify(
                    {"error": "Both players must play cards before resolving"}
                ),
                400,
            )

        # Create card objects
        player1_card = Card(
            player1_card_data["type"], player1_card_data["power"]
        )
        player2_card = Card(
            player2_card_data["type"], player2_card_data["power"]
        )

        # Determine round winner
        round_winner = None
        round_tied = False

        if player1_card.ties_with(player2_card):
            # Perfect tie - same type and power
            round_tied = True
        elif player1_card.beats(player2_card):
            round_winner = 1
        elif player2_card.beats(player1_card):
            round_winner = 2
        else:
            # Same type, different power
            if player1_card.power > player2_card.power:
                round_winner = 1
            elif player2_card.power > player1_card.power:
                round_winner = 2
            else:
                round_tied = True  # Shouldn't happen but safety check

        # Update scores (ties don't add points)
        new_p1_score = game["player1_score"]
        new_p2_score = game["player2_score"]

        if round_winner == 1:
            new_p1_score += 1
        elif round_winner == 2:
            new_p2_score += 1

        # Check game end conditions
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        game_over, winner, is_tie, tie_breaker_possible = get_game_end_status(
            p1_deck, p2_deck, new_p1_score, new_p2_score
        )

        # Prepare winner name if game is over
        winner_name = None
        if game_over and winner:
            if winner == "player1":
                winner_name = game["player1_name"]
            elif winner == "player2":
                winner_name = game["player2_name"]

        # Update database
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE games 
            SET player1_score = %s, player2_score = %s, 
                player1_played_card = NULL, player2_played_card = NULL,
                player1_hand_cards = '[]', player2_hand_cards = '[]',
                is_active = %s, winner = %s, turn = turn + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE game_id = %s
        """,
            (new_p1_score, new_p2_score, not game_over, winner_name, game_id),
        )

        if game_over:
            archive_game_history(
                conn,
                game,
                new_p1_score,
                new_p2_score,
                winner_name,
                p1_deck,
                p2_deck,
            )

        conn.commit()
        conn.close()

        return (
            jsonify(
                {
                    "round_winner": round_winner,
                    "round_tied": round_tied,
                    "player1_card": player1_card_data,
                    "player2_card": player2_card_data,
                    "player1_score": new_p1_score,
                    "player2_score": new_p2_score,
                    "game_over": game_over,
                    "winner": winner_name,
                    "is_tie": is_tie,
                    "tie_breaker_possible": tie_breaker_possible,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to resolve round: {str(e)}"}), 500


@app.route("/api/games/<game_id>/tie-breaker-status", methods=["GET"])
@jwt_required()
def check_tie_breaker_status(game_id):
    """Check if tie-breaker round is possible."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

        with unit_of_work() as cur:
            cur.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
            game = cur.fetchone()

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Check if user is a player
        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        # Parse decks
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        is_tied_game = (
            not game["is_active"]
            and game["winner"] is None
            and game["player1_score"] == game["player2_score"]
        )

        tie_breaker_possible = (
            is_tied_game and len(p1_deck) > 0 and len(p2_deck) > 0
        )

        return (
            jsonify(
                {
                    "is_tied_game": is_tied_game,
                    "tie_breaker_possible": tie_breaker_possible,
                    "player1_remaining_cards": len(p1_deck),
                    "player2_remaining_cards": len(p2_deck),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Failed to check tie-breaker status: {str(e)}"}),
            500,
        )


@app.route("/api/games/<game_id>/tie-breaker", methods=["POST"])
@jwt_required()
def tie_breaker_round(game_id):
    """Play a tie-breaker round using remaining cards when game ends in tie."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({"error": "Game not found"}), 404

        # Check if user is a player
        if current_user not in [game["player1_name"], game["player2_name"]]:
            conn.close()
            return jsonify({"error": "Unauthorized"}), 403

        # Verify game ended in a tie
        if game["is_active"] or game["winner"] is not None:
            conn.close()
            return jsonify({"error": "Game is not in a tie state"}), 400

        if game["player1_score"] != game["player2_score"]:
            conn.close()
            return jsonify({"error": "Game did not end in a tie"}), 400

        # Parse decks to get remaining cards
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        if len(p1_deck) == 0 or len(p2_deck) == 0:
            conn.close()
            return jsonify({"error": "No cards available for tie-breaker"}), 400

        # Each player draws one card for tie-breaker
        p1_card = random.choice(p1_deck)
        p2_card = random.choice(p2_deck)

        # Create card objects for comparison
        player1_card = Card(p1_card["type"], p1_card["power"])
        player2_card = Card(p2_card["type"], p2_card["power"])

        # Determine tie-breaker winner
        tie_breaker_winner = None
        tie_breaker_tied = False

        if player1_card.ties_with(player2_card):
            tie_breaker_tied = True
        elif player1_card.beats(player2_card):
            tie_breaker_winner = game["player1_name"]
        elif player2_card.beats(player1_card):
            tie_breaker_winner = game["player2_name"]
        else:
            # Same type, different power
            if player1_card.power > player2_card.power:
                tie_breaker_winner = game["player1_name"]
            elif player2_card.power > player1_card.power:
                tie_breaker_winner = game["player2_name"]
            else:
                tie_breaker_tied = True

        # Update game state
        cursor = conn.cursor()
        if tie_breaker_tied:
            # Still tied after tie-breaker - game remains in tie state
            cursor.execute(
                """
                UPDATE games 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE game_id = %s
            """,
                (game_id,),
            )
        else:
            # Tie-breaker resolved - set winner
            cursor.execute(
                """
                UPDATE games 
                SET winner = %s, updated_at = CURRENT_TIMESTAMP
                WHERE game_id = %s
            """,
                (tie_breaker_winner, game_id),
            )

        if not tie_breaker_tied:
            archive_game_history(
                conn,
                game,
                game["player1_score"],
                game["player2_score"],
                tie_breaker_winner,
                p1_deck,
                p2_deck,
            )

        conn.commit()
        conn.close()

        return (
            jsonify(
                {
                    "tie_breaker_winner": tie_breaker_winner,
                    "tie_breaker_tied": tie_breaker_tied,
                    "player1_card": p1_card,
                    "player2_card": p2_card,
                    "final_winner": (
                        tie_breaker_winner if not tie_breaker_tied else None
                    ),
                    "still_tied": tie_breaker_tied,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Failed to resolve tie-breaker: {str(e)}"}),
            500,
        )


@app.route("/api/games/<game_id>/end", methods=["POST"])
@jwt_required()
def end_game(game_id):
    """End a game."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()

        if not game:
            conn.close()
            return jsonify({"error": "Game not found"}), 404

        # Check if user is a player
        if current_user not in [game["player1_name"], game["player2_name"]]:
            conn.close()
            return jsonify({"error": "Unauthorized"}), 403

        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except (json.JSONDecodeError, TypeError):
            p1_deck = p2_deck = []

        # End the game
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE games 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP 
            WHERE game_id = %s
        """,
            (game_id,),
        )

        archive_game_history(
            conn,
            game,
            game["player1_score"],
            game["player2_score"],
            game["winner"],
            p1_deck,
            p2_deck,
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Game ended successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to end game: {str(e)}"}), 500


@app.route("/api/games/user/<username>", methods=["GET"])
@jwt_required()
def get_user_games(username):
    """Get all games for a user."""
    try:
        # Validate username format
        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({'error': f'Invalid username: {str(e)}'}), 400
            
        current_user = get_jwt_identity()
        include_history = (
            request.args.get("include_history", "false").lower() == "true"
        )

        # Users can only view their own games
        if current_user != username:
            return jsonify({"error": "Unauthorized"}), 403

        conn = get_db_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT game_id, turn, is_active, player1_name, player2_name, 
                       player1_score, player2_score, winner, created_at
                FROM games 
                WHERE player1_name = %s OR player2_name = %s 
                ORDER BY created_at DESC
            """,
                (username, username),
            )

            games = cursor.fetchall()

            history_payloads = {}
            tampered_game_ids = set()
            if include_history and games:
                history_cursor = conn.cursor(cursor_factory=RealDictCursor)
                try:
                    game_ids = [game["game_id"] for game in games]
                    history_cursor.execute(
                        """
                        SELECT 
                            game_id,
                            archived_at,
                            encrypted_payload,
                            integrity_hash,
                            player1_score,
                            player2_score,
                            winner
                        FROM game_history
                        WHERE game_id = ANY(%s)
                    """,
                        (game_ids,),
                    )
                    history_rows = history_cursor.fetchall()
                    for history_row in history_rows:
                        try:
                            snapshot = decrypt_history_row(history_row)
                        except ValueError:
                            tampered_game_ids.add(history_row["game_id"])
                            continue

                        history_payloads[history_row["game_id"]] = {
                            "archived_at": (
                                history_row["archived_at"].isoformat()
                                if history_row["archived_at"]
                                else None
                            ),
                            "player1_score": history_row["player1_score"],
                            "player2_score": history_row["player2_score"],
                            "winner": history_row["winner"],
                            "snapshot": snapshot,
                        }
                finally:
                    history_cursor.close()

            game_list = []
            for game in games:
                game_list.append(
                    {
                        "game_id": game["game_id"],
                        "turn": game["turn"],
                        "is_active": game["is_active"],
                        "player1_name": game["player1_name"],
                        "player2_name": game["player2_name"],
                        "player1_score": game["player1_score"],
                        "player2_score": game["player2_score"],
                        "winner": game["winner"],
                        "created_at": (
                            game["created_at"].isoformat()
                            if game["created_at"]
                            else None
                        ),
                    }
                )
                if include_history:
                    history = history_payloads.get(game["game_id"])
                    if history:
                        game_list[-1]["history"] = history
                    elif game["game_id"] in tampered_game_ids:
                        game_list[-1]["history_error"] = HISTORY_TAMPER_MESSAGE

            return jsonify({"games": game_list}), 200

        finally:
            conn.close()

    except Exception as e:
        return jsonify({"error": f"Failed to get user games: {str(e)}"}), 500


@app.route("/api/games/<game_id>/turn-info", methods=["GET"])
@jwt_required()
def get_turn_info(game_id):
    """Get detailed turn information including who needs to act next."""
    try:
        # Basic input sanitization - check for dangerous patterns but allow invalid UUIDs for proper 404s
        game_id = InputSanitizer.sanitize_string(game_id, max_length=100, allow_special=False)
            
        current_user = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM games WHERE game_id = %s", (game_id,))
        game = cursor.fetchone()
        conn.close()

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Check if user is a player
        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        # Parse game state
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
            p1_hand = json.loads(game["player1_hand_cards"] or "[]")
            p2_hand = json.loads(game["player2_hand_cards"] or "[]")
            p1_played = json.loads(game["player1_played_card"] or "null")
            p2_played = json.loads(game["player2_played_card"] or "null")
        except:
            return jsonify({"error": "Failed to parse game state"}), 500

        # Determine current state and next actions needed
        both_need_to_draw = len(p1_hand) == 0 and len(p2_hand) == 0
        p1_needs_to_draw = len(p1_hand) == 0 and len(p1_deck) >= 3
        p2_needs_to_draw = len(p2_hand) == 0 and len(p2_deck) >= 3
        p1_needs_to_play = len(p1_hand) > 0 and p1_played is None
        p2_needs_to_play = len(p2_hand) > 0 and p2_played is None
        both_played = p1_played is not None and p2_played is not None

        return (
            jsonify(
                {
                    "game_id": game_id,
                    "turn": game["turn"],
                    "is_active": game["is_active"],
                    "current_user": current_user,
                    "player1_name": game["player1_name"],
                    "player2_name": game["player2_name"],
                    "turn_status": {
                        "both_need_to_draw": both_need_to_draw,
                        "p1_needs_to_draw": p1_needs_to_draw,
                        "p2_needs_to_draw": p2_needs_to_draw,
                        "p1_needs_to_play": p1_needs_to_play,
                        "p2_needs_to_play": p2_needs_to_play,
                        "both_played": both_played,
                        "ready_to_resolve": both_played,
                    },
                    "deck_status": {
                        "p1_deck_size": len(p1_deck),
                        "p2_deck_size": len(p2_deck),
                        "p1_hand_size": len(p1_hand),
                        "p2_hand_size": len(p2_hand),
                    },
                    "scores": {
                        "player1_score": game["player1_score"],
                        "player2_score": game["player2_score"],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get turn info: {str(e)}"}), 500


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host="0.0.0.0", port=5003, debug=debug_mode)
