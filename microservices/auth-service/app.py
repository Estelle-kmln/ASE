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

# Database manager
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
        response = requests.get(f"{DB_MANAGER_URL}/tokens/active/{user_id}", timeout=5)

        if response.status_code != 200:
            print("DB Manager returned error:", response.text)
            return []
        
        data = response.json()
        sessions = data.get("sessions", [])

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
        payload = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "expires_delta": expires_delta.total_seconds(),
            "device_data": device_data or get_device_info()
        }

        response = requests.post(f"{DB_MANAGER_URL}/tokens/store", json=payload, timeout=5)

        if response.status_code == 200:
            return True
        else:
            print("DB Manager error:", response.text)
            return False

    except Exception as e:
        print(f"Failed to store refresh token: {e}")
        return False


def validate_refresh_token(refresh_token: str) -> dict:
    """Validate a refresh token and return user info if valid."""
    try:
        response = requests.post(
            f"{DB_MANAGER_URL}/tokens/validate",
            json={"refresh_token": refresh_token},
            timeout=5
        )

        if response.status_code != 200:
            print("DB Manager returned error:", response.text)
            return None

        data = response.json()
        token_data = data.get("token_data")

        return token_data
    
    except Exception as e:
        print(f"Failed to validate refresh token: {e}")
        return None


def revoke_refresh_token(refresh_token: str) -> bool:
    """Revoke a refresh token."""
    try:
        response = requests.post(
            f"{DB_MANAGER_URL}/tokens/revoke",
            json={"refresh_token": refresh_token},
            timeout=5
        )

        if response.status_code != 200:
            print("DB Manager returned error:", response.text)
            return False

        data = response.json()
        return data.get("success", False)
    
    except Exception as e:
        print(f"Failed to revoke refresh token: {e}")
        return False


