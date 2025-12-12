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

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:5001")

def validate_token(token):
    """Validate token with auth service."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
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
        response = requests.get("http://db-manager:5005/cards")
        data = response.json()

        cards = data["cards"]

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

        response = requests.get(f"http://db-manager:5005/cards/by-type/{card_type}")
        data = response.json()

        cards = data["cards"]

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

        response = requests.get(f"http://db-manager:5005/cards/{card_id}")

        if response.status_code == 404:
            return jsonify({"error": "Card not found"}), 404

        data = response.json()

        card = data.get("card")

        # Format into frontend-friendly response
        card_output = {
            "id": card["id"],
            "type": card["type"],
            "power": card["power"]
        }

        return jsonify({"card": card_output}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get card: {str(e)}"}), 500


@app.route("/api/cards/random-deck", methods=["POST"])
@jwt_required()
@require_sanitized_input({"size": "int"})
def create_random_deck():
    """Create a random deck of 22 cards."""
    try:
        data = request.get_json() or {}

        # Validate deck size
        try:
            deck_size = InputSanitizer.validate_integer(
                data.get("size", 22), min_val=1, max_val=50
            )
        except ValueError as e:
            # Return error message that matches test expectations
            return jsonify({"error": "Deck size must be between 1 and 50"}), 400

        response = requests.get("http://db-manager:5005/cards")
        all_cards = response.json()["cards"]

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

        # Get all cards for analysis
        response = requests.get("http://db-manager:5005/cards")
        data = response.json()

        cards = data.get("cards", [])
        

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

if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5002, debug=debug_mode)