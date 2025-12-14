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
import requests
from dotenv import load_dotenv

from security import get_history_security

# Add utils directory to path for input sanitizer
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
from input_sanitizer import (
    InputSanitizer,
    SecurityMiddleware,
    require_sanitized_input,
)

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

# Service URLs
DB_MANAGER_URL = os.getenv("DB_MANAGER_URL", "http://db-manager:5005")
CARD_SERVICE_URL = os.getenv("CARD_SERVICE_URL", "http://localhost:5002")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:5001")

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


# Error handlers to ensure all errors return JSON (not HTML)
@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors - returns JSON instead of HTML."""
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors - returns JSON instead of HTML."""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    return jsonify({"error": "Internal server error"}), 500


# Helper functions
def log_action(action: str, username: str = None, details: str = None):
    """Log an action via DB Manager."""
    try:
        response = requests.post(
            f"{DB_MANAGER_URL}/db/games/log-action",
            json={"action": action, "username": username, "details": details},
            timeout=3
        )
        if response.status_code != 200:
            print(f"Failed to log action: {response.status_code}")
    except Exception as e:
        print(f"Failed to log action: {e}")


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


def check_both_played(game):
    """Check if both players have played their cards this turn."""
    return game.get("player1_has_played", False) and game.get(
        "player2_has_played", False
    )


def get_game_end_status(p1_deck, p2_deck, p1_score, p2_score, turn_number=0):
    """Determine game end status and winner."""
    # Check for 7th round tie
    if turn_number == 7 and p1_score == p2_score and len(p1_deck) > 0 and len(p2_deck) > 0:
        return False, None, True, True, True
    
    # Check if either player can continue
    p1_can_continue = len(p1_deck) >= 3
    p2_can_continue = len(p2_deck) >= 3

    game_should_end = not p1_can_continue or not p2_can_continue

    if not game_should_end:
        return False, None, False, False, False

    # Determine winner
    if p1_score > p2_score:
        return True, "player1", False, False, False
    elif p2_score > p1_score:
        return True, "player2", False, False, False
    else:
        tie_breaker_possible = len(p1_deck) > 0 and len(p2_deck) > 0
        return True, None, True, tie_breaker_possible, False


HISTORY_LOCK_MESSAGE = "Game history is archived and cannot be modified"


def is_game_archived(game_id):
    """Check if game is archived via DB Manager."""
    try:
        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}/is-archived",
            timeout=3
        )
        return response.status_code == 200 and response.json().get("archived", False)
    except Exception as e:
        print(f"Failed to check if game is archived: {e}")
        return False


def build_history_snapshot(game, player1_score, player2_score, winner_name, p1_deck, p2_deck):
    """Prepare the payload for game history."""
    try:
        round_history = json.loads(game.get("round_history") or "[]")
    except Exception:
        round_history = []

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
        "round_history": round_history,
        "created_at": (
            game["created_at"].isoformat() if game.get("created_at") else None
        ),
        "archived_at": datetime.utcnow().isoformat(),
    }


def archive_game_history(game, player1_score, player2_score, winner_name, p1_deck, p2_deck):
    """Archive game history via DB Manager."""
    try:
        security_obj = get_history_security()
        snapshot = build_history_snapshot(
            game, player1_score, player2_score, winner_name, p1_deck, p2_deck
        )
        encrypted_payload, integrity_hash = security_obj.encrypt_snapshot(snapshot)

        try:
            round_history = json.loads(game.get("round_history") or "[]")
        except Exception:
            round_history = []

        response = requests.post(
            f"{DB_MANAGER_URL}/db/games/{game['game_id']}/archive",
            json={
                "player1_name": game["player1_name"],
                "player2_name": game["player2_name"],
                "player1_score": player1_score,
                "player2_score": player2_score,
                "winner": winner_name,
                "encrypted_payload": encrypted_payload.hex() if isinstance(encrypted_payload, bytes) else encrypted_payload,
                "integrity_hash": integrity_hash,
                "round_history": round_history,
            },
            timeout=5
        )
        if response.status_code != 200:
            print(f"Failed to archive game: {response.status_code}")
    except Exception as e:
        print(f"Failed to archive game history: {e}")


