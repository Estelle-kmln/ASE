"""Merged Rock Paper Scissors Battle Card Game logic."""

import random
import uuid
from typing import List, Optional
import psycopg2
from database import get_available_cards, get_all_cards
from database.game_repository import GameRepository
import psycopg2


class Card:
    """Represents a Rock Paper Scissors card with type and power."""
    
    def __init__(self, card_type: str, power: int):
        """Initialize a card.
        
        Args:
            card_type: Type of card ('Rock', 'Paper', or 'Scissors')
            power: Power value (1-13)
        """
        if card_type.title() not in ['Rock', 'Paper', 'Scissors']:
            raise ValueError(f"Invalid card type: {card_type}")
        if not (1 <= power <= 13):
            raise ValueError(f"Power must be between 1 and 13, got {power}")
            
        self.type = card_type.title()
        self.power = power
    
    def __str__(self):
        symbol_emoji = {'Rock': '🪨', 'Paper': '📄', 'Scissors': '✂️'}
        emoji = symbol_emoji.get(self.type, self.type)
        return f"{emoji} {self.type} {self.power}"
    
    def __repr__(self):
        return f"Card({self.type}, {self.power})"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.type == other.type and self.power == other.power
    
    def __hash__(self):
        return hash((self.type, self.power))
    
    def beats(self, other: 'Card') -> bool:
        """Check if this card beats another card in Rock Paper Scissors."""
        winning_combinations = {
            'Rock': 'Scissors',
            'Paper': 'Rock', 
            'Scissors': 'Paper'
        }
        return winning_combinations[self.type] == other.type


class Deck:
    """Represents a deck of 22 cards."""
    
    DECK_SIZE = 22
    
    def __init__(self, cards: List[Card]):
        """Initialize a deck.
        
        Args:
            cards: List of cards (must be 22 unique cards)
        
        Raises:
            ValueError: If deck size is not 22 or has duplicates
        """
        if len(cards) != self.DECK_SIZE:
            raise ValueError(f"Deck must contain exactly {self.DECK_SIZE} cards, got {len(cards)}")
        
        if len(set(cards)) != len(cards):
            raise ValueError("Deck cannot contain duplicate cards")
            
        self.cards = cards.copy()
        self.shuffled = False
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
        self.shuffled = True
    
    def draw_hand(self) -> List[Card]:
        """Draw 3 cards from the top of the deck.
        
        Returns:
            List of 3 cards
        
        Raises:
            ValueError: If deck has fewer than 3 cards
        """
        if len(self.cards) < 3:
            raise ValueError("Not enough cards in deck to draw a hand")
        
        hand_cards = []
        for _ in range(3):
            hand_cards.append(self.cards.pop(0))
        
        return hand_cards
    
    def __len__(self):
        return len(self.cards)
    
    def __bool__(self):
        return len(self.cards) > 0


class Hand:
    """Represents a hand of 3 cards for a turn."""
    
    HAND_SIZE = 3
    
    def __init__(self, cards: List[Card]):
        """Initialize a hand.
        
        Args:
            cards: List of cards for the hand (must be 3 cards)
        
        Raises:
            ValueError: If cards list is not exactly 3 cards
        """
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
        """Discard the remaining cards in the hand.
        
        Returns:
            List of discarded cards
        """
        self.discarded_cards.extend(self.cards)
        discarded = self.cards.copy()
        self.cards.clear()
        return discarded


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
        self.hand: Optional[Hand] = None
        self.score = 0
    
    def draw_new_hand(self) -> bool:
        """Draw a new hand of 3 cards from the deck.
        
        Returns:
            True if successful, False if not enough cards in deck
        """
        if len(self.deck) < Hand.HAND_SIZE:
            return False
        
        hand_cards = self.deck.draw_hand()
        self.hand = Hand(hand_cards)
        return True
    
    def __repr__(self) -> str:
        return f"Player({self.name}, deck={len(self.deck)} cards, score={self.score})"


class Game:
    """Represents a complete game between two players."""
    
    def __init__(self, player1_name: str, player1_deck: Deck, player2_name: str, player2_deck: Deck, game_id: str = None):
        """Initialize a game.
        
        Args:
            player1_name: Name of the first player
            player1_deck: First player's deck
            player2_name: Name of the second player  
            player2_deck: Second player's deck
            game_id: Optional game ID (generates one if not provided)
        """
        self.game_id = game_id or str(uuid.uuid4())
        self.player1 = Player(player1_name, player1_deck)
        self.player2 = Player(player2_name, player2_deck)
        self.current_player = self.player1  # Player 1 starts
        self.turn_number = 1
        self.game_over = False
        self.winner: Optional[Player] = None


