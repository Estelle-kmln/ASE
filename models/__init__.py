"""Models module - compatibility layer for imports."""

# Re-export classes from game.game_logic for backward compatibility
from game.game_logic import Card, Deck, Game, Hand, Player

__all__ = ["Card", "Deck", "Game", "Hand", "Player"]

