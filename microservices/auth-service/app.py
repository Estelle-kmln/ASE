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
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
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
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=5)  # Short-lived access tokens
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)  # Long-lived refresh tokens

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
            (action, username, details),
        )
        conn.commit()
        conn.close()
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


def get_device_info() -> dict:
    """Extract device information from request headers."""
    user_agent = request.headers.get('User-Agent', 'Unknown')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Parse user agent for simple device info
    device_info = 'Unknown Device'
    if 'Mobile' in user_agent:
        if 'iPhone' in user_agent or 'iPad' in user_agent:
            device_info = 'iOS Device'
        elif 'Android' in user_agent:
            device_info = 'Android Device'
        else:
            device_info = 'Mobile Device'
    elif 'Windows' in user_agent:
        if 'Edge' in user_agent:
            device_info = 'Edge on Windows'
        elif 'Chrome' in user_agent:
            device_info = 'Chrome on Windows'
        elif 'Firefox' in user_agent:
            device_info = 'Firefox on Windows'
        else:
            device_info = 'Windows Device'
    elif 'Macintosh' in user_agent or 'Mac OS' in user_agent:
        if 'Safari' in user_agent and 'Chrome' not in user_agent:
            device_info = 'Safari on Mac'
        elif 'Chrome' in user_agent:
            device_info = 'Chrome on Mac'
        elif 'Firefox' in user_agent:
            device_info = 'Firefox on Mac'
        else:
            device_info = 'Mac Device'
    elif 'Linux' in user_agent:
        device_info = 'Linux Device'
    
    return {
        'device_info': device_info,
        'ip_address': ip_address,
        'user_agent': user_agent
    }