def auto_resolve_round(game):
    """Automatically resolve a round when both players have played cards."""
    try:
        try:
            player1_card_data = json.loads(game["player1_played_card"] or "null")
            player2_card_data = json.loads(game["player2_played_card"] or "null")
        except Exception as e:
            print(f"Error parsing played cards: {e}")
            return None

        if not player1_card_data or not player2_card_data:
            return None

        # Create card objects
        player1_card = Card(player1_card_data["type"], player1_card_data["power"])
        player2_card = Card(player2_card_data["type"], player2_card_data["power"])

        # Determine round winner
        if player1_card.beats(player2_card):
            round_winner = 1
            round_tied = False
        elif player2_card.beats(player1_card):
            round_winner = 2
            round_tied = False
        elif player1_card.ties_with(player2_card):
            round_winner = None
            round_tied = True
        else:
            round_winner = None
            round_tied = False

        # Update scores
        new_p1_score = game["player1_score"]
        new_p2_score = game["player2_score"]
        if round_winner == 1:
            new_p1_score += 1
        elif round_winner == 2:
            new_p2_score += 1

        # Parse decks
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        # Check game end status
        game_should_end, winner, is_tie, tie_breaker_possible, awaiting_tiebreaker = (
            get_game_end_status(
                p1_deck, p2_deck, new_p1_score, new_p2_score, turn_number=game["turn"]
            )
        )

        # Determine winner name
        winner_name = None
        if game_should_end and winner:
            winner_name = game["player1_name"] if winner == "player1" else game["player2_name"]

        # Store round in history
        try:
            existing_history = json.loads(game.get("round_history") or "[]")
        except Exception:
            existing_history = []

        round_data = {
            "round": game["turn"],
            "player1_card": player1_card_data,
            "player2_card": player2_card_data,
            "round_winner": round_winner,
            "round_tied": round_tied,
            "player1_score_after": new_p1_score,
            "player2_score_after": new_p2_score,
        }
        existing_history.append(round_data)

        # Determine new game status
        if awaiting_tiebreaker:
            new_game_status = "active"
        elif game_should_end:
            new_game_status = "completed"
        else:
            current_status = game.get("game_status", "active")
            new_game_status = "active" if current_status == "pending" else current_status

        # Update game via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game['game_id']}/resolve-round",
            json={
                "player1_score": new_p1_score,
                "player2_score": new_p2_score,
                "game_status": new_game_status,
                "winner": winner_name,
                "turn": game["turn"] + 1,
                "round_history": existing_history,
                "awaiting_tiebreaker_response": awaiting_tiebreaker,
            },
            timeout=3
        )

        if response.status_code != 200:
            print(f"Failed to resolve round: {response.status_code}")
            return None

        if game_should_end:
            archive_game_history(game, new_p1_score, new_p2_score, winner_name, p1_deck, p2_deck)

        return {
            "round_winner": round_winner,
            "round_tied": round_tied,
            "player1_card": player1_card_data,
            "player2_card": player2_card_data,
            "player1_score": new_p1_score,
            "player2_score": new_p2_score,
            "game_over": game_should_end,
            "winner": winner_name,
            "is_tie": is_tie,
            "tie_breaker_possible": tie_breaker_possible,
            "awaiting_tiebreaker": awaiting_tiebreaker,
        }
    except Exception as e:
        print(f"Error in auto_resolve_round: {e}")
        return None


def mark_game_as_active(game_id):
    """Mark a game as active via DB Manager."""
    try:
        requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/mark-active",
            timeout=3
        )
    except Exception as e:
        print(f"Failed to mark game as active: {e}")


# Routes

