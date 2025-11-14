"""Database operations for the battle card game.

This module provides low-level database connection and user authentication functions.
It manages SQLite database connections and handles user account operations including
account creation, login verification, and username existence checks.

The database file is stored as 'game.db' in the current working directory.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gameuser:gamepassword@localhost:5432/battlecards")


def get_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(DATABASE_URL)


def init_database():
    """Initialize the database (tables are already created by init script)."""
    # Tables are created by postgresql-init/01-init-cards.sql
    # This function exists for compatibility but does nothing
    pass


def username_exists(username):
    """Check if a username already exists in the database.

    Queries the users table to determine if a given username is already registered.
    This is useful for validation before attempting to create a new account.

    Args:
        username (str): The username to check for existence.

    Returns:
        bool: True if the username exists in the database, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0


def create_account(username, password):
    """Create a new account in the database.

    Inserts a new user record into the users table with the provided username
    and password. The username must be unique; if it already exists, the operation
    will fail and return False.

    Args:
        username (str): The username for the new account (must be unique).
        password (str): The password for the new account.

    Returns:
        bool: True if the account was successfully created, False if the username
              already exists (IntegrityError).

    Note:
        Passwords are stored as plain text. In a production environment, passwords
        should be hashed before storage for security purposes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Ensure strings are properly encoded as UTF-8
        username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
        password = str(password).encode('utf-8', errors='ignore').decode('utf-8')
        
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password),
        )
        conn.commit()
        conn.close()
        return True
    except psycopg2.IntegrityError:
        conn.close()
        return False
    except Exception as e:
        print(f"Database error: {e}")
        conn.close()
        return False


def verify_login(username, password):
    """Verify if username and password match an existing account.

    Authenticates a user by checking if the provided username and password
    combination exists in the database. This is used for login verification.

    Args:
        username (str): The username to verify.
        password (str): The password to verify.

    Returns:
        bool: True if the username and password match an existing account,
              False otherwise.

    Note:
        This performs a plain text password comparison. In a production
        environment, passwords should be hashed and compared using secure
        hashing algorithms.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Ensure strings are properly encoded as UTF-8
        username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
        password = str(password).encode('utf-8', errors='ignore').decode('utf-8')
        
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s",
            (username, password),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Database error: {e}")
        conn.close()
        return False


def get_all_cards():
    """Get all RPS cards from the database."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM cards ORDER BY type, power")
    cards = cursor.fetchall()
    
    conn.close()
    return cards


def get_cards_by_type(card_type):
    """Get cards by type (rock, paper, or scissors)."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM cards WHERE LOWER(type) = LOWER(%s) ORDER BY power", (card_type,))
    cards = cursor.fetchall()
    
    conn.close()
    return cards


def get_card_by_id(card_id):
    """Get a specific card by ID."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM cards WHERE id = %s", (card_id,))
    card = cursor.fetchone()
    
    conn.close()
    return card


def get_available_cards():
    """Get all available RPS card types and powers."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT DISTINCT type FROM cards ORDER BY type")
    types = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT power FROM cards ORDER BY power")
    powers = cursor.fetchall()
    
    conn.close()
    return [t['type'] for t in types], [p['power'] for p in powers]


def get_user_profile(username):
    """Get user profile information by username.
    
    Args:
        username (str): The username to get profile for.
        
    Returns:
        dict or None: User profile data if found, None otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    conn.close()
    return dict(user) if user else None


def update_user_password(username, new_password):
    """Update user's password.
    
    Args:
        username (str): The username to update password for.
        new_password (str): The new password.
        
    Returns:
        bool: True if update was successful, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Ensure strings are properly encoded as UTF-8
        username = str(username).encode('utf-8', errors='ignore').decode('utf-8')
        new_password = str(new_password).encode('utf-8', errors='ignore').decode('utf-8')
        
        cursor.execute(
            "UPDATE users SET password = %s WHERE username = %s",
            (new_password, username)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Database error: {e}")
        conn.close()
        return False