class BattleCardGame:
    """Main game controller that manages the gameplay flow."""
    
    def __init__(self):
        """Initialize the game controller."""
        self.game: Optional[Game] = None
    
    def create_random_deck(self) -> Deck:
        """Create a random deck of 22 cards from the database."""
        all_cards_data = get_all_cards()
        if len(all_cards_data) < 22:
            raise ValueError("Not enough cards in database to create a deck")
        
        # Convert database cards to Card objects
        all_cards = []
        for card_data in all_cards_data:
            card = Card(card_data['type'], card_data['power'])
            all_cards.append(card)
        
        # Select 22 random cards
        selected_cards = random.sample(all_cards, 22)
        return Deck(selected_cards)
    
    def create_custom_deck(self, selected_cards: List[Card]) -> Deck:
        """Create a deck from specifically selected cards."""
        return Deck(selected_cards)
    
    def start_new_game(self, player1_name: str, player2_name: str, 
                      player1_deck: Optional[Deck] = None, player2_deck: Optional[Deck] = None) -> Game:
        """Start a new game between two players.
        
        Args:
            player1_name: Name of first player
            player2_name: Name of second player
            player1_deck: Optional custom deck for player 1 (random if None)
            player2_deck: Optional custom deck for player 2 (random if None)
        
        Returns:
            The initialized Game object
        """
        # Create random decks if not provided
        if player1_deck is None:
            player1_deck = self.create_random_deck()
        if player2_deck is None:
            player2_deck = self.create_random_deck()
        
        # Initialize the game
        self.game = Game(player1_name, player1_deck, player2_name, player2_deck)
        
        # Both players draw their initial hands
        self.game.player1.draw_new_hand()
        self.game.player2.draw_new_hand()
        
        return self.game
    
    def play_turn(self, card_index: int) -> dict:
        """Play a turn with the current player's selected card.
        
        Args:
            card_index: Index of card to play (0-2)
        
        Returns:
            Dictionary with turn results
        """
        if not self.game or self.game.game_over:
            raise ValueError("No active game")
        
        current_player = self.game.current_player
        other_player = self.game.player2 if current_player == self.game.player1 else self.game.player1
        
        # Play the card
        played_card = current_player.hand.play_card(card_index)
        
        # Switch to other player's turn
        self.game.current_player = other_player
        
        return {
            'player': current_player.name,
            'card_played': played_card,
            'turn_complete': True
        }
    
    def resolve_round(self) -> dict:
        """Resolve a round after both players have played cards.
        
        Returns:
            Dictionary with round results
        """
        if not self.game:
            raise ValueError("No active game")
        
        player1_card = self.game.player1.hand.played_card
        player2_card = self.game.player2.hand.played_card
        
        if not player1_card or not player2_card:
            raise ValueError("Both players must play cards before resolving round")
        
        # Determine winner
        round_winner = None
        if player1_card.beats(player2_card):
            round_winner = self.game.player1
        elif player2_card.beats(player1_card):
            round_winner = self.game.player2
        else:
            # It's a tie, check power levels
            if player1_card.power > player2_card.power:
                round_winner = self.game.player1
            elif player2_card.power > player1_card.power:
                round_winner = self.game.player2
            # If still tied, no one wins this round
        
        # Award point to winner
        if round_winner:
            round_winner.score += 1
        
        # Discard remaining cards from both hands
        self.game.player1.hand.discard_remaining()
        self.game.player2.hand.discard_remaining()
        
        # Try to draw new hands
        p1_can_continue = self.game.player1.draw_new_hand()
        p2_can_continue = self.game.player2.draw_new_hand()
        
        # Check if game is over
        game_continues = p1_can_continue and p2_can_continue
        if not game_continues:
            self.game.game_over = True
            # Determine overall winner
            if self.game.player1.score > self.game.player2.score:
                self.game.winner = self.game.player1
            elif self.game.player2.score > self.game.player1.score:
                self.game.winner = self.game.player2
            # Otherwise it's a tie (winner remains None)
        
        return {
            'player1_card': player1_card,
            'player2_card': player2_card,
            'round_winner': round_winner.name if round_winner else 'Tie',
            'player1_score': self.game.player1.score,
            'player2_score': self.game.player2.score,
            'game_over': self.game.game_over,
            'game_winner': self.game.winner.name if self.game.winner else ('Tie' if self.game.game_over else None),
            'game_continues': game_continues
        }


