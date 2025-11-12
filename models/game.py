"""Game model for the battle card game."""

from typing import List, Optional

from .card import Card
from .deck import Deck


class Player:
    """Represents a player in the game."""
    
    def __init__(self, name: str, deck: Deck):
        """Initialize a player.
        
        Args:
            name: Player's name
            deck: The player's deck (will be shuffled)
        """
        if not deck.shuffled:
            deck.shuffle()
        
        self.name = name
        self.deck = deck
        self.hand: Optional['Hand'] = None  # Forward reference
        self.score = 0  # Initialize score
    
    def __repr__(self) -> str:
        return f"Player({self.name}, deck={len(self.deck)} cards, score={self.score})"


class Hand:
    """Represents a hand of 3 cards for a turn."""
    
    HAND_SIZE = 3
    
    def __init__(self, cards: Optional[List[Card]] = None):
        """Initialize a hand.
        
        Args:
            cards: List of cards for the hand (must be 3 cards)
        
        Raises:
            ValueError: If cards list is not exactly 3 cards
        """
        if cards is None:
            cards = []
        
        if len(cards) != self.HAND_SIZE:
            raise ValueError(f"Hand must contain exactly {self.HAND_SIZE} cards, got {len(cards)}")
        
        self.cards = cards.copy()
        self.played_card: Optional[Card] = None
        self.discarded_cards: List[Card] = []
    
    def play_card(self, card_index: int) -> Card:
        """Play a card from the hand.
        
        Args:
            card_index: Index of the card to play (0-2)
        
        Returns:
            The played card
        
        Raises:
            IndexError: If card_index is out of range
            ValueError: If a card has already been played this turn
        """
        if self.played_card is not None:
            raise ValueError("A card has already been played this turn")
        
        if not (0 <= card_index < len(self.cards)):
            raise IndexError(f"Card index {card_index} is out of range")
        
        self.played_card = self.cards.pop(card_index)
        return self.played_card
    
    def discard_remaining(self) -> List[Card]:
        """Discard the remaining cards in the hand (should be 2 after playing).
        
        Returns:
            List of discarded cards
        """
        discarded = self.cards.copy()
        self.discarded_cards.extend(discarded)
        self.cards.clear()
        return discarded
    
    def is_complete(self) -> bool:
        """Check if the hand has been fully processed (card played, others discarded).
        
        Returns:
            True if hand is complete
        """
        return self.played_card is not None and len(self.cards) == 0
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __repr__(self) -> str:
        return f"Hand({len(self.cards)} cards, played={self.played_card is not None})"


