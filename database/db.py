"""Database operations for the battle card game.

This module provides low-level database connection and user authentication functions.
It manages SQLite database connections and handles user account operations including
account creation, login verification, and username existence checks.

The database file is stored as 'game.db' in the current working directory.
"""

import sqlite3

# Database file name used for SQLite storage
DB_NAME = "game.db"


def get_connection():
    """Create and return a database connection.

    Creates a new SQLite database connection to the database file specified by DB_NAME.
    The connection must be closed by the caller after use.

    Returns:
        sqlite3.Connection: A connection object to the SQLite database.

    Note:
        It is recommended to use context managers (with statement) or ensure
        the connection is properly closed to avoid resource leaks.
    """
    return sqlite3.connect(DB_NAME)


def init_database():
    """Initialize the database and create the users table if it doesn't exist.

    This function sets up the database schema by creating the users table.
    The table stores user account information with the following structure:
        - id: Auto-incrementing primary key
        - username: Unique username (required, must be unique)
        - password: User password (required, stored as plain text)

    If the table already exists, this function does nothing (idempotent operation).
    This function should be called at application startup to ensure the database
    schema is properly initialized.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """
    )

    conn.commit()
    conn.close()


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

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
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
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
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

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE username = ? AND password = ?",
        (username, password),
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0
