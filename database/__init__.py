"""Database package for game persistence.

This package provides database operations for the battle card game application.
It includes:
    - GameRepository: Repository pattern implementation for persisting and loading game state
    - db module: Low-level database connection and user authentication functions

The database uses SQLite for persistence, storing game state as JSON-serialized data
in the games table, and user credentials in the users table.
"""

from .game_repository import GameRepository

__all__ = ["GameRepository"]