# Global game controller instance
game_controller = BattleCardGame()


def play_rps_game():
    """Start the Rock Paper Scissors Battle game."""
    rps_game_menu()


def rps_game_menu():
    """Rock Paper Scissors game menu with two-player support."""
    print("\n🎮 Welcome to Rock Paper Scissors Battle Cards! 🎮")
    
    while True:
        print("\n" + "="*50)
        print("ROCK PAPER SCISSORS BATTLE CARDS")
        print("="*50)
        print("1. Start New Two-Player Game")
        print("2. View Game Rules")
        print("3. Back to Main Menu")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        try:
            if choice == "1":
                start_two_player_game()
            elif choice == "2":
                show_game_rules()
            elif choice == "3":
                print("\nReturning to main menu...")
                break
            else:
                print("Invalid choice. Please select 1-3.")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again.")


def start_two_player_game():
    """Start a new two-player game."""
    print("\n" + "="*50)
    print("  START NEW GAME - 2 PLAYERS")
    print("="*50)
    
    # Get player names
    player1_name = input("\nEnter Player 1 name (default: Player 1): ").strip() or "Player 1"
    player2_name = input("Enter Player 2 name (default: Player 2): ").strip() or "Player 2"
    
    print(f"\nPlayers: {player1_name} vs {player2_name}")
    
    try:
        # Start the game with random decks
        game = game_controller.start_new_game(player1_name, player2_name)
        
        # Save the game when it starts
        try:
            repository = GameRepository()
            repository.save_game(game)
        except (psycopg2.Error, OSError) as e:
            print(f"\n⚠️ Warning: Could not save game to database: {e}")
        
        print(f"\n{'='*50}")
        print("  GAME STARTED SUCCESSFULLY!")
        print(f"{'='*50}")
        print(f"Game ID: {game.game_id}")
        print(f"Players: {player1_name} vs {player2_name}")
        print(f"{player1_name}'s deck: {len(game.player1.deck)} cards")
        print(f"{player2_name}'s deck: {len(game.player2.deck)} cards")
        print(f"Starting player: {game.current_player.name}")
        print("\nReady to play!")
        
        # Play the game
        play_game_loop(game)
        
    except Exception as e:
        print(f"\nError starting game: {e}")


def play_game_loop(game: Game):
    """Main game loop for playing turns."""
    print(f"\n🎮 Game started! Each round, both players draw 3 cards and play one each.")
    
    while not game.game_over:
        print(f"\n{'='*60}")
        print(f"TURN {game.turn_number}")
        print(f"{'='*60}")
        print(f"Score: {game.player1.name} {game.player1.score} - {game.player2.score} {game.player2.name}")
        print(f"Cards remaining: {game.player1.name} {len(game.player1.deck)} - {len(game.player2.deck)} {game.player2.name}")
        
        # Show both players' hands
        print(f"\n{game.player1.name}'s hand:")
        for i, card in enumerate(game.player1.hand.cards, 1):
            print(f"  {i}. {card}")
            
        print(f"\n{game.player2.name}'s hand:")
        for i, card in enumerate(game.player2.hand.cards, 1):
            print(f"  {i}. {card}")
        
        # Player 1 chooses card
        p1_choice = get_player_card_choice(game.player1)
        if p1_choice is None:
            print("Game cancelled.")
            return
        
        p1_result = game_controller.play_turn(p1_choice)
        print(f"\n{game.player1.name} played: {p1_result['card_played']}")
        
        # Player 2 chooses card  
        p2_choice = get_player_card_choice(game.player2)
        if p2_choice is None:
            print("Game cancelled.")
            return
            
        p2_result = game_controller.play_turn(p2_choice)
        print(f"{game.player2.name} played: {p2_result['card_played']}")
        
        # Resolve the round
        round_result = game_controller.resolve_round()
        
        print(f"\n⚔️ ROUND RESULT ⚔️")
        print(f"{game.player1.name}: {round_result['player1_card']}")
        print(f"{game.player2.name}: {round_result['player2_card']}")
        
        if round_result['round_winner'] == 'Tie':
            print("🤝 Round tied! No points awarded.")
        else:
            print(f"🏆 {round_result['round_winner']} wins this round!")
        
        print(f"\nCurrent Score: {game.player1.name} {round_result['player1_score']} - {round_result['player2_score']} {game.player2.name}")
        
        if round_result['game_over']:
            print(f"\n{'='*60}")
            print("GAME OVER!")
            print(f"{'='*60}")
            
            if round_result['game_winner'] == 'Tie':
                print("🤝 The game ended in a tie! Well played both!")
            else:
                print(f"🎉🏆 {round_result['game_winner']} wins the game! 🏆🎉")
            
            print(f"Final Score: {game.player1.name} {round_result['player1_score']} - {round_result['player2_score']} {game.player2.name}")
            
            # Save the completed game to the database
            try:
                repository = GameRepository()
                winner_name = round_result['game_winner'] if round_result['game_winner'] != 'Tie' else None
                repository.save_game(game, winner=winner_name)
                print("\n✅ Game saved to leaderboard!")
            except (psycopg2.Error, OSError) as e:
                print(f"\n⚠️ Warning: Could not save game to database: {e}")
        else:
            game.turn_number += 1
            input("\nPress Enter to continue to next round...")


