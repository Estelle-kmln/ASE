"""
Database Manager - Centralized database access for all microservices.
Provides card, game, user, and utility data operations.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, timedelta


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

if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5005, debug=debug_mode)