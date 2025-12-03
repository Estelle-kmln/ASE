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
from dotenv import load_dotenv
from common.db_manager import unit_of_work, db_health, get_connection, release_connection


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


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gameuser:gamepassword@localhost:5432/battlecards",
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(db_health()), 200


@app.route("/api/auth/register", methods=["POST"])
@require_sanitized_input(
    {"username": "username", "password": "password", "email": "email"}
)
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

            # Optional email validation
            email = None
            if "email" in data and data["email"]:
                email = InputSanitizer.validate_email(data["email"])

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
                return jsonify({"error": "Username already exists"}), 409

            # Insert user
            if email:
                cur.execute(
                    """
                    INSERT INTO users (username, password, email)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (username, hashed_password, email),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO users (username, password)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (username, hashed_password),
                )

            user_id = cur.fetchone()["id"]

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
            return jsonify({"error": "Invalid username or password"}), 401

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
                "SELECT id, username, created_at FROM users WHERE username = %s",
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

        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500


@app.route("/api/auth/validate", methods=["POST"])
@jwt_required()
def validate_token():
    """Validate JWT token."""
    try:
        current_user = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE username = %s", (current_user,)
        )
        user_exists = cursor.fetchone()[0] > 0
        conn.close()

        if not user_exists:
            return jsonify({"error": "Invalid token"}), 401

        return jsonify({"valid": True, "username": current_user}), 200

    except Exception as e:
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 500


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host="0.0.0.0", port=5001, debug=debug_mode)