def get_player_card_choice(player: Player) -> Optional[int]:
    """Get a player's card choice.
    
    Args:
        player: The player choosing
        
    Returns:
        Card index (0-based) or None if cancelled
    """
    while True:
        print(f"\n{player.name}, which card would you like to play?")
        choice = input("Enter card number (1-3, or 'q' to quit): ").strip().lower()
        
        if choice == 'q':
            return None
            
        try:
            card_num = int(choice)
            if not (1 <= card_num <= 3):
                print("Please enter a number between 1 and 3.")
                continue
            
            return card_num - 1  # Convert to 0-based index
            
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")


def show_game_rules():
    """Display the game rules."""
    print(f"\n{'='*60}")
    print("ROCK PAPER SCISSORS BATTLE CARDS - RULES")
    print(f"{'='*60}")
    print("""
🎯 OBJECTIVE: Win more rounds than your opponent!

🃏 DECK COMPOSITION:
• Each player gets 22 random cards
• Cards are Rock 🪨, Paper 📄, or Scissors ✂️
• Each card has a power value from 1-13

🎮 GAME FLOW:
1. Each player draws 3 cards to form their hand
2. Both players choose 1 card to play
3. Cards are compared to determine round winner
4. Both players discard remaining 2 cards and draw 3 new cards
5. Continue until not enough cards remain for full hands
6. Player with most round wins is the game winner!

⚔️ BATTLE RULES:
• Rock beats Scissors
• Paper beats Rock  
• Scissors beats Paper
• Same symbol = higher power wins
• Same symbol + same power = tie (no winner)

🏆 SCORING:
• Win a round = +1 point
• Most points at end wins the game!
• Ties are possible!
""")
    
    input("\nPress Enter to continue...")


def view_card_database():
    """View all available cards in database."""
    print("\n=== Card Database ===")
    cards = get_all_cards()
    
    if not cards:
        print("No cards found in database.")
        return
    
    # Group by symbol
    rock_cards = [c for c in cards if c['type'].lower() == 'rock']
    paper_cards = [c for c in cards if c['type'].lower() == 'paper'] 
    scissors_cards = [c for c in cards if c['type'].lower() == 'scissors']
    
    print(f"\n🪨 ROCK CARDS ({len(rock_cards)}):")
    for card in sorted(rock_cards, key=lambda x: x['power']):
        print(f"   Power {card['power']}")
    
    print(f"\n📄 PAPER CARDS ({len(paper_cards)}):")  
    for card in sorted(paper_cards, key=lambda x: x['power']):
        print(f"   Power {card['power']}")
        
    print(f"\n✂️ SCISSORS CARDS ({len(scissors_cards)}):")
    for card in sorted(scissors_cards, key=lambda x: x['power']):
        print(f"   Power {card['power']}")
    
    print(f"\nTotal cards available: {len(cards)}")
    
    input("\nPress Enter to return to main menu...")


def show_card_statistics():
    """Show statistics about available cards."""
    print("\n=== Card Statistics ===")
    
    cards = get_all_cards()
    
    if not cards:
        print("No cards found.")
        return
    
    # Count by symbol
    symbol_counts = {}
    power_counts = {}
    
    for card in cards:
        symbol = card['type'].lower()
        power = card['power']
        
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        power_counts[power] = power_counts.get(power, 0) + 1
    
    print(f"Total Cards: {len(cards)}")
    print(f"\nSymbol Distribution:")
    for symbol, count in sorted(symbol_counts.items()):
        emoji = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}.get(symbol, symbol)
        print(f"  {emoji} {symbol.title()}: {count}")
    
    print(f"\nPower Distribution:")
    for power in sorted(power_counts.keys()):
        print(f"  Power {power}: {power_counts[power]} cards")
    
    input("\nPress Enter to return to main menu...")