def get_active_sessions(user_id: int) -> list:
    """Get all active (non-revoked, non-expired) sessions for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First, clean up expired tokens
        cursor.execute(
            """UPDATE refresh_tokens 
               SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP 
               WHERE user_id = %s AND revoked = FALSE AND expires_at <= CURRENT_TIMESTAMP""",
            (user_id,)
        )
        conn.commit()
        
        # Now get active sessions
        cursor.execute(
            """SELECT id, device_info, ip_address, created_at, last_used_at 
               FROM refresh_tokens 
               WHERE user_id = %s AND revoked = FALSE AND expires_at > CURRENT_TIMESTAMP
               ORDER BY created_at DESC""",
            (user_id,)
        )
        sessions = cursor.fetchall()
        conn.close()
        
        print(f"Active sessions for user {user_id}: {len(sessions)}")
        return sessions
    except Exception as e:
        print(f"Failed to get active sessions: {e}")
        return []


def check_concurrent_session(user_id: int) -> bool:
    """Check if user has an active session (strict mode)."""
    sessions = get_active_sessions(user_id)
    return len(sessions) > 0


def store_refresh_token(user_id: int, refresh_token: str, expires_delta: timedelta, device_data: dict = None) -> bool:
    """Store a refresh token in the database with device tracking."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        expires_at = datetime.now() + expires_delta
        
        # Get device info if not provided
        if device_data is None:
            device_data = get_device_info()
        
        cursor.execute(
            """INSERT INTO refresh_tokens 
               (user_id, token, expires_at, device_info, ip_address, user_agent, last_used_at) 
               VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
            (user_id, refresh_token, expires_at, 
             device_data.get('device_info', 'Unknown'),
             device_data.get('ip_address', 'Unknown'),
             device_data.get('user_agent', 'Unknown'))
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Failed to store refresh token: {e}")
        return False


def validate_refresh_token(refresh_token: str) -> dict:
    """Validate a refresh token and return user info if valid."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked, u.username 
               FROM refresh_tokens rt
               JOIN users u ON rt.user_id = u.id
               WHERE rt.token = %s""",
            (refresh_token,)
        )
        token_data = cursor.fetchone()
        
        if not token_data:
            conn.close()
            return None
        
        if token_data["revoked"]:
            conn.close()
            return None
        
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


def revoke_refresh_token(refresh_token: str) -> bool:
    """Revoke a refresh token."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP WHERE token = %s",
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


def revoke_all_user_tokens(user_id: int) -> bool:
    """Revoke all refresh tokens for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP WHERE user_id = %s AND revoked = FALSE",
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


@app.route("/health", methods=["GET"])
@app.route("/api/auth/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "auth-service"}), 200


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

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE username = %s", (username,)
        )
        if cursor.fetchone()[0] > 0:
            conn.close()
            # Log failed registration attempt
            log_action(
                "REGISTRATION_FAILED", username, "Username already exists"
            )
            return jsonify({"error": "Username already exists"}), 409

        # Hash password and create user
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, hashed_password),
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        # Log the registration
        log_action(
            "USER_REGISTERED",
            username,
            f"New user registered with ID: {user_id}",
        )

        # Create access token and refresh token
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        
        # Store refresh token in database
        refresh_expires = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        store_refresh_token(user_id, refresh_token, refresh_expires)
        
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
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": expires_in,
                    "user": {"id": user_id, "username": username},
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@app.route("/api/auth/force-logout", methods=["POST"])
def force_logout():
    """Force logout all sessions for a user after password verification."""
    try:
        log_action("FORCE_LOGOUT_ATTEMPT", None, "Force logout endpoint called")
        data = request.get_json()
        
        log_action("FORCE_LOGOUT_DEBUG", None, f"Data received: {data is not None}")

        if not data:
            log_action("FORCE_LOGOUT_ERROR", None, "No request body provided")
            return jsonify({"error": "Request body is required"}), 400

        # Validate required fields
        if not data.get("username") or not data.get("password"):
            log_action("FORCE_LOGOUT_ERROR", None, "Missing username or password")
            return jsonify({"error": "Username and password are required"}), 400

        # Sanitize and validate inputs
        try:
            username = InputSanitizer.validate_username(data["username"])
            password = InputSanitizer.validate_password(data["password"])
            log_action("FORCE_LOGOUT_DEBUG", username, "Input validation passed")
        except ValueError as e:
            log_action("FORCE_LOGOUT_ERROR", None, f"Validation error: {str(e)}")
            return jsonify({"error": str(e)}), 400

        # Get user and verify password
        log_action("FORCE_LOGOUT_DEBUG", username, "Getting user from database")
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """SELECT id, username, password 
               FROM users WHERE username = %s""",
            (username,),
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            log_action("FORCE_LOGOUT_FAILED", username, "User not found")
            return jsonify({"error": "Invalid username or password"}), 401

        log_action("FORCE_LOGOUT_DEBUG", username, "User found, verifying password")
        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            conn.close()
            log_action("FORCE_LOGOUT_FAILED", username, "Invalid password")
            return jsonify({"error": "Invalid username or password"}), 401

        conn.close()

        log_action("FORCE_LOGOUT_DEBUG", username, "Password verified, revoking tokens")
        # Revoke all sessions
        success = revoke_all_user_tokens(user["id"])
        
        if success:
            log_action("FORCE_LOGOUT", username, "All sessions forcefully terminated")
            return jsonify({"message": "All sessions have been terminated. You can now login again."}), 200
        else:
            log_action("FORCE_LOGOUT_ERROR", username, "Failed to revoke tokens")
            return jsonify({"error": "Failed to terminate sessions"}), 500

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        log_action("FORCE_LOGOUT_EXCEPTION", None, f"Exception: {str(e)} - {error_details}")
        return jsonify({"error": "An error occurred during force logout"}), 500


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

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get user from database with lockout information
        cursor.execute(
            """SELECT id, username, password, failed_login_attempts, 
                      account_locked_until, last_failed_login 
               FROM users WHERE username = %s""",
            (username,),
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            # Log failed login attempt (user not found)
            log_action("LOGIN_FAILED", username, "User not found")
            return jsonify({"error": "Invalid username or password"}), 401

        # Check if account is locked
        if user.get("account_locked_until"):
            if user["account_locked_until"] > datetime.now():
                # Account is still locked
                locked_until = user["account_locked_until"].isoformat()
                remaining_seconds = int((user["account_locked_until"] - datetime.now()).total_seconds())
                conn.close()
                log_action("LOGIN_BLOCKED", username, f"Account locked until {locked_until}")
                return jsonify({
                    "error": "Account is temporarily locked due to multiple failed login attempts",
                    "locked_until": locked_until,
                    "retry_after": remaining_seconds
                }), 423  # 423 Locked status code
            else:
                # Lock period expired, reset the lockout
                cursor.execute(
                    """UPDATE users 
                       SET failed_login_attempts = 0, 
                           account_locked_until = NULL 
                       WHERE username = %s""",
                    (username,)
                )
                conn.commit()

        # Verify password
        if not verify_password(password, user["password"]):
            # Increment failed login attempts
            failed_attempts = (user.get("failed_login_attempts") or 0) + 1
            
            # Lock account after 3 failed attempts (15 minutes lockout)
            if failed_attempts >= 3:
                lockout_duration = timedelta(minutes=15)
                locked_until = datetime.now() + lockout_duration
                cursor.execute(
                    """UPDATE users 
                       SET failed_login_attempts = %s, 
                           account_locked_until = %s,
                           last_failed_login = CURRENT_TIMESTAMP
                       WHERE username = %s""",
                    (failed_attempts, locked_until, username)
                )
                conn.commit()
                conn.close()
                log_action("ACCOUNT_LOCKED", username, 
                          f"Account locked after {failed_attempts} failed attempts until {locked_until.isoformat()}")
                return jsonify({
                    "error": "Account locked due to multiple failed login attempts",
                    "locked_until": locked_until.isoformat(),
                    "retry_after": int(lockout_duration.total_seconds())
                }), 423
            else:
                # Update failed attempts count
                cursor.execute(
                    """UPDATE users 
                       SET failed_login_attempts = %s,
                           last_failed_login = CURRENT_TIMESTAMP
                       WHERE username = %s""",
                    (failed_attempts, username)
                )
                conn.commit()
                conn.close()
                log_action("LOGIN_FAILED", username, 
                          f"Invalid password - attempt {failed_attempts} of 3")
                return jsonify({
                    "error": "Invalid username or password",
                    "remaining_attempts": 3 - failed_attempts
                }), 401

        # Successful login - reset failed attempts
        cursor.execute(
            """UPDATE users 
               SET failed_login_attempts = 0, 
                   account_locked_until = NULL,
                   last_failed_login = NULL
               WHERE username = %s""",
            (username,)
        )
        conn.commit()

        # STRICT MODE: Check for concurrent sessions
        if check_concurrent_session(user["id"]):
            # Get active session info for the error message
            active_sessions = get_active_sessions(user["id"])
            session_info = active_sessions[0] if active_sessions else {}
            
            conn.close()
            log_action("LOGIN_REJECTED", username, 
                      f"Concurrent session detected - active session from {session_info.get('device_info', 'Unknown Device')}")
            
            return jsonify({
                "error": "Another session is already active",
                "message": "You already have an active session. Please logout from your other device first.",
                "active_session": {
                    "device": session_info.get('device_info', 'Unknown Device'),
                    "ip_address": session_info.get('ip_address', 'Unknown'),
                    "created_at": session_info.get('created_at').isoformat() if session_info.get('created_at') else None
                }
            }), 409  # 409 Conflict
        
        conn.close()

        # Log successful login
        log_action("USER_LOGIN", username, f"User logged in successfully from {get_device_info()['device_info']}")

        # Create access token and refresh token
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        
        # Store refresh token in database with device tracking
        refresh_expires = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        store_refresh_token(user["id"], refresh_token, refresh_expires)
        
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
                    "refresh_token": refresh_token,
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

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id, username, is_admin, created_at FROM users WHERE username = %s",
            (current_user,),
        )
        user = cursor.fetchone()
        conn.close()

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

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if user exists and get user data
        cursor.execute(
            "SELECT id, username, created_at, is_admin FROM users WHERE username = %s", (current_user,)
        )
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404

        # Track if any updates were made
        updates_made = []
        
        # Update username if provided and different from current
        if "username" in data and data["username"] and data["username"] != current_user:
            new_username = data["username"]
            
            # Validate username
            try:
                new_username = InputSanitizer.validate_username(new_username)
            except ValueError as e:
                conn.close()
                return jsonify({"error": str(e)}), 400
            
            # Check if new username already exists
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE username = %s AND username != %s",
                (new_username, current_user),
            )
            if cursor.fetchone()["count"] > 0:
                conn.close()
                return jsonify({"error": "Username already exists"}), 400
            
            # Update username
            cursor.execute(
                "UPDATE users SET username = %s WHERE username = %s",
                (new_username, current_user),
            )
            updates_made.append(f"username changed from '{current_user}' to '{new_username}'")
            
            # Update the current_user variable for subsequent operations
            old_username = current_user
            current_user = new_username
            
            # Log username change
            log_action(
                "USERNAME_CHANGED", new_username, f"Username changed from '{old_username}' to '{new_username}'"
            )

        # Update password if provided
        if "password" in data and data["password"]:
            try:
                new_password = InputSanitizer.validate_password(
                    data["password"]
                )
            except ValueError as e:
                conn.close()
                return jsonify({"error": str(e)}), 400

            hashed_password = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password = %s WHERE username = %s",
                (hashed_password, current_user),
            )
            updates_made.append("password")
            # Log password change
            log_action(
                "PASSWORD_CHANGED", current_user, "User changed their password"
            )

        conn.commit()
        
        # Fetch updated user data to return
        cursor.execute(
            "SELECT id, username, created_at, is_admin FROM users WHERE username = %s",
            (current_user,)
        )
        updated_user = cursor.fetchone()
        user_id = updated_user['id']
        conn.close()

        # Generate new tokens if username was changed
        response_data = {
            "message": "Profile updated successfully",
            "user": dict(updated_user)
        }
        
        if "username" in data and data["username"] and data["username"] != get_jwt_identity():
            # Username was changed, generate new tokens
            access_token = create_access_token(identity=current_user)
            refresh_token = create_refresh_token(identity=current_user)
            
            # Store new refresh token in database
            refresh_expires = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
            store_refresh_token(user_id, refresh_token, refresh_expires)
            
            # OAuth2-style metadata
            jwt_expires = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
            expires_in = (
                int(jwt_expires.total_seconds())
                if hasattr(jwt_expires, "total_seconds")
                else int(jwt_expires)
            )
            
            response_data["access_token"] = access_token
            response_data["refresh_token"] = refresh_token
            response_data["token_type"] = "bearer"
            response_data["expires_in"] = expires_in

        return jsonify(response_data), 200

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


@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token."""
    try:
        data = request.get_json()
        
        if not data or not data.get("refresh_token"):
            return jsonify({"error": "Refresh token is required"}), 400
        
        refresh_token = data["refresh_token"]
        
        # Validate refresh token
        token_data = validate_refresh_token(refresh_token)
        
        if not token_data:
            log_action("TOKEN_REFRESH_FAILED", None, "Invalid or expired refresh token")
            return jsonify({"error": "Invalid or expired refresh token"}), 401
        
        username = token_data["username"]
        
        # Create new access token
        access_token = create_access_token(identity=username)
        
        # Log token refresh
        log_action("TOKEN_REFRESHED", username, "Access token refreshed successfully")
        
        jwt_expires = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        expires_in = (
            int(jwt_expires.total_seconds())
            if hasattr(jwt_expires, "total_seconds")
            else int(jwt_expires)
        )
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500


@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    """Logout user and revoke refresh token."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user_id = user[0]
        
        if data.get("refresh_token"):
            # Revoke specific refresh token
            refresh_token = data["refresh_token"]
            success = revoke_refresh_token(refresh_token)
            log_action("USER_LOGOUT", current_user, f"User logged out - specific token revoked (success: {success})")
        else:
            # Revoke all refresh tokens for this user
            success = revoke_all_user_tokens(user_id)
            log_action("USER_LOGOUT", current_user, f"User logged out - all tokens revoked (success: {success})")
        
        return jsonify({"message": "Logged out successfully"}), 200
        
    except Exception as e:
        log_action("LOGOUT_ERROR", current_user if 'current_user' in locals() else None, f"Logout failed: {str(e)}")
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@app.route("/api/auth/sessions", methods=["GET"])
@jwt_required()
def get_sessions():
    """Get all active sessions for the current user."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        sessions = get_active_sessions(user["id"])
        
        # Format sessions for response
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "id": session["id"],
                "device": session.get("device_info", "Unknown Device"),
                "ip_address": session.get("ip_address", "Unknown"),
                "created_at": session["created_at"].isoformat() if session.get("created_at") else None,
                "last_used_at": session["last_used_at"].isoformat() if session.get("last_used_at") else None
            })
        
        return jsonify({
            "sessions": formatted_sessions,
            "total": len(formatted_sessions)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get sessions: {str(e)}"}), 500


@app.route("/api/auth/sessions/<int:session_id>", methods=["DELETE"])
@jwt_required()
def revoke_session(session_id):
    """Revoke a specific session by ID."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Verify the session belongs to this user
        cursor.execute(
            "SELECT id, user_id FROM refresh_tokens WHERE id = %s",
            (session_id,)
        )
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            return jsonify({"error": "Session not found"}), 404
        
        if session["user_id"] != user["id"]:
            conn.close()
            log_action("UNAUTHORIZED_SESSION_REVOKE", current_user, 
                      f"Attempted to revoke session {session_id} belonging to another user")
            return jsonify({"error": "Unauthorized"}), 403
        
        # Revoke the session
        cursor.execute(
            "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP WHERE id = %s",
            (session_id,)
        )
        conn.commit()
        conn.close()
        
        log_action("SESSION_REVOKED", current_user, f"User revoked session {session_id}")
        
        return jsonify({"message": "Session revoked successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to revoke session: {str(e)}"}), 500


@app.route("/api/auth/sessions/revoke-all", methods=["POST"])
@jwt_required()
def revoke_all_sessions():
    """Revoke all sessions for the current user (except the current one if specified)."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Revoke all tokens
        revoke_all_user_tokens(user["id"])
        
        log_action("ALL_SESSIONS_REVOKED", current_user, "User revoked all sessions")
        
        return jsonify({"message": "All sessions revoked successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to revoke all sessions: {str(e)}"}), 500


# Admin-only endpoints
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
                (current_user,),
            )
            user = cursor.fetchone()
            conn.close()

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

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total = cursor.fetchone()["count"]

        # Get paginated users
        cursor.execute(
            """SELECT id, username, is_admin, created_at 
               FROM users 
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (size, offset),
        )
        users = cursor.fetchall()
        conn.close()

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

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        search_pattern = f"%{query}%"

        # Get total count
        cursor.execute(
            "SELECT COUNT(*) as count FROM users WHERE username ILIKE %s",
            (search_pattern,),
        )
        total = cursor.fetchone()["count"]

        # Get paginated results
        cursor.execute(
            """SELECT id, username, is_admin, created_at 
               FROM users 
               WHERE username ILIKE %s
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (search_pattern, size, offset),
        )
        users = cursor.fetchall()
        conn.close()

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
