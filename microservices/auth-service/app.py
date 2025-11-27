"""
Auth Service - User authentication and profile management microservice
"""

import os
import sys
import bcrypt
from datetime import timedelta, datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add utils directory to path for input sanitizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from input_sanitizer import InputSanitizer, SecurityMiddleware, require_sanitized_input

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

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

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://gameuser:gamepassword@localhost:5432/battlecards')

def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(DATABASE_URL)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'auth-service'}), 200

@app.route('/api/auth/register', methods=['POST'])
@require_sanitized_input({'username': 'username', 'password': 'password', 'email': 'email'})
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Sanitize and validate inputs
        try:
            username = InputSanitizer.validate_username(data['username'])
            password = InputSanitizer.validate_password(data['password'])
            
            # Optional email validation
            email = None
            if 'email' in data and data['email']:
                email = InputSanitizer.validate_email(data['email'])
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'error': 'Username already exists'}), 409
        
        # Hash password and create user
        hashed_password = hash_password(password)
        if email:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s) RETURNING id",
                (username, hashed_password, email)
            )
        else:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
                (username, hashed_password)
            )
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        # Create access token
        access_token = create_access_token(identity=username)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': user_id,
                'username': username
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
@require_sanitized_input({'username': 'username', 'password': 'password'})
def login():
    """Authenticate user and return JWT token."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Sanitize and validate inputs
        try:
            username = InputSanitizer.validate_username(data['username'])
            password = InputSanitizer.validate_password(data['password'])
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get user from database
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create access token
        access_token = create_access_token(identity=username)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id, username, created_at FROM users WHERE username = %s", (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (current_user,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        # Update password if provided
        if 'password' in data and data['password']:
            try:
                new_password = InputSanitizer.validate_password(data['password'])
            except ValueError as e:
                conn.close()
                return jsonify({'error': str(e)}), 400
            
            hashed_password = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password = %s WHERE username = %s",
                (hashed_password, current_user)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

@app.route('/api/auth/validate', methods=['POST'])
@jwt_required()
def validate_token():
    """Validate JWT token."""
    try:
        current_user = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (current_user,))
        user_exists = cursor.fetchone()[0] > 0
        conn.close()
        
        if not user_exists:
            return jsonify({'error': 'Invalid token'}), 401
        
        return jsonify({
            'valid': True,
            'username': current_user
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Token validation failed: {str(e)}'}), 500

if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=5001, debug=True)