class Game:
    """Represents the main game state with 2 players."""
    
    def __init__(self, player1_name: str, player1_deck: Deck, player2_name: str, player2_deck: Deck, game_id: Optional[str] = None):
        """Initialize a new game with 2 players.
        
        Args:
            player1_name: Name of the first player
            player1_deck: First player's deck (will be shuffled)
            player2_name: Name of the second player
            player2_deck: Second player's deck (will be shuffled)
            game_id: Optional unique identifier for the game
        """
        self.game_id = game_id
        self.player1 = Player(player1_name, player1_deck)
        self.player2 = Player(player2_name, player2_deck)
        self.current_player: Player = self.player1  # Player 1 starts
        self.turn = 0
        self.is_active = True
        # Track per-round wins (score) for each player. These are in-memory only
        # and not persisted by the repository schema currently in use.
        self.player1_score = 0
        self.player2_score = 0
    
    def get_current_player(self) -> Player:
        """Get the current player whose turn it is.
        
        Returns:
            The current player
        """
        return self.current_player
    
    def get_other_player(self) -> Player:
        """Get the other player (not current).
        
        Returns:
            The other player
        """
        return self.player2 if self.current_player == self.player1 else self.player1
    
    def switch_player(self):
        """Switch to the other player."""
        self.current_player = self.get_other_player()
    
    def start_turn(self) -> Hand:
        """Start a new turn for the current player by drawing 3 cards.
        
        Returns:
            The new hand
        
        Raises:
            ValueError: If there are not enough cards in the deck
            ValueError: If current hand is not complete
        """
        player = self.get_current_player()
        
        if player.hand is not None and not player.hand.is_complete():
            raise ValueError(f"Cannot start new turn until {player.name}'s current hand is complete")
        
        if len(player.deck) < Hand.HAND_SIZE:
            raise ValueError(f"Not enough cards in {player.name}'s deck to start turn (need {Hand.HAND_SIZE}, have {len(player.deck)})")
        
        drawn_cards = player.deck.draw(Hand.HAND_SIZE)
        player.hand = Hand(drawn_cards)
        self.turn += 1
        
        return player.hand
    
    def play_card_for_current_player(self, card_index: int) -> Card:
        """Play a card from the current player's hand (without switching players).
        
        Args:
            card_index: Index of the card to play
        
        Returns:
            The played card
        
        Raises:
            ValueError: If no hand is available
        """
        player = self.get_current_player()
        
        if player.hand is None:
            raise ValueError(f"No hand available for {player.name}. Start a turn first.")
        
        played_card = player.hand.play_card(card_index)
        
        # Automatically discard remaining cards
        if len(player.hand.cards) > 0:
            player.hand.discard_remaining()
        
        return played_card
    
    def battle(self) -> dict:
        """Compare the played cards from both players and determine the winner.
        
        Returns:
            Dictionary with:
            - 'winner': Player name who won (or None if tie)
            - 'player1_card': Card played by player1
            - 'player2_card': Card played by player2
            - 'reason': Explanation of why the winner won
        """
        # Get both players' played cards
        player1_hand_exists = self.player1.hand is not None
        player2_hand_exists = self.player2.hand is not None
        
        player1_card = self.player1.hand.played_card if player1_hand_exists else None
        player2_card = self.player2.hand.played_card if player2_hand_exists else None
        
        if player1_card is None or player2_card is None:
            raise ValueError("Both players must play a card before battling")
        
        # Compare cards
        if player1_card.beats(player2_card):
            winner = self.player1.name
            reason = self._get_battle_reason(player1_card, player2_card)
            # Increment per-round win for player1
            try:
                self.player1_score += 1
            except AttributeError:
                # In case scores weren't initialized for some reason
                self.player1_score = 1
        elif player2_card.beats(player1_card):
            winner = self.player2.name
            reason = self._get_battle_reason(player2_card, player1_card)
            # Increment per-round win for player2
            try:
                self.player2_score += 1
            except AttributeError:
                self.player2_score = 1
        else:
            # Shouldn't happen, but handle tie
            winner = None
            reason = "Tie (shouldn't happen)"
        
        return {
            'winner': winner,
            'player1_card': player1_card,
            'player2_card': player2_card,
            'reason': reason
        }
    
    def _get_battle_reason(self, winning_card, losing_card) -> str:
        """Generate an explanation of why a card won.
        
        Args:
            winning_card: The winning card
            losing_card: The losing card
        
        Returns:
            Explanation string
        """
        if winning_card.suit != losing_card.suit:
            # Suit-based win
            suit_beats = {
                "rock": "scissors",
                "scissors": "paper",
                "paper": "rock"
            }
            return f"{winning_card.suit} beats {losing_card.suit}"
        else:
            # Number-based win
            if winning_card.value == 1 and losing_card.value == 13:
                return "1 beats 13 (special rule)"
            else:
                return f"{winning_card.value} beats {losing_card.value} (higher number)"
    
    def check_game_over(self) -> bool:
        """Check if the game should end (either player has less than 3 cards).
        
        Returns:
            True if game should end
        """
        return len(self.player1.deck) < 3 or len(self.player2.deck) < 3
    
    def __repr__(self) -> str:
        return f"Game(id={self.game_id}, turn={self.turn}, current={self.current_player.name}, active={self.is_active})"

