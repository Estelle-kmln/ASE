"""Database operations for the battle card game."""

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
    """Check if a username already exists in the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0


def create_account(username, password):
    """Create a new account in the database."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
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


def verify_login(username, password):
    """Verify if username and password match an existing account."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE username = %s AND password = %s",
        (username, password),
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count > 0


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