@app.route("/health", methods=["GET"])
@app.route("/api/games/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "game-service"}), 200


@app.route("/api/games", methods=["POST"])
@jwt_required()
@require_sanitized_input({"player2_name": "username"})
def create_game():
    """Create a new game with deck selection phase."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data or not data.get("player2_name"):
            return jsonify({"error": "Player 2 name is required"}), 400

        try:
            player1_name = InputSanitizer.validate_username(current_user)
            player2_name = InputSanitizer.validate_username(data["player2_name"])
        except ValueError as e:
            return jsonify({"error": f"Invalid player name: {str(e)}"}), 400

        if player1_name == player2_name:
            return jsonify({"error": "Cannot create game with yourself"}), 400

        game_id = str(uuid.uuid4())

        # Create game via DB Manager
        response = requests.post(
            f"{DB_MANAGER_URL}/db/games/create",
            json={
                "game_id": game_id,
                "player1_name": player1_name,
                "player2_name": player2_name,
            },
            timeout=3
        )

        if response.status_code != 201:
            return jsonify({"error": "Failed to create game"}), 500

        log_action(
            "GAME_CREATED",
            player1_name,
            f"Created game {game_id} with {player2_name}",
        )

        return jsonify({
            "game_id": game_id,
            "player1_name": player1_name,
            "player2_name": player2_name,
            "status": "pending",
            "turn": 1,
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to create game: {str(e)}"}), 500


@app.route("/api/games/<game_id>", methods=["GET"])
@jwt_required()
def get_game(game_id):
    """Get game state."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code == 404:
            return jsonify({"error": "Game not found"}), 404

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch game"}), 500

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized to view this game"}), 403

        try:
            player1_deck = json.loads(game["player1_deck_cards"] or "[]")
            player1_hand = json.loads(game["player1_hand_cards"] or "[]")
            player2_deck = json.loads(game["player2_deck_cards"] or "[]")
            player2_hand = json.loads(game["player2_hand_cards"] or "[]")
            player1_played = json.loads(game["player1_played_card"] or "null")
            player2_played = json.loads(game["player2_played_card"] or "null")
            round_history = json.loads(game["round_history"] or "[]")
        except:
            return jsonify({"error": "Failed to parse game data"}), 500

        return jsonify({
            "game_id": game_id,
            "turn": game["turn"],
            "status": game["game_status"],
            "player1": {
                "name": game["player1_name"],
                "deck_size": len(player1_deck),
                "hand": player1_hand,
                "score": game["player1_score"],
                "played_card": player1_played,
                "has_drawn": game["player1_has_drawn"],
                "has_played": game["player1_has_played"],
            },
            "player2": {
                "name": game["player2_name"],
                "deck_size": len(player2_deck),
                "hand": player2_hand,
                "score": game["player2_score"],
                "played_card": player2_played,
                "has_drawn": game["player2_has_drawn"],
                "has_played": game["player2_has_played"],
            },
            "round_history": round_history,
            "winner": game.get("winner"),
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get game: {str(e)}"}), 500



@app.route("/api/games/<game_id>/history", methods=["GET"])
@jwt_required()
def get_game_history(game_id):
    """Get game history if archived."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}/history",
            timeout=3
        )

        if response.status_code == 404:
            return jsonify({"error": "Game history not found"}), 404

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch game history"}), 500

        history = response.json()

        # Auth check
        if current_user not in [history["player1_name"], history["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            round_history = json.loads(history.get("round_history") or "[]")
        except:
            round_history = []

        return jsonify({
            "game_id": game_id,
            "player1_name": history["player1_name"],
            "player2_name": history["player2_name"],
            "player1_score": history["player1_score"],
            "player2_score": history["player2_score"],
            "winner": history["winner"],
            "archived_at": history.get("archived_at"),
            "round_history": round_history,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get game history: {str(e)}"}), 500


@app.route("/api/games/<game_id>/hand", methods=["GET"])
@jwt_required()
def get_player_hand(game_id):
    """Get current player's hand."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized to view this game"}), 403

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
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        # Get current game state
        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if is_game_archived(game_id):
            return jsonify({"error": HISTORY_LOCK_MESSAGE}), 409

        if game["game_status"] not in ["active", "pending", "deck_selection"]:
            return jsonify({"error": "Game is not active"}), 400

        is_player1 = current_user == game["player1_name"]
        if not is_player1 and current_user != game["player2_name"]:
            return jsonify({"error": "Unauthorized to play this game"}), 403

        # Mark as active if player2 first interacts
        if not is_player1 and game.get("game_status") == "pending":
            mark_game_as_active(game_id)

        # Check if already drawn
        has_drawn_field = "player1_has_drawn" if is_player1 else "player2_has_drawn"
        if game.get(has_drawn_field, False):
            return jsonify({
                "error": "You have already drawn cards this turn. Wait for both players to play."
            }), 400

        # Parse deck
        deck_field = "player1_deck_cards" if is_player1 else "player2_deck_cards"
        try:
            deck = json.loads(game[deck_field] or "[]")
        except:
            deck = []

        if len(deck) == 0:
            return jsonify({"error": "No cards left in deck"}), 400

        # Draw cards
        if len(deck) < 3:
            hand = deck.copy()
            remaining_deck = []
        else:
            drawn_indices = random.sample(range(len(deck)), 3)
            hand = [deck[i] for i in drawn_indices]
            remaining_deck = [deck[i] for i in range(len(deck)) if i not in drawn_indices]

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/draw-hand",
            json={
                "is_player1": is_player1,
                "hand": hand,
                "remaining_deck": remaining_deck,
            },
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to draw hand"}), 500

        return jsonify({
            "hand": hand,
            "deck_size": len(remaining_deck),
            "is_final_hand": len(remaining_deck) == 0,
            "cards_drawn": len(hand),
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to draw hand: {str(e)}"}), 500


@app.route("/api/games/<game_id>/play-card", methods=["POST"])
@jwt_required()
@require_sanitized_input({"card_index": "int"})
def play_card(game_id):
    """Play a card from hand."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data or "card_index" not in data:
            return jsonify({"error": "Card index is required"}), 400

        try:
            card_index = InputSanitizer.validate_integer(
                data["card_index"], min_val=0, max_val=20
            )
        except ValueError as e:
            return jsonify({"error": f"Invalid card index: {str(e)}"}), 400

        # Get game
        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if is_game_archived(game_id):
            return jsonify({"error": HISTORY_LOCK_MESSAGE}), 409

        if game["game_status"] not in ["active", "pending", "deck_selection"]:
            return jsonify({"error": "Game is not active"}), 400

        is_player1 = current_user == game["player1_name"]
        if not is_player1 and current_user != game["player2_name"]:
            return jsonify({"error": "Unauthorized to play this game"}), 403

        # Mark active if player2 first interacts
        if not is_player1 and game.get("game_status") == "pending":
            mark_game_as_active(game_id)

        # Check if player has drawn
        has_drawn_field = "player1_has_drawn" if is_player1 else "player2_has_drawn"
        if not game.get(has_drawn_field, False):
            return jsonify({"error": "You must draw cards before playing"}), 400

        # Check if already played
        has_played_field = "player1_has_played" if is_player1 else "player2_has_played"
        if game.get(has_played_field, False):
            return jsonify({
                "error": "You have already played a card this turn. Wait for the round to resolve."
            }), 400

        # Get hand
        hand_field = "player1_hand_cards" if is_player1 else "player2_hand_cards"
        try:
            hand = json.loads(game[hand_field] or "[]")
        except:
            hand = []

        if not hand or card_index < 0 or card_index >= len(hand):
            return jsonify({"error": "Invalid card index"}), 400

        played_card = hand[card_index]

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/play-card",
            json={
                "is_player1": is_player1,
                "played_card": played_card,
            },
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to play card"}), 500

        # Get updated game
        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )
        updated_game = response.json() if response.status_code == 200 else game

        both_played = check_both_played(updated_game)

        result = {
            "played_card": played_card,
            "remaining_hand": [],
            "both_played": both_played,
            "discarded_cards": 2 if len(hand) == 3 else (len(hand) - 1),
        }

        if both_played:
            auto_result = auto_resolve_round(updated_game)
            if auto_result:
                result["round_resolved"] = True
                result["round_result"] = auto_result

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Failed to play card: {str(e)}"}), 500



@app.route("/api/games/<game_id>/resolve-round", methods=["POST"])
@jwt_required()
def resolve_round(game_id):
    """Manually resolve a round."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if game["game_status"] not in ["active", "pending", "deck_selection"]:
            return jsonify({"error": "Game is not active"}), 400

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        auto_result = auto_resolve_round(game)

        if not auto_result:
            return jsonify({"error": "Failed to resolve round"}), 500

        return jsonify(auto_result), 200

    except Exception as e:
        return jsonify({"error": f"Failed to resolve round: {str(e)}"}), 500


@app.route("/api/games/<game_id>/accept", methods=["POST"])
@jwt_required()
def accept_invitation(game_id):
    """Accept a pending game invitation."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Only players in this game can accept"}), 403

        if game.get("game_status") not in ["pending", "deck_selection"]:
            return jsonify({
                "error": "Can only accept pending invitations or games in deck selection"
            }), 400

        if game.get("game_status") in ["deck_selection", "active"]:
            return jsonify({
                "message": "Game already accepted",
                "status": game.get("game_status"),
            }), 200

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/accept",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to accept invitation"}), 500

        log_action(
            "GAME_INVITATION_ACCEPTED",
            current_user,
            f"Accepted game invitation {game_id}",
        )

        return jsonify({
            "message": "Invitation accepted successfully",
            "status": "deck_selection",
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to accept invitation: {str(e)}"}), 500


@app.route("/api/games/<game_id>/ignore", methods=["POST"])
@jwt_required()
def ignore_invitation(game_id):
    """Ignore a game invitation."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user != game["player2_name"]:
            return jsonify({
                "error": "Only the invited player can ignore this invitation"
            }), 403

        if game.get("game_status") not in ["pending", "deck_selection"]:
            return jsonify({
                "error": "Can only ignore pending invitations or games in deck selection"
            }), 400

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/ignore",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to ignore invitation"}), 500

        log_action(
            "GAME_INVITATION_DECLINED",
            current_user,
            f"Declined game invitation {game_id}",
        )

        return jsonify({"message": "Invitation ignored successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to ignore invitation: {str(e)}"}), 500


@app.route("/api/games/<game_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_invitation(game_id):
    """Cancel a game invitation."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user != game["player1_name"]:
            return jsonify({
                "error": "Only the game creator can cancel this invitation"
            }), 403

        if game.get("game_status") not in ["pending", "deck_selection"]:
            return jsonify({
                "error": "Can only cancel pending invitations or games in deck selection"
            }), 400

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/cancel",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to cancel invitation"}), 500

        log_action(
            "GAME_INVITATION_CANCELLED",
            current_user,
            f"Cancelled game invitation {game_id}",
        )

        return jsonify({"message": "Invitation cancelled successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to cancel invitation: {str(e)}"}), 500


@app.route("/api/games/<game_id>/end", methods=["POST"])
@jwt_required()
def end_game(game_id):
    """End a game."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        current_status = game.get("game_status", "active")
        if game["winner"]:
            new_status = "completed"
        elif current_status == "pending":
            new_status = "ignored"
        elif game["turn"] <= 1:
            new_status = "abandoned"
        else:
            new_status = "abandoned"

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/end",
            json={"new_status": new_status},
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to end game"}), 500

        # Archive if needed
        if new_status in ["completed", "abandoned"]:
            archive_game_history(
                game,
                game["player1_score"],
                game["player2_score"],
                game["winner"],
                p1_deck,
                p2_deck,
            )

        if new_status == "completed":
            winner = game["winner"] or "tie"
            log_action(
                "GAME_COMPLETED",
                current_user,
                f"Game {game_id} completed - Winner: {winner}",
            )
        elif new_status == "abandoned":
            log_action(
                "GAME_ABANDONED", current_user, f"Game {game_id} abandoned"
            )

        return jsonify({"message": "Game ended successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to end game: {str(e)}"}), 500


@app.route("/api/games/user/<username>", methods=["GET"])
@jwt_required()
def get_user_games(username):
    """Get all games for a user."""
    try:
        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({"error": f"Invalid username: {str(e)}"}), 400

        current_user = get_jwt_identity()
        include_history = request.args.get("include_history", "false").lower() == "true"

        if current_user != username:
            return jsonify({"error": "Unauthorized"}), 403

        # Get games via DB Manager
        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/user/{username}",
            params={"include_history": include_history},
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch games"}), 500

        return jsonify(response.json()), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get user games: {str(e)}"}), 500


@app.route("/api/games/<game_id>/tie-breaker-status", methods=["GET"])
@jwt_required()
def get_tie_breaker_status(game_id):
    """Get tiebreaker status."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        if not game.get("awaiting_tiebreaker_response", False):
            return jsonify({
                "status": "no_tiebreaker",
                "message": "Game is not awaiting tiebreaker decision"
            }), 200

        p1_decision = game.get("player1_tiebreaker_decision")
        p2_decision = game.get("player2_tiebreaker_decision")

        return jsonify({
            "status": "awaiting_decision",
            "player1_decided": p1_decision is not None,
            "player2_decided": p2_decision is not None,
            "player1_decision": p1_decision,
            "player2_decision": p2_decision,
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get tiebreaker status: {str(e)}"}), 500


@app.route("/api/games/<game_id>/tiebreaker-decision", methods=["POST"])
@jwt_required()
def submit_tiebreaker_decision(game_id):
    """Submit tiebreaker decision."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data or "decision" not in data:
            return jsonify({"error": "Decision is required (yes or no)"}), 400

        decision = data["decision"].lower()
        if decision not in ["yes", "no"]:
            return jsonify({"error": "Decision must be 'yes' or 'no'"}), 400

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        is_player1 = current_user == game["player1_name"]
        is_player2 = current_user == game["player2_name"]

        if not is_player1 and not is_player2:
            return jsonify({"error": "Unauthorized"}), 403

        if not game.get("awaiting_tiebreaker_response", False):
            return jsonify({
                "error": "Game is not awaiting tiebreaker decision"
            }), 400

        # Update decision via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/tiebreaker-decision",
            json={
                "is_player1": is_player1,
                "decision": decision,
            },
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to submit decision"}), 500

        response_data = response.json()

        if decision == "no":
            archive_game_history(
                game,
                game["player1_score"],
                game["player2_score"],
                None,
                json.loads(game["player1_deck_cards"] or "[]"),
                json.loads(game["player2_deck_cards"] or "[]"),
            )

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to submit tiebreaker decision: {str(e)}"}), 500


@app.route("/api/games/<game_id>/tiebreaker-play", methods=["POST"])
@jwt_required()
def play_tiebreaker_card(game_id):
    """Play tiebreaker card."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        is_player1 = current_user == game["player1_name"]
        is_player2 = current_user == game["player2_name"]

        if not is_player1 and not is_player2:
            return jsonify({"error": "Unauthorized"}), 403

        if game.get("game_status") != "active":
            return jsonify({"error": "Game is not active"}), 400

        # Get remaining decks
        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
        except:
            p1_deck = p2_deck = []

        if (is_player1 and len(p1_deck) != 1) or (is_player2 and len(p2_deck) != 1):
            return jsonify({"error": "Invalid deck state for tiebreaker"}), 400

        # Get card
        card = p1_deck[0] if is_player1 else p2_deck[0]

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/tiebreaker-play",
            json={
                "is_player1": is_player1,
                "played_card": card,
            },
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to play tiebreaker card"}), 500

        # Get updated game
        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )
        updated_game = response.json() if response.status_code == 200 else game

        p1_played = json.loads(updated_game.get("player1_played_card") or "null")
        p2_played = json.loads(updated_game.get("player2_played_card") or "null")

        result = {"played_card": card}

        if p1_played and p2_played:
            player1_card = Card(p1_played["type"], p1_played["power"])
            player2_card = Card(p2_played["type"], p2_played["power"])

            if player1_card.beats(player2_card):
                winner_name = game["player1_name"]
            elif player2_card.beats(player1_card):
                winner_name = game["player2_name"]
            else:
                winner_name = None

            result["round_resolved"] = True
            result["winner"] = winner_name

            # Archive game
            archive_game_history(
                game,
                game["player1_score"],
                game["player2_score"],
                winner_name,
                [],
                [],
            )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Failed to play tiebreaker card: {str(e)}"}), 500


@app.route("/api/games/<game_id>/turn-info", methods=["GET"])
@jwt_required()
def get_turn_info(game_id):
    """Get turn information."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        try:
            p1_deck = json.loads(game["player1_deck_cards"] or "[]")
            p2_deck = json.loads(game["player2_deck_cards"] or "[]")
            p1_hand = json.loads(game["player1_hand_cards"] or "[]")
            p2_hand = json.loads(game["player2_hand_cards"] or "[]")
            p1_played = json.loads(game["player1_played_card"] or "null")
            p2_played = json.loads(game["player2_played_card"] or "null")
        except:
            return jsonify({"error": "Failed to parse game state"}), 500

        both_need_to_draw = len(p1_hand) == 0 and len(p2_hand) == 0
        p1_needs_to_draw = len(p1_hand) == 0 and len(p1_deck) >= 3
        p2_needs_to_draw = len(p2_hand) == 0 and len(p2_deck) >= 3
        p1_needs_to_play = len(p1_hand) > 0 and p1_played is None
        p2_needs_to_play = len(p2_hand) > 0 and p2_played is None
        both_played = p1_played is not None and p2_played is not None

        return jsonify({
            "game_id": game_id,
            "turn": game["turn"],
            "game_status": game["game_status"],
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
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get turn info: {str(e)}"}), 500


@app.route("/api/games/<game_id>/select-deck", methods=["POST"])
@jwt_required()
def select_deck(game_id):
    """Select deck for a game."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data or not data.get("deck"):
            return jsonify({"error": "Deck is required"}), 400

        deck = data["deck"]

        if not isinstance(deck, list):
            return jsonify({"error": "Deck must be an array"}), 400

        if len(deck) != 22:
            return jsonify({
                "error": f"Deck must contain exactly 22 cards, got {len(deck)}"
            }), 400

        valid_types = ["Rock", "Paper", "Scissors"]
        for card in deck:
            if not isinstance(card, dict) or "type" not in card:
                return jsonify({"error": "Each card must have a type"}), 400
            if card["type"] not in valid_types:
                return jsonify({
                    "error": f"Invalid card type: {card['type']}"
                }), 400

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}",
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Game not found"}), 404

        game = response.json()

        if current_user not in [game["player1_name"], game["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        if game["game_status"] not in ["pending", "deck_selection"]:
            return jsonify({"error": "Game is not in deck selection phase"}), 400

        # Get token for card service
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{CARD_SERVICE_URL}/api/cards", headers=headers
            )
            if response.status_code == 200:
                all_cards = response.json()["cards"]
            else:
                return jsonify({"error": "Failed to fetch cards from card service"}), 500
        except Exception as e:
            return jsonify({"error": f"Failed to connect to card service: {str(e)}"}), 500

        # Group cards
        cards_by_type = {"Rock": [], "Paper": [], "Scissors": []}
        for card in all_cards:
            if card["type"] in cards_by_type:
                cards_by_type[card["type"]].append(card)

        # Assign powers
        final_deck = []
        for card_request in deck:
            card_type = card_request["type"]
            available_cards = cards_by_type.get(card_type, [])

            if not available_cards:
                return jsonify({"error": f"No cards available for type: {card_type}"}), 500

            selected_card = random.choice(available_cards)
            final_deck.append({
                "id": selected_card["id"],
                "type": selected_card["type"],
                "power": selected_card["power"],
            })

        is_player1 = current_user == game["player1_name"]

        # Update via DB Manager
        response = requests.put(
            f"{DB_MANAGER_URL}/db/games/{game_id}/select-deck",
            json={
                "is_player1": is_player1,
                "deck": final_deck,
            },
            timeout=3
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to select deck"}), 500

        data = response.json()

        log_action(
            "DECK_SELECTED", current_user, f"Selected deck for game {game_id}"
        )
        if data.get("both_selected"):
            log_action(
                "GAME_STARTED",
                None,
                f"Game {game_id} started - Both players selected decks",
            )

        return jsonify({
            "message": "Deck selected successfully",
            "deck": final_deck,
            "both_selected": data.get("both_selected", False),
            "status": data.get("status", "deck_selection"),
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to select deck: {str(e)}"}), 500


@app.route("/api/games/<game_id>/status", methods=["GET"])
@jwt_required()
def get_game_status(game_id):
    """Get game status."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}/status",
            timeout=3
        )

        if response.status_code == 404:
            return jsonify({"error": "Game not found"}), 404

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch game status"}), 500

        data = response.json()

        if current_user not in [data["player1_name"], data["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get game status: {str(e)}"}), 500


@app.route("/api/games/<game_id>/details", methods=["GET"])
@jwt_required()
def get_game_details(game_id):
    """Get detailed game information."""
    try:
        game_id = InputSanitizer.sanitize_string(
            game_id, max_length=100, allow_special=False
        )
        current_user = get_jwt_identity()

        response = requests.get(
            f"{DB_MANAGER_URL}/db/games/{game_id}/details",
            timeout=3
        )

        if response.status_code == 404:
            return jsonify({"error": "Game not found"}), 404

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch game details"}), 500

        data = response.json()

        if current_user not in [data["player1_name"], data["player2_name"]]:
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify(data), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get game details: {str(e)}"}), 500


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5003, debug=debug_mode)
