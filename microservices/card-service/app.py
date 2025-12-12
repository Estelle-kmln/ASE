"""
Card Service - Card database and statistics microservice
"""

import os
import sys
import random
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests

# Add utils directory to path for input sanitizer
# In Docker container, utils/ is copied to ./utils/ relative to app.py
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
from input_sanitizer import (
    InputSanitizer,
    SecurityMiddleware,
    require_sanitized_input,
)
from service_auth import ServiceAuth

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
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:5001")


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(DATABASE_URL)


def validate_token(token):
    """Validate token with auth service using service-to-service authentication."""
    try:
        # Zero-trust: Include service API key for service-to-service call
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Service-API-Key": ServiceAuth.get_service_key("card-service"),
        }
        response = requests.post(
            f"{AUTH_SERVICE_URL}/api/auth/validate", headers=headers
        )
        return response.status_code == 200
    except:
        return False


@app.route("/health", methods=["GET"])
@app.route("/api/cards/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "card-service"}), 200


@app.route("/api/cards", methods=["GET"])
@jwt_required()
def get_all_cards():
    """Get all available cards."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM cards ORDER BY type, power")
        cards = cursor.fetchall()
        conn.close()

        # Convert to list of dicts
        card_list = []
        for card in cards:
            card_list.append(
                {"id": card["id"], "type": card["type"], "power": card["power"]}
            )

        return jsonify({"cards": card_list}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get cards: {str(e)}"}), 500


@app.route("/api/cards/by-type/<card_type>", methods=["GET"])
@jwt_required()
def get_cards_by_type(card_type):
    """Get cards by type (rock, paper, scissors)."""
    try:
        # Validate and sanitize card type
        try:
            card_type = InputSanitizer.validate_card_type(card_type)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT * FROM cards WHERE LOWER(type) = LOWER(%s) ORDER BY power",
            (card_type,),
        )
        cards = cursor.fetchall()
        conn.close()

        card_list = []
        for card in cards:
            card_list.append(
                {"id": card["id"], "type": card["type"], "power": card["power"]}
            )

        return jsonify({"cards": card_list, "type": card_type}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get cards by type: {str(e)}"}), 500


@app.route("/api/cards/<int:card_id>", methods=["GET"])
@jwt_required()
def get_card_by_id(card_id):
    """Get a specific card by ID."""
    try:
        # Basic input sanitization for security (but allow any integer for proper 404s)
        if not isinstance(card_id, int) or card_id < 0:
            return jsonify({"error": "Invalid card ID format"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM cards WHERE id = %s", (card_id,))
        card = cursor.fetchone()
        conn.close()

        if not card:
            return jsonify({"error": "Card not found"}), 404

        return (
            jsonify(
                {
                    "card": {
                        "id": card["id"],
                        "type": card["type"],
                        "power": card["power"],
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get card: {str(e)}"}), 500


@app.route("/api/cards/random-deck", methods=["POST"])
@jwt_required()
@require_sanitized_input({"size": "int"})
def create_random_deck():
    """Create a random deck of 22 cards.

    Zero-trust: If called by another service, X-Service-API-Key header must be present and valid.
    User calls through API gateway don't require service key.
    """
    try:
        # Zero-trust: Validate service API key if present (for service-to-service calls)
        service_key = request.headers.get("X-Service-API-Key", "")
        if service_key:
            # If service key is provided, it must be valid
            if not ServiceAuth.validate_service_key(service_key):
                return (
                    jsonify(
                        {
                            "error": "Invalid service credentials",
                            "message": "Service API key is invalid",
                        }
                    ),
                    403,
                )
        data = request.get_json() or {}

        # Validate deck size
        try:
            deck_size = InputSanitizer.validate_integer(
                data.get("size", 22), min_val=1, max_val=50
            )
        except ValueError as e:
            # Return error message that matches test expectations
            return jsonify({"error": "Deck size must be between 1 and 50"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all available cards
        cursor.execute("SELECT * FROM cards ORDER BY type, power")
        all_cards = cursor.fetchall()
        conn.close()

        if len(all_cards) < deck_size:
            return (
                jsonify(
                    {
                        "error": f"Not enough cards in database. Available: {len(all_cards)}, Requested: {deck_size}"
                    }
                ),
                400,
            )

        # Select random cards
        selected_cards = random.sample(all_cards, deck_size)

        deck = []
        for card in selected_cards:
            deck.append(
                {"id": card["id"], "type": card["type"], "power": card["power"]}
            )

        return jsonify({"deck": deck, "size": len(deck)}), 200

    except Exception as e:
        return (
            jsonify({"error": f"Failed to create random deck: {str(e)}"}),
            500,
        )


@app.route("/api/cards/statistics", methods=["GET"])
@jwt_required()
def get_card_statistics():
    """Get card database statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all cards for analysis
        cursor.execute("SELECT type, power FROM cards")
        cards = cursor.fetchall()
        conn.close()

        if not cards:
            return jsonify({"error": "No cards found"}), 404

        # Calculate statistics
        total_cards = len(cards)
        type_counts = {}
        power_distribution = {}

        for card in cards:
            card_type = card["type"]
            power = card["power"]

            # Count by type
            type_counts[card_type] = type_counts.get(card_type, 0) + 1

            # Count by power
            power_distribution[power] = power_distribution.get(power, 0) + 1

        # Calculate percentages for types
        type_percentages = {}
        for card_type, count in type_counts.items():
            type_percentages[card_type] = round((count / total_cards) * 100, 2)

        return (
            jsonify(
                {
                    "total_cards": total_cards,
                    "type_distribution": {
                        "counts": type_counts,
                        "percentages": type_percentages,
                    },
                    "power_distribution": power_distribution,
                    "available_types": list(type_counts.keys()),
                    "power_range": {
                        "min": (
                            min(power_distribution.keys())
                            if power_distribution
                            else 0
                        ),
                        "max": (
                            max(power_distribution.keys())
                            if power_distribution
                            else 0
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500


@app.route("/api/cards/types", methods=["GET"])
@jwt_required()
def get_card_types():
    """Get all available card types."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT type FROM cards ORDER BY type")
        types_result = cursor.fetchall()

        cursor.execute("SELECT DISTINCT power FROM cards ORDER BY power")
        powers_result = cursor.fetchall()

        conn.close()

        types = [row[0] for row in types_result]
        powers = [row[0] for row in powers_result]

        return jsonify({"types": types, "powers": powers}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get card types: {str(e)}"}), 500


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5002, debug=debug_mode)