def revoke_all_user_tokens(user_id: int) -> bool:
    """Revoke all refresh tokens for a user."""
    try:
        response = requests.post(
            f"{DB_MANAGER_URL}/tokens/revoke_all",
            json={"user_id": user_id},
            timeout=5
        )

        if response.status_code != 200:
            print("DB Manager returned error:", response.text)
            return False

        data = response.json()
        return data.get("success", False)
    
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

        # Check if username already exists
        exists_response = requests.get(
            f"{DB_MANAGER_URL}/users/exists/{username}", timeout=5
        )

        if exists_response.status_code != 200:
            return jsonify({"error": "DB Manager error"}), 500

        if exists_response.json().get("exists"):
            log_action("REGISTRATION_FAILED", username, "Username already exists")
            return jsonify({"error": "Username already exists"}), 409
        
        # Hash password and create user
        hashed_password = hash_password(password)
        
        create_response = requests.post(
            f"{DB_MANAGER_URL}/users/create",
            json={"username": username, "password": hashed_password},
            timeout=5
        )

        if create_response.status_code != 201:
            return jsonify({"error": "Failed to create user"}), 500

        user_id = create_response.json().get("user_id")

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
        user_response = requests.get(
            f"{DB_MANAGER_URL}/users/{username}",
            timeout=5
        )

        if user_response.status_code != 200:
            log_action("FORCE_LOGOUT_FAILED", username, "User not found")
            return jsonify({"error": "Invalid username or password"}), 401

        user = user_response.json().get("user")

        if not user:
            return jsonify({"error": "Invalid username or password"}), 401
        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            log_action("FORCE_LOGOUT_FAILED", username, "Invalid password")
            return jsonify({"error": "Invalid username or password"}), 401
        # Revoke all sessions
        success = revoke_all_user_tokens(user["id"])

        if success:
            log_action("FORCE_LOGOUT", username, "All sessions forcefully terminated")
            return jsonify({
                "message": "All sessions have been terminated. You can now login again."
            }), 200
        
        else:
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

        # Get username
        user_response = requests.get(
            f"{DB_MANAGER_URL}/auth/user/{username}",
            timeout=5
        )
        
        if user_response.status_code != 200:
            log_action("LOGIN_FAILED", username, "User not found")
            return jsonify({"error": "Invalid username or password"}), 401

        user = user_response.json().get("user")
        if not user:
            log_action("LOGIN_FAILED", username, "User not found")
            return jsonify({"error": "Invalid username or password"}), 401

        # Check lockout
        if user.get("account_locked_until"):
            locked_until = datetime.fromisoformat(user["account_locked_until"])

            if locked_until > datetime.now():
                remaining = int((locked_until - datetime.now()).total_seconds())
                log_action("LOGIN_BLOCKED", username, f"Locked until {locked_until}")

                return jsonify({
                    "error": "Account is temporarily locked",
                    "locked_until": locked_until.isoformat(),
                    "retry_after": remaining
                }), 423
            
            # Lock expired, reset it
            requests.post(f"{DB_MANAGER_URL}/auth/reset_failures",
                          json={"username": username})

        # Verify password
        if not verify_password(password, user["password"]):
            failed_attempts = (user.get("failed_login_attempts") or 0) + 1

            # If reached 3 attempts locks account
            if failed_attempts >= 3:
                lockout_minutes = 15
                requests.post(f"{DB_MANAGER_URL}/auth/lock",
                              json={
                                  "username": username,
                                  "failed_attempts": failed_attempts,
                                  "lock_minutes": lockout_minutes
                              })

                log_action("ACCOUNT_LOCKED", username,
                           f"Locked after {failed_attempts} failed attempts")

                return jsonify({
                    "error": "Account locked due to multiple failed attempts",
                    "locked_until": (datetime.now() + timedelta(minutes=lockout_minutes)).isoformat(),
                    "retry_after": lockout_minutes * 60
                }), 423

            # Less than 3 mean just increment attempts
            requests.post(
                f"{DB_MANAGER_URL}/auth/fail_attempt",
                json={"username": username, "failed_attempts": failed_attempts}
            )

            log_action("LOGIN_FAILED", username,
                       f"Invalid password - attempt {failed_attempts} of 3")

            return jsonify({
                "error": "Invalid username or password",
                "remaining_attempts": 3 - failed_attempts
            }), 401

        # Succesfull login restarts attempts
        requests.post(
            f"{DB_MANAGER_URL}/auth/reset_failures",
            json={"username": username}
        )

        # Strict mode (active session check)
        user_id = user["id"]

        if check_concurrent_session(user_id):
            active_sessions = get_active_sessions(user_id)
            session_info = active_sessions[0] if active_sessions else {}

            log_action("LOGIN_REJECTED", username,
                       f"Concurrent session from {session_info.get('device_info','Unknown')}")

            return jsonify({
                "error": "Another session is already active",
                "active_session": session_info
            }), 409

        # Successfull login
        log_action("USER_LOGIN", username,
                   f"User logged in successfully from {get_device_info()['device_info']}")

        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)

        refresh_expires = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
        store_refresh_token(user_id, refresh_token, refresh_expires)

        jwt_expires = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        expires_in = (
            int(jwt_expires.total_seconds())
            if hasattr(jwt_expires, "total_seconds")
            else int(jwt_expires)
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {"id": user_id, "username": user["username"]},
        }), 200

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@app.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get user profile."""
    try:
        # Get logged-in identity from JWT
        current_user = get_jwt_identity()

        # Request user profile from DB Manager
        response = requests.get(
            f"{DB_MANAGER_URL}/auth/profile/{current_user}",
            timeout=5
        )

        if response.status_code == 404:
            return jsonify({"error": "User not found"}), 404

        if response.status_code != 200:
            return jsonify({"error": "DB Manager error"}), 500

        data = response.json()
        user = data.get("user")

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Return profile in same format as original version
        return (
            jsonify(
                {
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "is_admin": user.get("is_admin", False),
                        "created_at": user.get("created_at"),
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

        # Get user
        user_response = requests.get(
            f"{DB_MANAGER_URL}/auth/user/{current_user}",
            timeout=5
        )

        if user_response.status_code != 200:
            return jsonify({"error": "User not found"}), 404

        user = user_response.json().get("user")
        if not user:
            return jsonify({"error": "User not found"}), 404

        updates_made = []
        old_username = current_user

        # Update username
        if "username" in data and data["username"] and data["username"] != current_user:
            new_username = data["username"]

            # Validate username
            try:
                new_username = InputSanitizer.validate_username(new_username)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            # Call DB Manager to update username
            update_resp = requests.post(
                f"{DB_MANAGER_URL}/auth/update_username",
                json={"old_username": current_user, "new_username": new_username},
                timeout=5
            )

            if update_resp.status_code != 200:
                return jsonify({"error": update_resp.json().get("error", "Failed to update username")}), 400

            updates_made.append(f"username changed from '{current_user}' to '{new_username}'")

            # Update identity for remaining logic
            current_user = new_username

            # Log username change
            log_action(
                "USERNAME_CHANGED",
                new_username,
                f"Username changed from '{old_username}' to '{new_username}'"
            )

        # Update password
        if "password" in data and data["password"]:
            try:
                new_password = InputSanitizer.validate_password(data["password"])
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            hashed_password = hash_password(new_password)

            # Call DB Manager
            pw_resp = requests.post(
                f"{DB_MANAGER_URL}/auth/update_password",
                json={"username": current_user, "hashed_password": hashed_password},
                timeout=5
            )

            if pw_resp.status_code != 200:
                return jsonify({"error": "Failed to update password"}), 500

            updates_made.append("password")

            # Log password change
            log_action(
                "PASSWORD_CHANGED",
                current_user,
                "User changed their password"
            )

        # Refresh updated user data
        updated_user_resp = requests.get(
            f"{DB_MANAGER_URL}/auth/user/{current_user}",
            timeout=5
        )

        updated_user = updated_user_resp.json().get("user")
        user_id = updated_user["id"]

        # If username changed - generate new tokens
        response_data = {
            "message": "Profile updated successfully",
            "user": updated_user
        }

        if old_username != current_user:
            access_token = create_access_token(identity=current_user)
            refresh_token = create_refresh_token(identity=current_user)

            refresh_expires = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
            store_refresh_token(user_id, refresh_token, refresh_expires)

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
        # Extract identity from token
        current_user = get_jwt_identity()

        # Check if user exists
        response = requests.get(
            f"{DB_MANAGER_URL}/auth/user-exists/{current_user}",
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "Token validation failed"}), 500

        exists = response.json().get("exists", False)

        # If user doesn't exist - token invalid
        if not exists:
            return jsonify({"error": "Invalid token"}), 401

        # Token is valid
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
            # Log failed refresh
            log_action("TOKEN_REFRESH_FAILED", None, "Invalid or expired refresh token")
            return jsonify({"error": "Invalid or expired refresh token"}), 401
        
        username = token_data["username"]
        
        # Create new access token
        access_token = create_access_token(identity=username)
        
        # Log token refresh
        log_action("TOKEN_REFRESHED", username, "Access token refreshed successfully")
        
        # OAuth2-style expiration format
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
        
        #Get user_id
        response = requests.get(
            f"{DB_MANAGER_URL}/auth/user-id/{current_user}",
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve user"}), 500
        
        user_id = response.json().get("user_id")
        
        if user_id is None:
            return jsonify({"error": "User not found"}), 404
        
        # If refresh token provided - revoke only that one
        if data.get("refresh_token"):
            refresh_token = data["refresh_token"]

            success = revoke_refresh_token(refresh_token)

            log_action(
                "USER_LOGOUT",
                current_user,
                f"User logged out - specific token revoked (success: {success})"
            )
        
        else:
            # Revoke ALL tokens for this user
            success = revoke_all_user_tokens(user_id)

            log_action(
                "USER_LOGOUT",
                current_user,
                f"User logged out - all tokens revoked (success: {success})"
            )
        
        return jsonify({"message": "Logged out successfully"}), 200
        
    except Exception as e:
        log_action(
            "LOGOUT_ERROR",
            current_user if 'current_user' in locals() else None,
            f"Logout failed: {str(e)}"
        )
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@app.route("/api/auth/sessions", methods=["GET"])
@jwt_required()
def get_sessions():
    """Get all active sessions for the current user."""
    try:
        current_user = get_jwt_identity()
        
        # Get user_id
        response = requests.get(
            f"{DB_MANAGER_URL}/auth/user-id/{current_user}",
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve user"}), 500
        
        user_id = response.json().get("user_id")
        
        if user_id is None:
            return jsonify({"error": "User not found"}), 404
        
        # Get active sessions
        sessions = get_active_sessions(user_id)

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
        
        # Get user id
        response = requests.get(
            f"{DB_MANAGER_URL}/auth/user-id/{current_user}",
            timeout=5
        )
        user_id = response.json().get("user_id")

        if user_id is None:
            return jsonify({"error": "User not found"}), 404
        
        # Get session owner from DB Manager
        session_response = requests.get(
            f"{DB_MANAGER_URL}/tokens/session/{session_id}",
            timeout=5
        )
        session = session_response.json().get("session")

        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Verify the session belongs to current user
        if session["user_id"] != user_id:
            log_action(
                "UNAUTHORIZED_SESSION_REVOKE",
                current_user,
                f"Attempted to revoke session {session_id} belonging to another user"
            )
            return jsonify({"error": "Unauthorized"}), 403
        
        # Revoke session in DB Manager
        revoke_response = requests.delete(
            f"{DB_MANAGER_URL}/tokens/revoke-session/{session_id}",
            timeout=5
        )
        
        success = revoke_response.json().get("success", False)
        
        if success:
            log_action("SESSION_REVOKED", current_user, f"User revoked session {session_id}")
            return jsonify({"message": "Session revoked successfully"}), 200
        else:
            return jsonify({"error": "Failed to revoke session"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to revoke session: {str(e)}"}), 500


@app.route("/api/auth/sessions/revoke-all", methods=["POST"])
@jwt_required()
def revoke_all_sessions():
    """Revoke all sessions for the current user (except the current one if specified)."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        # Get user_id from DB Manager
        response = requests.get(
            f"{DB_MANAGER_URL}/auth/user-id/{current_user}",
            timeout=5
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve user"}), 500
        
        user_id = response.json().get("user_id")

        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Revoke all tokens for this user via DB Manager
        revoke_response = requests.post(
            f"{DB_MANAGER_URL}/tokens/revoke_all",
            json={"user_id": user_id},
            timeout=5
        )

        if revoke_response.status_code != 200:
            return jsonify({"error": "Failed to revoke sessions"}), 500
        
        success = revoke_response.json().get("success", False)

        # Log the action (keep your original log)
        log_action("ALL_SESSIONS_REVOKED", current_user, "User revoked all sessions")
        
        if success:
            return jsonify({"message": "All sessions revoked successfully"}), 200
        else:
            return jsonify({"error": "Failed to revoke sessions"}), 500
        
    except Exception as e:
        return jsonify({"error": f"Failed to revoke all sessions: {str(e)}"}), 500


# Admin-only endpoints
def require_admin():
    """Decorator to require admin privileges."""

    def wrapper(fn):
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user = get_jwt_identity()

            try:
                response = requests.get(
                    f"{DB_MANAGER_URL}/auth/is-admin/{current_user}",
                    timeout=5
                )
                
                if response.status_code != 200:
                    return jsonify({"error": "Failed to verify admin status"}), 500
                
                is_admin = response.json().get("is_admin", False)
                
                if not is_admin:
                    # Log unauthorized admin access attempt
                    log_action(
                        "UNAUTHORIZED_ADMIN_ACCESS",
                        current_user,
                        f"Attempted to access admin endpoint: {fn.__name__}",
                    )
                    return jsonify({"error": "Admin privileges required"}), 403

                return fn(*args, **kwargs)
            
            except Exception as e:
                return jsonify({"error": f"Failed to check admin status: {str(e)}"}), 500

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

        # Call db-manager to get users
        response = requests.get(
            f"{DB_MANAGER_URL}/admin/users",
            params={"page": page, "size": size},
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve users"}), 500

        data = response.json()
        users = data.get("users", [])
        total = data.get("total", 0)

        # Format users response
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
                        if isinstance(user.get("created_at"), str)
                        else user["created_at"]
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

        # Call db-manager to search users
        response = requests.get(
            f"{DB_MANAGER_URL}/admin/users/search",
            params={"query": query, "page": page, "size": size},
            timeout=5
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to search users"}), 500

        data = response.json()
        users = data.get("users", [])
        total = data.get("total", 0)

        # Format users response
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
                        if isinstance(user.get("created_at"), str)
                        else user["created_at"]
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
