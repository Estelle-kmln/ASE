"""
Database Manager - Centralized database access for all microservices.
Provides card, game, user, and utility data operations.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gameuser:gamepassword@localhost:5432/battlecards",
)

def get_db_connection():
    """Creates and returns a PostgreSQL connection."""
    return psycopg2.connect(DATABASE_URL)

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "db-manager"}), 200

@app.route("/cards", methods=["GET"])
def db_get_all_cards():
    """Get all available cards."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM cards ORDER BY type, power")
        cards = cursor.fetchall()
        conn.close()
        
        return jsonify({"cards": cards}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get cards: {str(e)}"}), 500

@app.route("/cards/by-type/<card_type>", methods=["GET"])
def db_get_cards_by_type(card_type):
    """Get cards by type."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT * FROM cards WHERE LOWER(type) = LOWER(%s) ORDER BY power",
            (card_type,),
        )
        cards = cursor.fetchall()
        conn.close()

        return jsonify({"cards": cards, "type": card_type}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get cards by type: {str(e)}"}), 500

@app.route("/cards/<int:card_id>", methods=["GET"])
def db_get_card_by_id(card_id):
    """Get a specific card by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM cards WHERE id = %s", (card_id,))
        card = cursor.fetchone()
        conn.close()

        if not card:
            return jsonify({"error": "Card not found"}), 404

        return jsonify({"card": card}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get card: {str(e)}"}), 500

@app.route("/cards/types", methods=["GET"])
def db_get_card_types():
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
    app.run(host="0.0.0.0", port=5005, debug=debug_mode)
