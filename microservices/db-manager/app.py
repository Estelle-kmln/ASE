"""
Database Manager - Centralized database access for all microservices.
Provides card, game, user, and utility data operations.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, timedelta
from contextlib import contextmanager



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

def log_action(action: str, username: str = None, details: str = None):
    """Log an action to the logs table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (action, username, details) VALUES (%s, %s, %s)",
            (action, username, details),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log action: {e}")

def store_refresh_token_db(user_id, refresh_token, expires_seconds, device_data):
    """Store refresh token (pure SQL)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        expires_at = datetime.now() + timedelta(seconds=expires_seconds)

        cursor.execute(
            """
            INSERT INTO refresh_tokens
                (user_id, token, expires_at, device_info, ip_address, user_agent, last_used_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                refresh_token,
                expires_at,
                device_data.get("device_info", "Unknown"),
                device_data.get("ip_address", "Unknown"),
                device_data.get("user_agent", "Unknown")
            )
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("DB error storing refresh token:", e)
        return False

def validate_refresh_token_db(refresh_token: str):
    """Validate a refresh token and return user info if valid."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query refresh token and join user
        cursor.execute(
            """SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked, u.username 
               FROM refresh_tokens rt
               JOIN users u ON rt.user_id = u.id
               WHERE rt.token = %s""",
            (refresh_token,)
        )
        token_data = cursor.fetchone()

        # Token not found
        if not token_data:
            conn.close()
            return None
        
        # Token is revoked
        if token_data["revoked"]:
            conn.close()
            return None
        
        # Token expired
        if token_data["expires_at"] < datetime.now():
            conn.close()
            return None
        
        # Update last_used_at timestamp
        cursor.execute(
            "UPDATE refresh_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE id = %s",
            (token_data["id"],)
        )
        conn.commit()
        conn.close()
        
        return token_data

    except Exception as e:
        print(f"Failed to validate refresh token: {e}")
        return None

def revoke_refresh_token_db(refresh_token: str) -> bool:
    """Revoke a refresh token."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE refresh_tokens 
            SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP 
            WHERE token = %s
            """,
            (refresh_token,)
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"Revoked refresh token - rows affected: {rows_affected}")
        return rows_affected > 0

    except Exception as e:
        print(f"Failed to revoke refresh token: {e}")
        return False

def revoke_all_user_tokens_db(user_id: int) -> bool:
    """Revoke all refresh tokens for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE refresh_tokens 
            SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP 
            WHERE user_id = %s AND revoked = FALSE
            """,
            (user_id,)
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"Revoked all tokens for user {user_id} - rows affected: {rows_affected}")
        return True

    except Exception as e:
        print(f"Failed to revoke user tokens: {e}")
        return False

def get_user_with_lock_info(username: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT id, username, password, failed_login_attempts, 
                   account_locked_until, last_failed_login
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cursor.fetchone()
        conn.close()
        return user

    except Exception as e:
        print("DB ERROR get_user:", e)
        return None

def update_failed_attempt(username: str, failed_attempts: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET failed_login_attempts = %s,
                last_failed_login = CURRENT_TIMESTAMP
            WHERE username = %s
            """,
            (failed_attempts, username)
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("DB ERROR update_failed_attempt:", e)
        return False

def lock_user(username: str, failed_attempts: int, lock_minutes: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET failed_login_attempts = %s,
                account_locked_until = CURRENT_TIMESTAMP + (%s || ' minutes')::interval,
                last_failed_login = CURRENT_TIMESTAMP
            WHERE username = %s
            """,
            (failed_attempts, lock_minutes, username)
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("DB ERROR lock_user:", e)
        return False

def reset_failed_attempts(username: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET failed_login_attempts = 0,
                account_locked_until = NULL,
                last_failed_login = NULL
            WHERE username = %s
            """,
            (username,)
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("DB ERROR reset_failed_attempts:", e)
        return False


# Health check
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "db-manager"}), 200

# Cards requests
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


