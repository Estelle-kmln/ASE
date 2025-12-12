"""
Logs Service - System logging and monitoring microservice
"""

import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

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


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gameuser:gamepassword@localhost:5432/battlecards",
)


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(DATABASE_URL)


def log_action(action: str, username: str = None, details: str = None):
    """Log an action to the logs table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (action, username, details) VALUES (%s, %s, %s)",
            (action, username, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Failed to log action: {e}")


def require_admin():
    """Decorator to require admin privileges."""
    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user = get_jwt_identity()
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT is_admin FROM users WHERE username = %s",
                (current_user,)
            )
            user = cursor.fetchone()
            conn.close()
            
            if not user or not user.get("is_admin"):
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
        current_user = get_jwt_identity()
        page = int(request.args.get("page", 0))
        size = int(request.args.get("size", 50))
        offset = page * size
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM logs")
        total = cursor.fetchone()["count"]
        
        # Get paginated logs
        cursor.execute(
            """SELECT id, action, username, timestamp, details 
               FROM logs 
               ORDER BY timestamp DESC 
               LIMIT %s OFFSET %s""",
            (size, offset)
        )
        logs = cursor.fetchall()
        conn.close()
        
        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log["id"],
                "action": log["action"],
                "username": log.get("username"),
                "timestamp": log["timestamp"].isoformat() if log["timestamp"] else None,
                "details": log.get("details")
            })
        
        return jsonify(formatted_logs), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to list logs: {str(e)}"}), 500


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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO logs (action, username, details) VALUES (%s, %s, %s) RETURNING id",
            (action, current_user, details)
        )
        log_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Log created successfully", "id": log_id}), 201
        
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
        offset = page * size
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        search_pattern = f"%{query}%"
        
        # Get total count
        cursor.execute(
            """SELECT COUNT(*) as count FROM logs 
               WHERE action ILIKE %s OR username ILIKE %s OR details ILIKE %s""",
            (search_pattern, search_pattern, search_pattern)
        )
        total = cursor.fetchone()["count"]
        
        # Get paginated results
        cursor.execute(
            """SELECT id, action, username, timestamp, details 
               FROM logs 
               WHERE action ILIKE %s OR username ILIKE %s OR details ILIKE %s
               ORDER BY timestamp DESC 
               LIMIT %s OFFSET %s""",
            (search_pattern, search_pattern, search_pattern, size, offset)
        )
        logs = cursor.fetchall()
        conn.close()
        
        # Log admin searching logs
        if page == 0:  # Only log the first page search to avoid too many entries
            log_action("ADMIN_SEARCHED_LOGS", current_user, f"Searched logs with query: {query}")
        
        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log["id"],
                "action": log["action"],
                "username": log.get("username"),
                "timestamp": log["timestamp"].isoformat() if log["timestamp"] else None,
                "details": log.get("details")
            })
        
        return jsonify(formatted_logs), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to search logs: {str(e)}"}), 500


if __name__ == "__main__":
    # For development only - debug mode controlled by environment variable
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host="0.0.0.0", port=5006, debug=debug_mode)
