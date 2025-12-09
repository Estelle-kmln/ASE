"""
Auth Service - User authentication and profile management microservice
"""

import os
import sys
import bcrypt
from datetime import timedelta, datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_cors import CORS
from common.db_manager import unit_of_work, db_health
from dotenv import load_dotenv


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
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

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


# Database configuration - kept for reference but not used directly anymore
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gameuser:gamepassword@localhost:5432/battlecards",
)


def log_action(action: str, username: str = None, details: str = None):
    """Log an action to the logs table using db_manager."""
    try:
        with unit_of_work() as cur:
            cur.execute(
                "INSERT INTO logs (action, username, details) VALUES (%s, %s, %s)",
                (action, username, details),
            )
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log action: {e}")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@app.route("/health", methods=["GET"])
@app.route("/api/auth/health", methods=["GET"])
def health_check():
    return jsonify(db_health()), 200


@app.route("/api/auth/register", methods=["POST"])
@require_sanitized_input({"username": "username", "password": "password"})
def register():
    """Register a new user."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        # Sanitize and validate inputs
        try:
            username = InputSanitizer.validate_username(data["username"])
            password = InputSanitizer.validate_password(data["password"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        hashed_password = hash_password(password)

        with unit_of_work() as cur:
            # Check if username exists
            cur.execute(
                "SELECT COUNT(*) AS count FROM users WHERE username = %s",
                (username,),
            )
            if cur.fetchone()["count"] > 0:
                # Log failed registration attempt
                log_action(
                    "REGISTRATION_FAILED", username, "Username already exists"
                )
                return jsonify({"error": "Username already exists"}), 409

            # Insert user
            cur.execute(
                """
                INSERT INTO users (username, password)
                VALUES (%s, %s)
                RETURNING id
                """,
                (username, hashed_password),
            )
            user_id = cur.fetchone()["id"]

        # Log the registration
        log_action(
            "USER_REGISTERED",
            username,
            f"New user registered with ID: {user_id}",
        )

        # Create access token (JWT bearer token)
        access_token = create_access_token(identity=username)
        # OAuth2-style metadata (support timedelta or numeric seconds)
        jwt_expires = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        expires_in = (
            int(jwt_expires.total_seconds())
            if hasattr(jwt_expires, "total_seconds")
            else int(jwt_expires)
        )

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": expires_in,
                    "user": {"id": user_id, "username": username},
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500



@app.route("/api/auth/login", methods=["POST"])
@require_sanitized_input({"username": "username", "password": "password"})
def login():
    """Authenticate user and return JWT token."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        # Sanitize and validate inputs
        try:
            username = InputSanitizer.validate_username(data["username"])
            password = InputSanitizer.validate_password(data["password"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Get user from database
        with unit_of_work() as cur:
            cur.execute(
                "SELECT id, username, password FROM users WHERE username = %s",
                (username,),
            )
            user = cur.fetchone()
        

        if not user or not verify_password(password, user["password"]):
            # Log failed login attempt
            log_action("LOGIN_FAILED", username, "Invalid username or password")
            return jsonify({"error": "Invalid username or password"}), 401

        # Log successful login
        log_action("USER_LOGIN", username, "User logged in successfully")

        # Create access token (JWT bearer token)
        access_token = create_access_token(identity=username)
        # OAuth2-style metadata (support timedelta or numeric seconds)
        jwt_expires = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        expires_in = (
            int(jwt_expires.total_seconds())
            if hasattr(jwt_expires, "total_seconds")
            else int(jwt_expires)
        )

        return (
            jsonify(
                {
                    "message": "Login successful",
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": expires_in,
                    "user": {"id": user["id"], "username": user["username"]},
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@app.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get user profile."""
    try:
        current_user = get_jwt_identity()

        with unit_of_work() as cur:
            cur.execute(
                "SELECT id, username, is_admin, created_at FROM users WHERE username = %s",
                (current_user,),
            )
            user = cur.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return (
            jsonify(
                {
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "is_admin": user.get("is_admin", False),
                        "enabled": user.get("enabled", True),
                        "created_at": (
                            user["created_at"].isoformat()
                            if user["created_at"]
                            else None
                        ),
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500


@app.route("/api/auth/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update user profile."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        with unit_of_work() as cur:
            # Check if user exists
            cur.execute(
                "SELECT COUNT(*) AS count FROM users WHERE username = %s",
                (current_user,)
            )
            if cur.fetchone()["count"] == 0:
                return jsonify({"error": "User not found"}), 404

            # Update password if provided
            if "password" in data and data["password"]:
                try:
                    new_password = InputSanitizer.validate_password(data["password"])
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400

                hashed = hash_password(new_password)
                cur.execute(
                    "UPDATE users SET password = %s WHERE username = %s",
                    (hashed, current_user)
                )
                
                # Log password change
                log_action(
                    "PASSWORD_CHANGED", current_user, "User changed their password"
                )

        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500


@app.route("/api/auth/validate", methods=["POST"])
@jwt_required()
def validate_token():
    """Validate JWT token."""
    try:
        current_user = get_jwt_identity()

        with unit_of_work() as cur:
            cur.execute(
                "SELECT COUNT(*) AS count FROM users WHERE username = %s",
                (current_user,)
            )
            user_exists = cur.fetchone()["count"] > 0

        if not user_exists:
            return jsonify({"error": "Invalid token"}), 401

        return jsonify({"valid": True, "username": current_user}), 200

    except Exception as e:
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 500


# Admin-only endpoints
def require_admin():
    """Decorator to require admin privileges."""

    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user = get_jwt_identity()

            with unit_of_work() as cur:
                cur.execute(
                    "SELECT is_admin FROM users WHERE username = %s",
                    (current_user,),
                )
                user = cur.fetchone()

            if not user or not user.get("is_admin"):
                # Log unauthorized admin access attempt
                log_action(
                    "UNAUTHORIZED_ADMIN_ACCESS",
                    current_user,
                    f"Attempted to access admin endpoint: {fn.__name__}",
                )
                return jsonify({"error": "Admin privileges required"}), 403

            return fn(*args, **kwargs)

        decorator.__name__ = fn.__name__
        return decorator

    return wrapper


@app.route("/api/admin/users", methods=["GET"])
@require_admin()
def list_users():
    """List all users with pagination."""
    try:
        current_user = get_jwt_identity()
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 10))
        offset = page * size

        with unit_of_work() as cur:
            # Get total count
            cur.execute("SELECT COUNT(*) as count FROM users")
            total = cur.fetchone()["count"]

            # Get paginated users
            cur.execute(
                """SELECT id, username, is_admin, created_at 
                   FROM users 
                   ORDER BY created_at DESC 
                   LIMIT %s OFFSET %s""",
                (size, offset),
            )
            users = cur.fetchall()

        # Format users
        formatted_users = []
        for user in users:
            formatted_users.append(
                {
                    "id": user["id"],
                    "username": user["username"],
                    "roles": [
                        "ROLE_ADMIN" if user.get("is_admin") else "ROLE_USER"
                    ],
                    "created_at": (
                        user["created_at"].isoformat()
                        if user["created_at"]
                        else None
                    ),
                }
            )

        return (
            jsonify(
                {
                    "content": formatted_users,
                    "totalPages": (total + size - 1) // size,
                    "totalElements": total,
                    "number": page,
                    "size": size,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to list users: {str(e)}"}), 500


@app.route("/api/admin/users/search", methods=["GET"])
@require_admin()
def search_users():
    """Search users by username."""
    try:
        current_user = get_jwt_identity()
        query = request.args.get("query", "")
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 10))
        offset = page * size

        with unit_of_work() as cur:
            search_pattern = f"%{query}%"

            # Get total count
            cur.execute(
                "SELECT COUNT(*) as count FROM users WHERE username ILIKE %s",
                (search_pattern,),
            )
            total = cur.fetchone()["count"]

            # Get paginated results
            cur.execute(
                """SELECT id, username, is_admin, created_at 
                   FROM users 
                   WHERE username ILIKE %s
                   ORDER BY created_at DESC 
                   LIMIT %s OFFSET %s""",
                (search_pattern, size, offset),
            )
            users = cur.fetchall()

        # Format users
        formatted_users = []
        for user in users:
            formatted_users.append(
                {
                    "id": user["id"],
                    "username": user["username"],
                    "roles": [
                        "ROLE_ADMIN" if user.get("is_admin") else "ROLE_USER"
                    ],
                    "created_at": (
                        user["created_at"].isoformat()
                        if user["created_at"]
                        else None
                    ),
                }
            )

        return (
            jsonify(
                {
                    "content": formatted_users,
                    "totalPages": (total + size - 1) // size,
                    "totalElements": total,
                    "number": page,
                    "size": size,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to search users: {str(e)}"}), 500


@app.route("/api/admin/roles", methods=["GET"])
@require_admin()
def list_roles():
    """List available roles."""
    return (
        jsonify(
            [
                {"id": "ROLE_USER", "name": "User"},
                {"id": "ROLE_ADMIN", "name": "Administrator"},
            ]
        ),
        200,
    )


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