# Auth requests
@app.route("/tokens/active/<int:user_id>", methods=["GET"])
def get_active_sessions_db(user_id):
    """Return active (non-expired, non-revoked) sessions for a user.
       Also performs cleanup of expired tokens."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # First, clean up expired tokens
        cursor.execute(
            """
            UPDATE refresh_tokens
            SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND revoked = FALSE AND expires_at <= CURRENT_TIMESTAMP
            """,
            (user_id,)
        )
        conn.commit()

        # Now get active sessions
        cursor.execute(
            """
            SELECT id, device_info, ip_address, created_at, last_used_at
            FROM refresh_tokens
            WHERE user_id = %s 
              AND revoked = FALSE 
              AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        sessions = cursor.fetchall()
        conn.close()

        return jsonify({"sessions": sessions}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tokens/store", methods=["POST"])
def store_refresh_token_route():
    try:
        data = request.get_json()

        user_id = data["user_id"]
        refresh_token = data["refresh_token"]
        expires_seconds = data["expires_delta"]
        device_data = data.get("device_data", {})

        result = store_refresh_token_db(
            user_id,
            refresh_token,
            expires_seconds,
            device_data
        )

        if result:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tokens/validate", methods=["POST"])
def validate_refresh_token_route():
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        token_data = validate_refresh_token_db(refresh_token)

        if token_data is None:
            return jsonify({"token_data": None}), 200

        return jsonify({"token_data": token_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tokens/revoke", methods=["POST"])
def revoke_refresh_token_route():
    try:
        data = request.get_json()
        refresh_token = data.get("refresh_token")

        success = revoke_refresh_token_db(refresh_token)

        return jsonify({"success": success}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/tokens/revoke_all", methods=["POST"])
def revoke_all_user_tokens_route():
    try:
        data = request.get_json()
        user_id = data.get("user_id")

        success = revoke_all_user_tokens_db(user_id)

        return jsonify({"success": success}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/exists/<username>", methods=["GET"])
def user_exists(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        exists = cursor.fetchone()[0] > 0

        conn.close()
        return jsonify({"exists": exists}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/create", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"]  # already hashed

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, password),
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        return jsonify({"user_id": user_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/users/<username>", methods=["GET"])
def db_get_user(username):
    """Return user by username (id, username, password_hash)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({"user": None}), 404

        return jsonify({"user": user}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/user/<username>", methods=["GET"])
def db_get_user_lockinfo(username):
    user = get_user_with_lock_info(username)

    if not user:
        return jsonify({"user": None}), 200

    return jsonify({"user": user}), 200

@app.route("/auth/fail_attempt", methods=["POST"])
def db_fail_attempt():
    data = request.get_json()
    username = data.get("username")
    failed_attempts = data.get("failed_attempts")

    success = update_failed_attempt(username, failed_attempts)
    return jsonify({"success": success}), 200

@app.route("/auth/lock", methods=["POST"])
def db_lock_user():
    data = request.get_json()
    username = data.get("username")
    failed_attempts = data.get("failed_attempts")
    lock_minutes = data.get("lock_minutes")

    success = lock_user(username, failed_attempts, lock_minutes)
    return jsonify({"success": success}), 200

@app.route("/auth/reset_failures", methods=["POST"])
def db_reset_failures():
    data = request.get_json()
    username = data.get("username")

    success = reset_failed_attempts(username)
    return jsonify({"success": success}), 200

@app.route("/auth/profile/<username>", methods=["GET"])
def get_profile_db(username):
    """Get user profile from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id, username, is_admin, enabled, created_at FROM users WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({"user": None}), 404

        # Convert timestamp safely
        if user.get("created_at"):
            user["created_at"] = user["created_at"].isoformat()

        return jsonify({"user": user}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/update_username", methods=["POST"])
def update_username_db():
    """Update username in database."""
    try:
        data = request.get_json()
        old_username = data["old_username"]
        new_username = data["new_username"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if new username already exists
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE username = %s", (new_username,)
        )
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({"error": "Username already exists"}), 409

        cursor.execute(
            "UPDATE users SET username = %s WHERE username = %s",
            (new_username, old_username),
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/update_password", methods=["POST"])
def update_password_db():
    """Update user's password."""
    try:
        data = request.get_json()
        username = data["username"]
        hashed_password = data["hashed_password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (hashed_password, username),
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/user-exists/<username>", methods=["GET"])
def user_exists_db(username):
    """Check if user exists (for token validation)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE username = %s", (username,)
        )
        exists = cursor.fetchone()[0] > 0

        conn.close()
        return jsonify({"exists": exists}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/user-id/<username>", methods=["GET"])
def get_user_id(username):
    """Return user ID by username (used for logout)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()

        conn.close()

        if not row:
            return jsonify({"user_id": None}), 200
        
        return jsonify({"user_id": row[0]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/is-admin/<username>", methods=["GET"])
def check_is_admin(username):
    """Check if user is admin by username."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({"is_admin": False}), 200
        
        return jsonify({"is_admin": user.get("is_admin", False)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users", methods=["GET"])
def admin_list_users():
    """Return paginated list of all users for admin."""
    try:
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 10))
        offset = page * size

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Total count
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        total = cursor.fetchone()["count"]

        # Paginated users
        cursor.execute(
            """
            SELECT id, username, is_admin, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (size, offset),
        )
        users = cursor.fetchall()
        conn.close()

        return jsonify({
            "users": users,
            "total": total
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/search", methods=["GET"])
def admin_search_users():
    """Search users by username with pagination."""
    try:
        query = request.args.get("query", "")
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 10))
        offset = page * size

        search_pattern = f"%{query}%"

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Count results
        cursor.execute(
            "SELECT COUNT(*) AS count FROM users WHERE username ILIKE %s",
            (search_pattern,),
        )
        total = cursor.fetchone()["count"]

        # Paginated users
        cursor.execute(
            """
            SELECT id, username, is_admin, created_at
            FROM users
            WHERE username ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (search_pattern, size, offset),
        )
        users = cursor.fetchall()
        conn.close()

        return jsonify({
            "users": users,
            "total": total
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/roles", methods=["GET"])
def admin_list_roles():
    """Return list of available roles."""
    return jsonify([
        {"id": "ROLE_USER", "name": "User"},
        {"id": "ROLE_ADMIN", "name": "Administrator"}
    ]), 200




# Leaderboard requests


# Routes

@app.route("/db/leaderboard", methods=["GET"])
def db_get_leaderboard():
    """
    DB MANAGER endpoint
    Samo vadi podatke iz baze – BEZ biznis logike
    """
    try:
        limit = int(request.args.get("limit", 10))

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            WITH player_stats AS (
                SELECT player1_name as player, COUNT(*) as wins
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                  AND winner = player1_name
                GROUP BY player1_name

                UNION ALL

                SELECT player2_name as player, COUNT(*) as wins
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                  AND winner = player2_name
                GROUP BY player2_name
            ),
            total_games AS (
                SELECT player1_name as player, COUNT(*) as total_games
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                GROUP BY player1_name

                UNION ALL

                SELECT player2_name as player, COUNT(*) as total_games
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                GROUP BY player2_name
            ),
            aggregated_stats AS (
                SELECT
                    COALESCE(p.player, t.player) as player,
                    SUM(p.wins) as wins,
                    SUM(t.total_games) as games
                FROM player_stats p
                FULL OUTER JOIN total_games t ON p.player = t.player
                GROUP BY COALESCE(p.player, t.player)
            )
            SELECT
                player,
                COALESCE(wins, 0) as wins,
                COALESCE(games, 0) as games,
                CASE
                    WHEN COALESCE(games, 0) = 0 THEN 0
                    ELSE ROUND((COALESCE(wins, 0)::decimal / games) * 100, 2)
                END as win_percentage
            FROM aggregated_stats
            WHERE player IS NOT NULL
            ORDER BY wins DESC, win_percentage DESC, games DESC
            LIMIT %s
            """,
            (limit,),
        )

        results = cursor.fetchall()
        conn.close()

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/db/my-matches", methods=["GET"])
def db_get_my_matches():
    """
    DB manager – samo vadi mečeve iz baze
    """
    try:
        username = request.args.get("username")

        if not username:
            return jsonify({"error": "Missing username"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                game_id,
                player1_name,
                player2_name,
                player1_score,
                player2_score,
                winner,
                created_at
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
              AND game_status != 'ignored'
              AND (player1_name = %s OR player2_name = %s)
            ORDER BY created_at DESC
            """,
            (username, username),
        )

        games = cursor.fetchall()
        conn.close()

        return jsonify(games), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/db/player/stats", methods=["GET"])
def db_player_stats():
    try:
        player = request.args.get("player")

        if not player:
            return jsonify({"error": "Missing player"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            WITH player_wins AS (
                SELECT COUNT(*) as wins
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                AND (
                    (winner = player1_name AND player1_name = %s) OR
                    (winner = player2_name AND player2_name = %s)
                )
            ),
            player_games AS (
                SELECT COUNT(*) as total_games
                FROM games
                WHERE game_status IN ('completed', 'abandoned')
                AND (player1_name = %s OR player2_name = %s)
            )
            SELECT
                p.wins,
                g.total_games,
                (g.total_games - p.wins) as losses,
                CASE
                    WHEN g.total_games = 0 THEN 0
                    ELSE ROUND((p.wins::decimal / g.total_games) * 100, 2)
                END as win_percentage
            FROM player_wins p, player_games g
            """,
            (player, player, player, player),
        )

        stats = cursor.fetchone()
        conn.close()

        return jsonify(stats), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/db/player/recent-games", methods=["GET"])
def db_player_recent_games():
    try:
        player = request.args.get("player")

        if not player:
            return jsonify({"error": "Missing player"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                game_id,
                player1_name,
                player2_name,
                player1_score,
                player2_score,
                winner,
                created_at
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
            AND (player1_name = %s OR player2_name = %s)
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (player, player),
        )

        games = cursor.fetchall()
        conn.close()

        return jsonify(games), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/db/recent-games", methods=["GET"])
def db_recent_games():
    """
    DB manager – vraca sirove game redove iz baze
    """
    try:
        limit = int(request.args.get("limit", 10))

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT
                game_id,
                player1_name,
                player2_name,
                player1_score,
                player2_score,
                winner,
                turn,
                created_at,
                updated_at
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (limit,),
        )

        games = cursor.fetchall()
        conn.close()

        return jsonify(games), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/db/top-players", methods=["GET"])
def db_top_players():
    """
    DB manager – vraca top igrace po razlicitim metrikama
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 🔹 Top by wins
        cursor.execute(
            """
            WITH player_stats AS (
                SELECT g.player1_name as player, COUNT(*) as wins
                FROM games g
                INNER JOIN users u ON g.player1_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND g.winner = g.player1_name
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player1_name

                UNION ALL

                SELECT g.player2_name as player, COUNT(*) as wins
                FROM games g
                INNER JOIN users u ON g.player2_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND g.winner = g.player2_name
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player2_name
            )
            SELECT
                player,
                SUM(wins) as total_wins
            FROM player_stats
            WHERE player IS NOT NULL
            GROUP BY player
            ORDER BY total_wins DESC
            LIMIT 5
            """
        )
        top_by_wins = cursor.fetchall()

        # 🔹 Top by win percentage
        cursor.execute(
            """
            WITH visible_players AS (
                SELECT username
                FROM users
                WHERE show_on_leaderboard = TRUE
            ),
            player_wins AS (
                SELECT player, SUM(wins) as total_wins
                FROM (
                    SELECT player1_name as player, COUNT(*) as wins
                    FROM games
                    WHERE game_status IN ('completed', 'abandoned')
                    AND winner = player1_name
                    AND player1_name IN (SELECT username FROM visible_players)
                    GROUP BY player1_name

                    UNION ALL

                    SELECT player2_name as player, COUNT(*) as wins
                    FROM games
                    WHERE game_status IN ('completed', 'abandoned')
                    AND winner = player2_name
                    AND player2_name IN (SELECT username FROM visible_players)
                    GROUP BY player2_name
                ) wins_subquery
                GROUP BY player
            ),
            player_games AS (
                SELECT player, SUM(games) as total_games
                FROM (
                    SELECT player1_name as player, COUNT(*) as games
                    FROM games
                    WHERE game_status IN ('completed', 'abandoned')
                    AND player1_name IN (SELECT username FROM visible_players)
                    GROUP BY player1_name

                    UNION ALL

                    SELECT player2_name as player, COUNT(*) as games
                    FROM games
                    WHERE game_status IN ('completed', 'abandoned')
                    AND player2_name IN (SELECT username FROM visible_players)
                    GROUP BY player2_name
                ) games_subquery
                GROUP BY player
            )
            SELECT
                pg.player,
                COALESCE(pw.total_wins, 0) as wins,
                pg.total_games as games,
                ROUND((COALESCE(pw.total_wins, 0)::decimal / pg.total_games) * 100, 2) as win_percentage
            FROM player_games pg
            LEFT JOIN player_wins pw ON pg.player = pw.player
            WHERE pg.total_games >= 1
            ORDER BY win_percentage DESC
            LIMIT 5
            """
        )
        top_by_percentage = cursor.fetchall()

        # 🔹 Most active players
        cursor.execute(
            """
            WITH total_games AS (
                SELECT g.player1_name as player, COUNT(*) as total_games
                FROM games g
                INNER JOIN users u ON g.player1_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player1_name

                UNION ALL

                SELECT g.player2_name as player, COUNT(*) as total_games
                FROM games g
                INNER JOIN users u ON g.player2_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player2_name
            )
            SELECT
                player,
                SUM(total_games) as total_games
            FROM total_games
            WHERE player IS NOT NULL
            GROUP BY player
            ORDER BY total_games DESC
            LIMIT 5
            """
        )
        most_active = cursor.fetchall()

        conn.close()

        return jsonify(
            {
                "top_by_wins": top_by_wins,
                "top_by_win_percentage": top_by_percentage,
                "most_active": most_active,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/db/statistics", methods=["GET"])
def db_global_statistics():
    """
    DB manager – vraca globalne statistike iz baze
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Total games and unique players
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_games,
                COUNT(DISTINCT player1_name) + COUNT(DISTINCT player2_name) as unique_players
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
            """
        )
        basic_stats = cursor.fetchone()

        # Games by outcome
        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN winner IS NOT NULL THEN 1 END) as games_with_winner,
                COUNT(CASE WHEN winner IS NULL THEN 1 END) as tied_games
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
            """
        )
        outcome_stats = cursor.fetchone()

        # Average / min / max game duration
        cursor.execute(
            """
            SELECT
                AVG(turn) as avg_game_turns,
                MIN(turn) as shortest_game,
                MAX(turn) as longest_game
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
            """
        )
        duration_stats = cursor.fetchone()

        # Recent activity (last 7 days)
        cursor.execute(
            """
            SELECT COUNT(*) as games_last_week
            FROM games
            WHERE game_status IN ('completed', 'abandoned')
            AND created_at >= %s
            """,
            (datetime.now() - timedelta(days=7),),
        )
        recent_activity = cursor.fetchone()

        conn.close()

        return jsonify(
            {
                "basic": basic_stats,
                "outcome": outcome_stats,
                "duration": duration_stats,
                "recent": recent_activity,
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/db/rankings", methods=["GET"])
def db_rankings():
    """
    DB manager – vraca raw ranking podatke iz baze
    """
    try:
        limit = int(request.args.get("limit", 100))

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            WITH player_stats AS (
                -- Player 1 stats
                SELECT
                    g.player1_name as player,
                    SUM(CASE WHEN g.winner = g.player1_name THEN 1 ELSE 0 END) as wins,
                    SUM(g.player1_score) as total_score,
                    COUNT(*) as games_played
                FROM games g
                INNER JOIN users u ON g.player1_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player1_name

                UNION ALL

                -- Player 2 stats
                SELECT
                    g.player2_name as player,
                    SUM(CASE WHEN g.winner = g.player2_name THEN 1 ELSE 0 END) as wins,
                    SUM(g.player2_score) as total_score,
                    COUNT(*) as games_played
                FROM games g
                INNER JOIN users u ON g.player2_name = u.username
                WHERE g.game_status IN ('completed', 'abandoned')
                AND u.show_on_leaderboard = TRUE
                GROUP BY g.player2_name
            )
            SELECT
                player,
                SUM(wins) as total_wins,
                SUM(total_score) as total_score,
                SUM(games_played) as total_games
            FROM player_stats
            WHERE player IS NOT NULL
            GROUP BY player
            ORDER BY total_wins DESC, total_score DESC, total_games DESC
            LIMIT %s
            """,
            (limit,),
        )

        rows = cursor.fetchall()
        conn.close()

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Visibility

@app.route("/db/visibility", methods=["PUT"])
def db_update_visibility():
    """
    DB manager – update show_on_leaderboard flag
    """
    try:
        data = request.get_json()

        if not data or "username" not in data or "show_on_leaderboard" not in data:
            return jsonify({"error": "Missing parameters"}), 400

        username = data["username"]
        show_on_leaderboard = data["show_on_leaderboard"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET show_on_leaderboard = %s
            WHERE username = %s
            """,
            (show_on_leaderboard, username),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "User not found"}), 404

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/db/visibility", methods=["GET"])
def db_get_visibility():
    """
    DB manager – get show_on_leaderboard flag
    """
    try:
        username = request.args.get("username")

        if not username:
            return jsonify({"error": "Missing username"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT show_on_leaderboard
            FROM users
            WHERE username = %s
            """,
            (username,),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({"error": "User not found"}), 404

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Logs requests

@app.route("/db/logs/create", methods=["POST"])
def db_create_log():
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO logs (action, username, details)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                data.get("action"),
                data.get("username"),
                data.get("details"),
            ),
        )

        log_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        return jsonify({"message": "Log created successfully", "id": log_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/db/logs/list", methods=["GET"])
def db_list_logs():
    try:
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 50))
        offset = page * size

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT COUNT(*) as count FROM logs")
        total = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT id, action, username, timestamp, details
            FROM logs
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
            """,
            (size, offset),
        )

        logs = cursor.fetchall()
        conn.close()

        return jsonify(
            {
                "total": total,
                "logs": [
                    {
                        "id": l["id"],
                        "action": l["action"],
                        "username": l["username"],
                        "timestamp": l["timestamp"].isoformat() if l["timestamp"] else None,
                        "details": l["details"],
                    }
                    for l in logs
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/db/logs/search", methods=["GET"])
def db_search_logs():
    try:
        query = request.args.get("query", "")
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 50))
        offset = page * size

        pattern = f"%{query}%"

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM logs
            WHERE action ILIKE %s OR username ILIKE %s OR details ILIKE %s
            """,
            (pattern, pattern, pattern),
        )
        total = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT id, action, username, timestamp, details
            FROM logs
            WHERE action ILIKE %s OR username ILIKE %s OR details ILIKE %s
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
            """,
            (pattern, pattern, pattern, size, offset),
        )

        logs = cursor.fetchall()
        conn.close()

        return jsonify(
            {
                "total": total,
                "logs": [
                    {
                        "id": l["id"],
                        "action": l["action"],
                        "username": l["username"],
                        "timestamp": l["timestamp"].isoformat() if l["timestamp"] else None,
                        "details": l["details"],
                    }
                    for l in logs
                ],
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/db/users/is-admin", methods=["GET"])
def db_is_admin():
    try:
        username = request.args.get("username")

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT is_admin FROM users WHERE username = %s",
            (username,),
        )

        user = cursor.fetchone()
        conn.close()

        return jsonify({"is_admin": bool(user and user["is_admin"])}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Game service
def register_game_endpoints(app, get_db_connection):
    """Register all game-related database endpoints."""

    @contextmanager
    def get_cursor():
        """Context manager for database cursor."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()


    @app.route("/db/games/create", methods=["POST"])
    def db_create_game():
        """Create a new game."""
        try:
            data = request.get_json()
            game_id = data.get("game_id")
            player1_name = data.get("player1_name")
            player2_name = data.get("player2_name")

            if not game_id or not player1_name or not player2_name:
                return jsonify({"error": "Missing required fields"}), 400

            with get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO games (
                        game_id, player1_name, player2_name, 
                        game_status, turn, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (game_id, player1_name, player2_name, "pending", 1, datetime.utcnow())
                )

            return jsonify({"game_id": game_id}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500



    @app.route("/db/games/<game_id>", methods=["GET"])
    def db_get_game(game_id):
        """Get a single game by ID."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT game_id, player1_name, player2_name, 
                           game_status, turn, player1_score, player2_score,
                           player1_deck_cards, player2_deck_cards,
                           player1_hand_cards, player2_hand_cards,
                           player1_played_card, player2_played_card,
                           player1_has_drawn, player2_has_drawn,
                           player1_has_played, player2_has_played,
                           winner, created_at, round_history,
                           awaiting_tiebreaker_response,
                           player1_tiebreaker_decision,
                           player2_tiebreaker_decision
                    FROM games WHERE game_id = %s
                    """,
                    (game_id,)
                )
                game = cursor.fetchone()

            if not game:
                return jsonify({"error": "Game not found"}), 404

            return jsonify(game), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/status", methods=["GET"])
    def db_get_game_status(game_id):
        """Get game status summary."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT game_id, player1_name, player2_name, 
                           game_status, turn, player1_score, player2_score,
                           winner, awaiting_tiebreaker_response
                    FROM games WHERE game_id = %s
                    """,
                    (game_id,)
                )
                game = cursor.fetchone()

            if not game:
                return jsonify({"error": "Game not found"}), 404

            return jsonify(game), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/details", methods=["GET"])
    def db_get_game_details(game_id):
        """Get detailed game information."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT game_id, player1_name, player2_name, 
                           game_status, turn, player1_score, player2_score,
                           player1_deck_cards, player2_deck_cards,
                           player1_hand_cards, player2_hand_cards,
                           player1_played_card, player2_played_card,
                           player1_has_drawn, player2_has_drawn,
                           player1_has_played, player2_has_played,
                           winner, created_at, round_history,
                           awaiting_tiebreaker_response,
                           player1_tiebreaker_decision,
                           player2_tiebreaker_decision
                    FROM games WHERE game_id = %s
                    """,
                    (game_id,)
                )
                game = cursor.fetchone()

            if not game:
                return jsonify({"error": "Game not found"}), 404

            return jsonify(game), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/history", methods=["GET"])
    def db_get_game_history(game_id):
        """Get archived game history."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT game_id, player1_name, player2_name,
                           player1_score, player2_score, winner,
                           archived_at, round_history
                    FROM game_history WHERE game_id = %s
                    """,
                    (game_id,)
                )
                history = cursor.fetchone()

            if not history:
                return jsonify({"error": "Game history not found"}), 404

            return jsonify(history), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/is-archived", methods=["GET"])
    def db_is_game_archived(game_id):
        """Check if a game is archived."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM game_history WHERE game_id = %s LIMIT 1",
                    (game_id,)
                )
                exists = cursor.fetchone() is not None

            return jsonify({"archived": exists}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/user/<username>", methods=["GET"])
    def db_get_user_games(username):
        """Get all games for a user."""
        try:
            include_history = request.args.get("include_history", "false").lower() == "true"

            with get_cursor() as cursor:
                if include_history:
                    # Get active games
                    cursor.execute(
                        """
                        SELECT game_id, player1_name, player2_name, game_status, 
                               turn, player1_score, player2_score, winner
                        FROM games 
                        WHERE player1_name = %s OR player2_name = %s
                        ORDER BY created_at DESC
                        """,
                        (username, username)
                    )
                    active_games = cursor.fetchall()

                    # Get archived games
                    cursor.execute(
                        """
                        SELECT game_id, player1_name, player2_name,
                               player1_score, player2_score, winner, archived_at
                        FROM game_history
                        WHERE player1_name = %s OR player2_name = %s
                        ORDER BY archived_at DESC
                        """,
                        (username, username)
                    )
                    archived_games = cursor.fetchall()

                    return jsonify({
                        "active_games": active_games,
                        "archived_games": archived_games,
                    }), 200
                else:
                    # Only active games
                    cursor.execute(
                        """
                        SELECT game_id, player1_name, player2_name, game_status, 
                               turn, player1_score, player2_score, winner
                        FROM games 
                        WHERE player1_name = %s OR player2_name = %s
                        ORDER BY created_at DESC
                        """,
                        (username, username)
                    )
                    games = cursor.fetchall()

                    return jsonify({"games": games}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/db/games/<game_id>/draw-hand", methods=["PUT"])
    def db_draw_hand(game_id):
        """Update hand and deck after drawing."""
        try:
            data = request.get_json()
            is_player1 = data.get("is_player1")
            hand = data.get("hand")
            remaining_deck = data.get("remaining_deck")

            with get_cursor() as cursor:
                if is_player1:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player1_hand_cards = %s,
                            player1_deck_cards = %s,
                            player1_has_drawn = true
                        WHERE game_id = %s
                        """,
                        (json.dumps(hand), json.dumps(remaining_deck), game_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player2_hand_cards = %s,
                            player2_deck_cards = %s,
                            player2_has_drawn = true
                        WHERE game_id = %s
                        """,
                        (json.dumps(hand), json.dumps(remaining_deck), game_id)
                    )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/play-card", methods=["PUT"])
    def db_play_card(game_id):
        """Update game when player plays a card."""
        try:
            data = request.get_json()
            is_player1 = data.get("is_player1")
            played_card = data.get("played_card")

            with get_cursor() as cursor:
                if is_player1:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player1_played_card = %s,
                            player1_has_played = true
                        WHERE game_id = %s
                        """,
                        (json.dumps(played_card), game_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player2_played_card = %s,
                            player2_has_played = true
                        WHERE game_id = %s
                        """,
                        (json.dumps(played_card), game_id)
                    )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/resolve-round", methods=["PUT"])
    def db_resolve_round(game_id):
        """Resolve a round and update game state."""
        try:
            data = request.get_json()
            player1_score = data.get("player1_score")
            player2_score = data.get("player2_score")
            game_status = data.get("game_status")
            winner = data.get("winner")
            turn = data.get("turn")
            round_history = data.get("round_history")
            awaiting_tiebreaker = data.get("awaiting_tiebreaker_response")

            with get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE games 
                    SET player1_score = %s,
                        player2_score = %s,
                        game_status = %s,
                        winner = %s,
                        turn = %s,
                        round_history = %s,
                        awaiting_tiebreaker_response = %s,
                        player1_played_card = null,
                        player2_played_card = null,
                        player1_has_drawn = false,
                        player2_has_drawn = false,
                        player1_has_played = false,
                        player2_has_played = false
                    WHERE game_id = %s
                    """,
                    (
                        player1_score, player2_score, game_status, winner, turn,
                        json.dumps(round_history), awaiting_tiebreaker, game_id
                    )
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/accept", methods=["PUT"])
    def db_accept_game(game_id):
        """Accept game invitation."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE games 
                    SET game_status = 'deck_selection'
                    WHERE game_id = %s
                    """,
                    (game_id,)
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/ignore", methods=["PUT"])
    def db_ignore_game(game_id):
        """Ignore game invitation."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE games 
                    SET game_status = 'ignored'
                    WHERE game_id = %s
                    """,
                    (game_id,)
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/cancel", methods=["PUT"])
    def db_cancel_game(game_id):
        """Cancel game invitation."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE games 
                    SET game_status = 'cancelled'
                    WHERE game_id = %s
                    """,
                    (game_id,)
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/end", methods=["PUT"])
    def db_end_game(game_id):
        """End a game."""
        try:
            data = request.get_json()
            new_status = data.get("new_status", "abandoned")

            with get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE games 
                    SET game_status = %s
                    WHERE game_id = %s
                    """,
                    (new_status, game_id)
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/mark-active", methods=["PUT"])
    def db_mark_active(game_id):
        """Mark game as active."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE games 
                    SET game_status = 'active'
                    WHERE game_id = %s AND game_status = 'pending'
                    """,
                    (game_id,)
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/select-deck", methods=["PUT"])
    def db_select_deck(game_id):
        """Select deck for a player."""
        try:
            data = request.get_json()
            is_player1 = data.get("is_player1")
            deck = data.get("deck")

            with get_cursor() as cursor:
                if is_player1:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player1_deck_cards = %s
                        WHERE game_id = %s
                        """,
                        (json.dumps(deck), game_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player2_deck_cards = %s
                        WHERE game_id = %s
                        """,
                        (json.dumps(deck), game_id)
                    )

                # Check if both players have selected decks
                cursor.execute(
                    """
                    SELECT player1_deck_cards, player2_deck_cards 
                    FROM games WHERE game_id = %s
                    """,
                    (game_id,)
                )
                game = cursor.fetchone()
                both_selected = (
                    game["player1_deck_cards"] is not None and
                    game["player2_deck_cards"] is not None
                )

                if both_selected:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET game_status = 'active'
                        WHERE game_id = %s
                        """,
                        (game_id,)
                    )

            return jsonify({
                "success": True,
                "both_selected": both_selected,
                "status": "active" if both_selected else "deck_selection"
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/tiebreaker-decision", methods=["PUT"])
    def db_tiebreaker_decision(game_id):
        """Submit tiebreaker decision."""
        try:
            data = request.get_json()
            is_player1 = data.get("is_player1")
            decision = data.get("decision")

            with get_cursor() as cursor:
                if is_player1:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player1_tiebreaker_decision = %s
                        WHERE game_id = %s
                        """,
                        (decision, game_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player2_tiebreaker_decision = %s
                        WHERE game_id = %s
                        """,
                        (decision, game_id)
                    )

                # Check if both players made decisions
                cursor.execute(
                    """
                    SELECT player1_tiebreaker_decision, player2_tiebreaker_decision 
                    FROM games WHERE game_id = %s
                    """,
                    (game_id,)
                )
                game = cursor.fetchone()
                both_decided = (
                    game["player1_tiebreaker_decision"] is not None and
                    game["player2_tiebreaker_decision"] is not None
                )

                # If either said no, end game
                if both_decided and (game["player1_tiebreaker_decision"] == "no" or 
                                     game["player2_tiebreaker_decision"] == "no"):
                    cursor.execute(
                        """
                        UPDATE games 
                        SET game_status = 'completed', awaiting_tiebreaker_response = false
                        WHERE game_id = %s
                        """,
                        (game_id,)
                    )
                elif both_decided and game["player1_tiebreaker_decision"] == "yes" and \
                     game["player2_tiebreaker_decision"] == "yes":
                    # Both want tiebreaker
                    cursor.execute(
                        """
                        UPDATE games 
                        SET awaiting_tiebreaker_response = false
                        WHERE game_id = %s
                        """,
                        (game_id,)
                    )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/db/games/<game_id>/tiebreaker-play", methods=["PUT"])
    def db_tiebreaker_play(game_id):
        """Play tiebreaker card."""
        try:
            data = request.get_json()
            is_player1 = data.get("is_player1")
            played_card = data.get("played_card")

            with get_cursor() as cursor:
                if is_player1:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player1_played_card = %s
                        WHERE game_id = %s
                        """,
                        (json.dumps(played_card), game_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE games 
                        SET player2_played_card = %s
                        WHERE game_id = %s
                        """,
                        (json.dumps(played_card), game_id)
                    )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/db/games/<game_id>/archive", methods=["POST"])
    def db_archive_game(game_id):
        """Archive a completed game."""
        try:
            data = request.get_json()
            player1_name = data.get("player1_name")
            player2_name = data.get("player2_name")
            player1_score = data.get("player1_score")
            player2_score = data.get("player2_score")
            winner = data.get("winner")
            encrypted_payload = data.get("encrypted_payload")
            integrity_hash = data.get("integrity_hash")
            round_history = data.get("round_history")

            with get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO game_history 
                    (game_id, player1_name, player2_name, player1_score, 
                     player2_score, winner, archived_at, encrypted_payload,
                     integrity_hash, round_history)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        game_id, player1_name, player2_name, player1_score,
                        player2_score, winner, datetime.utcnow(), encrypted_payload,
                        integrity_hash, json.dumps(round_history)
                    )
                )

                # Update active game to mark as archived
                cursor.execute(
                    """
                    UPDATE games 
                    SET game_status = 'completed'
                    WHERE game_id = %s
                    """,
                    (game_id,)
                )

            return jsonify({"success": True}), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/db/games/log-action", methods=["POST"])
    def db_log_action():
        """Log an action."""
        try:
            data = request.get_json()
            action = data.get("action")
            username = data.get("username")
            details = data.get("details")

            with get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO logs (action, username, details, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (action, username, details, datetime.utcnow())
                )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


# Register game endpoints (must be outside __main__ for gunicorn)
register_game_endpoints(app, get_db_connection)


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5005, debug=debug_mode)