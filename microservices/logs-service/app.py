"""
Logs Service - System logging and monitoring microservice
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Add utils directory to path for input sanitizer
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "utils"))
from input_sanitizer import InputSanitizer, SecurityMiddleware

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

# JWT error handlers
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


DB_MANAGER_URL = os.getenv("DB_MANAGER_URL", "http://db-manager:5005")


def log_action(action: str, username: str = None, details: str = None):
    """Delegate logging to DB Manager (fire-and-forget)."""
    try:
        requests.post(
            f"{DB_MANAGER_URL}/db/logs/create",
            json={
                "action": action,
                "username": username,
                "details": details,
            },
            timeout=3,
        )
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log action: {e}")


def require_admin():
    """Decorator to require admin privileges."""
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user = get_jwt_identity()

            response = requests.get(
                f"{DB_MANAGER_URL}/db/users/is-admin",
                params={"username": current_user},
                timeout=5,
            )

            if response.status_code != 200 or not response.json().get("is_admin"):
                return jsonify({"error": "Admin privileges required"}), 403

            return fn(*args, **kwargs)

        decorator.__name__ = fn.__name__
        return decorator
    return wrapper


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "logs-service"}), 200


@app.route("/api/logs/list", methods=["GET"])
@require_admin()
def list_logs():
    """List all logs with pagination."""
    try:
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 50))

        response = requests.get(
            f"{DB_MANAGER_URL}/db/logs/list",
            params={"page": page, "size": size},
            timeout=5,
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": f"Failed to list logs: {str(e)}"}), 500


@app.route("/api/logs", methods=["POST"])
@app.route("/api/logs/create", methods=["POST"])
@jwt_required()
def create_log():
    """Create a new log entry."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        if not data or "action" not in data:
            return jsonify({"error": "Action is required"}), 400

        action = InputSanitizer.sanitize_string(data["action"])
        details = InputSanitizer.sanitize_string(data.get("details", ""))

        response = requests.post(
            f"{DB_MANAGER_URL}/db/logs/create",
            json={
                "action": action,
                "username": current_user,
                "details": details,
            },
            timeout=5,
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": f"Failed to create log: {str(e)}"}), 500


@app.route("/api/logs/search", methods=["GET"])
@require_admin()
def search_logs():
    """Search logs by action, username, or details."""
    try:
        current_user = get_jwt_identity()
        query = request.args.get("query", "")
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 50))

        response = requests.get(
            f"{DB_MANAGER_URL}/db/logs/search",
            params={
                "query": query,
                "page": page,
                "size": size,
            },
            timeout=5,
        )

        if page == 0:
            log_action(
                "ADMIN_SEARCHED_LOGS",
                current_user,
                f"Searched logs with query: {query}",
            )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": f"Failed to search logs: {str(e)}"}), 500


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host="0.0.0.0", port=5006, debug=debug_mode)
