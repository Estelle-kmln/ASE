"""
Leaderboard Service - Game results and rankings microservice
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests

# Add utils directory to path for input sanitizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_sanitizer import InputSanitizer, SecurityMiddleware, require_sanitized_input

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize extensions
jwt = JWTManager(app)
CORS(app)
security = SecurityMiddleware(app)

# JWT error handlers - convert 422 to 401 for invalid tokens
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    """Handle invalid token errors."""
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    """Handle missing token errors."""
    return jsonify({'error': 'Missing authorization header'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token errors."""
    return jsonify({'error': 'Token has expired'}), 401

DB_MANAGER_URL = os.getenv(
    "DB_MANAGER_URL",
    "http://db-manager:5005"
)


@app.route('/health', methods=['GET'])
@app.route('/api/leaderboard/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'leaderboard-service'}), 200

@app.route("/api/leaderboard", methods=["GET"])
@jwt_required()
def get_leaderboard():
    """Get the global leaderboard."""
    try:
        # Validate and sanitize limit parameter
        limit_param = request.args.get("limit", "10")
        try:
            limit = InputSanitizer.validate_integer(
                limit_param, min_val=1, max_val=100
            )
        except ValueError:
            limit = 10

        # 🔁 POZIV DB MANAGERA
        response = requests.get(
            f"{DB_MANAGER_URL}/db/leaderboard",
            params={"limit": limit},
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        results = response.json()

        leaderboard = []
        for i, player in enumerate(results, 1):
            leaderboard.append(
                {
                    "rank": i,
                    "player": player["player"],
                    "wins": player["wins"],
                    "games": player["games"],
                    "losses": player["games"] - player["wins"],
                    "win_percentage": float(player["win_percentage"]),
                }
            )

        return jsonify(
            {
                "leaderboard": leaderboard,
                "total_players": len(leaderboard),
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get leaderboard: {str(e)}"}), 500


@app.route("/api/leaderboard/my-matches", methods=["GET"])
@jwt_required()
def get_my_matches():
    """Get match history for the authenticated user."""
    try:
        from flask_jwt_extended import get_jwt_identity

        username = get_jwt_identity()

        if not username:
            return jsonify({"error": "Unable to identify user"}), 401

        # Validate and sanitize username
        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({"error": f"Invalid username: {str(e)}"}), 400

        # 🔁 POZIV DB MANAGERA
        response = requests.get(
            f"{DB_MANAGER_URL}/db/my-matches",
            params={"username": username},
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        games = response.json()

        matches = []
        for game in games:
            opponent = (
                game["player2_name"]
                if game["player1_name"] == username
                else game["player1_name"]
            )

            my_score = (
                game["player1_score"]
                if game["player1_name"] == username
                else game["player2_score"]
            )

            opponent_score = (
                game["player2_score"]
                if game["player1_name"] == username
                else game["player1_score"]
            )

            result = "win" if game["winner"] == username else "loss"

            matches.append(
                {
                    "game_id": game["game_id"],
                    "opponent": opponent,
                    "my_score": my_score,
                    "opponent_score": opponent_score,
                    "result": result,
                    "date": (
                        game["created_at"]
                        if game["created_at"]
                        else None
                    ),
                }
            )

        return jsonify(
            {
                "matches": matches,
                "total": len(matches),
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get matches: {str(e)}"}), 500


@app.route("/api/leaderboard/player/<player_name>", methods=["GET"])
@jwt_required()
def get_player_stats(player_name):
    """Get detailed statistics for a specific player."""
    try:
        # Validate and sanitize player name
        try:
            player_name = InputSanitizer.validate_username(player_name)
        except ValueError as e:
            return jsonify({"error": f"Invalid player name: {str(e)}"}), 400

        # 🔁 DB MANAGER – player stats
        stats_resp = requests.get(
            f"{DB_MANAGER_URL}/db/player/stats",
            params={"player": player_name},
            timeout=5
        )

        if stats_resp.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        stats = stats_resp.json()

        if not stats or stats["total_games"] == 0:
            return jsonify(
                {
                    "player": player_name,
                    "wins": 0,
                    "losses": 0,
                    "total_games": 0,
                    "win_percentage": 0,
                    "recent_games": [],
                }
            ), 200

        # 🔁 DB MANAGER – recent games
        games_resp = requests.get(
            f"{DB_MANAGER_URL}/db/player/recent-games",
            params={"player": player_name},
            timeout=5
        )

        if games_resp.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        recent_games = games_resp.json()

        games_list = []
        for game in recent_games:
            opponent = (
                game["player2_name"]
                if game["player1_name"] == player_name
                else game["player1_name"]
            )

            player_score = (
                game["player1_score"]
                if game["player1_name"] == player_name
                else game["player2_score"]
            )

            opponent_score = (
                game["player2_score"]
                if game["player1_name"] == player_name
                else game["player1_score"]
            )

            result = (
                "win"
                if game["winner"] == player_name
                else ("loss" if game["winner"] else "tie")
            )

            games_list.append(
                {
                    "game_id": game["game_id"],
                    "opponent": opponent,
                    "player_score": player_score,
                    "opponent_score": opponent_score,
                    "result": result,
                    "date": (
                        game["created_at"]
                        if game["created_at"]
                        else None
                    ),
                }
            )

        return jsonify(
            {
                "player": player_name,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "total_games": stats["total_games"],
                "win_percentage": float(stats["win_percentage"]),
                "recent_games": games_list,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get player stats: {str(e)}"}), 500


@app.route("/api/leaderboard/recent-games", methods=["GET"])
@jwt_required()
def get_recent_games():
    """Get recent completed games."""
    try:
        # Validate and sanitize limit parameter
        limit_param = request.args.get("limit", "10")
        try:
            limit = InputSanitizer.validate_integer(
                limit_param, min_val=1, max_val=50
            )
        except ValueError:
            limit = 10

        # 🔁 POZIV DB MANAGERA
        response = requests.get(
            f"{DB_MANAGER_URL}/db/recent-games",
            params={"limit": limit},
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        games = response.json()

        games_list = []
        for game in games:
            games_list.append(
                {
                    "game_id": game["game_id"],
                    "player1_name": game["player1_name"],
                    "player2_name": game["player2_name"],
                    "player1_score": game["player1_score"],
                    "player2_score": game["player2_score"],
                    "winner": game["winner"],
                    "duration_turns": game["turn"],
                    "started_at": (
                        game["created_at"]
                        if game["created_at"]
                        else None
                    ),
                    "completed_at": (
                        game["updated_at"]
                        if game["updated_at"]
                        else None
                    ),
                }
            )

        return jsonify(
            {
                "recent_games": games_list,
                "total_games": len(games_list),
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get recent games: {str(e)}"}), 500


@app.route("/api/leaderboard/top-players", methods=["GET"])
@jwt_required()
def get_top_players():
    """Get top players by different metrics."""
    try:
        response = requests.get(
            f"{DB_MANAGER_URL}/db/top-players",
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        data = response.json()

        return jsonify(
            {
                "top_by_wins": [
                    {"player": row["player"], "wins": row["total_wins"]}
                    for row in data["top_by_wins"]
                ],
                "top_by_win_percentage": [
                    {
                        "player": row["player"],
                        "wins": row["wins"],
                        "games": row["games"],
                        "win_percentage": float(row["win_percentage"]),
                    }
                    for row in data["top_by_win_percentage"]
                ],
                "most_active": [
                    {
                        "player": row["player"],
                        "total_games": row["total_games"],
                    }
                    for row in data["most_active"]
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get top players: {str(e)}"}), 500


@app.route("/api/leaderboard/statistics", methods=["GET"])
@jwt_required()
def get_global_statistics():
    """Get global game statistics."""
    try:
        response = requests.get(
            f"{DB_MANAGER_URL}/db/statistics",
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        data = response.json()

        basic = data["basic"]
        outcome = data["outcome"]
        duration = data["duration"]
        recent = data["recent"]

        return jsonify(
            {
                "total_completed_games": basic["total_games"],
                "unique_players": basic["unique_players"],
                "games_with_winner": outcome["games_with_winner"],
                "tied_games": outcome["tied_games"],
                "average_game_turns": (
                    round(float(duration["avg_game_turns"]), 2)
                    if duration["avg_game_turns"]
                    else 0
                ),
                "shortest_game_turns": duration["shortest_game"],
                "longest_game_turns": duration["longest_game"],
                "games_last_week": recent["games_last_week"],
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get statistics: {str(e)}"}), 500


@app.route("/api/leaderboard/rankings", methods=["GET"])
@jwt_required()
def get_rankings():
    """Get the global leaderboard rankings based on number of wins."""
    try:
        # Validate and sanitize limit parameter
        limit_param = request.args.get("limit", "100")
        try:
            limit = InputSanitizer.validate_integer(
                limit_param, min_val=1, max_val=500
            )
        except ValueError:
            limit = 100

        response = requests.get(
            f"{DB_MANAGER_URL}/db/rankings",
            params={"limit": limit},
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "DB manager error"}), 500

        results = response.json()

        rankings = []
        for i, player in enumerate(results, 1):
            rankings.append(
                {
                    "rank": i,
                    "username": player["player"],
                    "wins": player["total_wins"],
                    "total_score": player["total_score"],
                    "games_played": player["total_games"],
                }
            )

        return jsonify(
            {
                "rankings": rankings,
                "total_players": len(rankings),
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get rankings: {str(e)}"}), 500


@app.route("/api/leaderboard/visibility", methods=["PUT"])
@jwt_required()
def update_visibility():
    """Update the authenticated user's leaderboard visibility preference."""
    try:
        from flask_jwt_extended import get_jwt_identity

        username = get_jwt_identity()
        if not username:
            return jsonify({"error": "Unable to identify user"}), 401

        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        data = request.get_json()
        if data is None or "show_on_leaderboard" not in data:
            return jsonify({"error": "Missing show_on_leaderboard parameter"}), 400

        show_on_leaderboard = data["show_on_leaderboard"]

        if not isinstance(show_on_leaderboard, bool):
            return jsonify({"error": "show_on_leaderboard must be boolean"}), 400

        response = requests.put(
            f"{DB_MANAGER_URL}/db/visibility",
            json={
                "username": username,
                "show_on_leaderboard": show_on_leaderboard,
            },
            timeout=5,
        )

        if response.status_code != 200:
            return jsonify(response.json()), response.status_code

        return jsonify(
            {
                "message": "Visibility preference updated successfully",
                "show_on_leaderboard": show_on_leaderboard,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update visibility: {str(e)}"}), 500


@app.route("/api/leaderboard/visibility", methods=["GET"])
@jwt_required()
def get_visibility():
    """Get the authenticated user's leaderboard visibility preference."""
    try:
        from flask_jwt_extended import get_jwt_identity

        username = get_jwt_identity()
        if not username:
            return jsonify({"error": "Unable to identify user"}), 401

        try:
            username = InputSanitizer.validate_username(username)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        response = requests.get(
            f"{DB_MANAGER_URL}/db/visibility",
            params={"username": username},
            timeout=5,
        )

        if response.status_code != 200:
            return jsonify(response.json()), response.status_code

        return jsonify(response.json()), 200

    except Exception as e:
        return jsonify({"error": f"Failed to get visibility: {str(e)}"}), 500


if __name__ == '__main__':
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=5004, debug=debug_mode)