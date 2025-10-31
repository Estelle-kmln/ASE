"""Database operations for the battle card game."""

import sqlite3

DB_NAME = "game.db"


def get_connection():
    """Create and return a database connection."""
    return sqlite3.connect(DB_NAME)


def init_database():
    """Initialize the database and create the users table if it doesn't exist."""
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
    """Check if a username already exists in the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0


def create_account(username, password):
    """Create a new account in the database."""
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
    """Verify if username and password match an existing account."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE username = ? AND password = ?",
        (username, password),
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0

