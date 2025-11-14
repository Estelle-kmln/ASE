"""Merged Rock Paper Scissors Battle Card Game logic."""

import random
import uuid
from typing import List, Optional
from database import get_available_cards, get_all_cards


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


    """Manages the Rock Paper Scissors card game."""
    
    def __init__(self, player_name):
        self.player_name = player_name
        self.player_deck = []
        self.ai_deck = []
        self.player_hand = []
        self.ai_hand = []
        self.player_score = 0
        self.ai_score = 0
        self.round_number = 1
        
    def create_deck(self, rock_count=None, paper_count=None, scissors_count=None):
        """Create a deck of 22 cards with specified or random distribution."""
        if rock_count is None or paper_count is None or scissors_count is None:
            # Random distribution that adds up to 22
            remaining = 22
            rock_count = random.randint(1, remaining - 2)
            remaining -= rock_count
            paper_count = random.randint(1, remaining - 1)
            scissors_count = remaining - paper_count
        
        # Validate total is 22
        if rock_count + paper_count + scissors_count != 22:
            raise ValueError("Total cards must equal 22")
        
        deck = []
        
        # Add rock cards with random powers
        powers = list(range(1, 14)) * 2  # Two sets of 1-13 to have enough variety
        random.shuffle(powers)
        
        for _ in range(rock_count):
            power = powers.pop()
            deck.append(RPSCard('rock', power))
            
        for _ in range(paper_count):
            power = powers.pop()
            deck.append(RPSCard('paper', power))
            
        for _ in range(scissors_count):
            power = powers.pop()
            deck.append(RPSCard('scissors', power))
        
        random.shuffle(deck)
        return deck
    
    def setup_game(self, rock_count=None, paper_count=None, scissors_count=None):
        """Setup the game with player-chosen or random deck composition."""
        print(f"\n🎮 Setting up Rock Paper Scissors Battle for {self.player_name}!")
        
        if rock_count is None:
            choice = input("\nDo you want to choose your deck composition or use random? (choose/random): ").strip().lower()
            
            if choice == 'choose':
                rock_count, paper_count, scissors_count = self.choose_deck_composition()
            else:
                rock_count = paper_count = scissors_count = None
        
        # Create decks for both players
        self.player_deck = self.create_deck(rock_count, paper_count, scissors_count)
        self.ai_deck = self.create_deck()  # AI always gets random deck
        
        print(f"\n✅ Deck created!")
        self.display_deck_composition(self.player_deck, "Your")
        self.display_deck_composition(self.ai_deck, "AI")
        
        print(f"\nGame starts! You'll play until you have 1 card left.")
        
    def choose_deck_composition(self):
        """Let player choose their deck composition."""
        print("\n🎯 Choose your deck composition (22 cards total):")
        
        while True:
            try:
                rock_count = int(input("How many Rock cards? (1-20): "))
                if rock_count < 1 or rock_count > 20:
                    print("Rock count must be between 1 and 20")
                    continue
                    
                paper_count = int(input("How many Paper cards? (1-20): "))
                if paper_count < 1 or paper_count > 20:
                    print("Paper count must be between 1 and 20") 
                    continue
                    
                scissors_count = 22 - rock_count - paper_count
                
                if scissors_count < 1:
                    print(f"Not enough cards left for Scissors (need at least 1, got {scissors_count})")
                    continue
                    
                print(f"Your composition: {rock_count} Rock, {paper_count} Paper, {scissors_count} Scissors")
                confirm = input("Confirm this composition? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    return rock_count, paper_count, scissors_count
                    
            except ValueError:
                print("Please enter valid numbers")
    
    def display_deck_composition(self, deck, owner):
        """Display the composition of a deck."""
        rock_count = sum(1 for card in deck if card.symbol == 'rock')
        paper_count = sum(1 for card in deck if card.symbol == 'paper') 
        scissors_count = sum(1 for card in deck if card.symbol == 'scissors')
        
        print(f"{owner} deck: 🪨 {rock_count} Rock, 📄 {paper_count} Paper, ✂️ {scissors_count} Scissors")
    
    def draw_hand(self, deck):
        """Draw a hand of 3 cards from the deck."""
        if len(deck) < 3:
            return deck[:]  # Return all remaining cards if less than 3
        
        hand = deck[-3:]  # Take last 3 cards
        del deck[-3:]     # Remove them from deck
        return hand
    
    def display_hand(self, hand, owner="Your"):
        """Display a hand of cards."""
        print(f"\n{owner} hand:")
        for i, card in enumerate(hand, 1):
            print(f"{i}. {card}")
    
    def player_select_card(self, hand):
        """Let player select a card from their hand."""
        while True:
            try:
                choice = int(input(f"\nSelect card to play (1-{len(hand)}): ")) - 1
                if 0 <= choice < len(hand):
                    return hand.pop(choice)
                else:
                    print(f"Please select a number between 1 and {len(hand)}")
            except ValueError:
                print("Please enter a valid number")
    
    def ai_select_card(self, hand):
        """AI selects a random card from hand."""
        return hand.pop(random.randint(0, len(hand) - 1))
    
    def determine_winner(self, player_card, ai_card):
        """Determine winner based on RPS rules and power tiebreaker."""
        # Rock Paper Scissors rules
        if player_card.symbol == ai_card.symbol:
            # Same symbol - check power
            if player_card.power > ai_card.power:
                return "player"
            elif ai_card.power > player_card.power:
                return "ai"
            else:
                return "tie"
        
        # Different symbols - standard RPS rules
        winning_combinations = {
            ('rock', 'scissors'): 'player',
            ('paper', 'rock'): 'player', 
            ('scissors', 'paper'): 'player',
            ('scissors', 'rock'): 'ai',
            ('rock', 'paper'): 'ai',
            ('paper', 'scissors'): 'ai'
        }
        
        return winning_combinations.get((player_card.symbol, ai_card.symbol), 'tie')
    
    def play_round(self):
        """Play a single round (3 card battles)."""
        print(f"\n{'='*50}")
        print(f"ROUND {self.round_number}")
        print(f"{'='*50}")
        
        # Draw hands
        self.player_hand = self.draw_hand(self.player_deck)
        self.ai_hand = self.draw_hand(self.ai_deck)
        
        print(f"\nCards left in deck: You {len(self.player_deck)}, AI {len(self.ai_deck)}")
        
        round_player_wins = 0
        round_ai_wins = 0
        
        # Play 3 battles in the round
        for battle in range(1, min(len(self.player_hand), len(self.ai_hand)) + 1):
            print(f"\n--- Battle {battle} ---")
            
            # Show player's hand
            self.display_hand(self.player_hand)
            
            # Player selects card
            player_card = self.player_select_card(self.player_hand)
            
            # AI selects card
            ai_card = self.ai_select_card(self.ai_hand)
            
            print(f"\n🎭 Battle: {player_card} vs {ai_card}")
            
            # Determine winner
            winner = self.determine_winner(player_card, ai_card)
            
            if winner == "player":
                print(f"🎉 You win this battle!")
                round_player_wins += 1
            elif winner == "ai":
                print(f"💀 AI wins this battle!")
                round_ai_wins += 1
            else:
                print(f"⚖️ Tie! No one wins this battle!")
        
        # Determine round winner
        if round_player_wins > round_ai_wins:
            print(f"\n🏆 You win Round {self.round_number}!")
            self.player_score += 1
        elif round_ai_wins > round_player_wins:
            print(f"\n🤖 AI wins Round {self.round_number}!")
            self.ai_score += 1
        else:
            print(f"\n🤝 Round {self.round_number} is a tie!")
        
        print(f"\nScore after Round {self.round_number}: You {self.player_score} - {self.ai_score} AI")
        self.round_number += 1
    
    def play_final_card(self):
        """Handle the final card scenario when both players have 1 card left."""
        print(f"\n{'='*50}")
        print("FINAL CARD SCENARIO")
        print(f"{'='*50}")
        print(f"Current score: You {self.player_score} - {self.ai_score} AI")
        
        if self.player_score == self.ai_score:
            print("\n🎯 The score is tied! You can choose to play your final card or not.")
            choice = input("Do you want to play your final card? (y/n): ").strip().lower()
            
            if choice == 'y':
                player_card = self.player_deck[0]
                ai_card = self.ai_deck[0]
                
                print(f"\n🎭 Final Battle: {player_card} vs {ai_card}")
                
                winner = self.determine_winner(player_card, ai_card)
                
                if winner == "player":
                    print(f"🎉 You win the final battle and the game!")
                    self.player_score += 1
                elif winner == "ai":
                    print(f"💀 AI wins the final battle and the game!")
                    self.ai_score += 1
                else:
                    print(f"⚖️ Final battle is a tie! Game ends in a draw!")
            else:
                print("You chose not to play the final card. Game ends in a tie!")
        else:
            print("\n🏁 Game ends without final card play (score not tied).")
    
    def play_game(self):
        """Play the complete game."""
        # Game continues until both players have 1 card left
        while len(self.player_deck) > 1 and len(self.ai_deck) > 1:
            self.play_round()
            
            # Check if we can continue
            if len(self.player_deck) == 0 or len(self.ai_deck) == 0:
                break
                
            input("\nPress Enter to continue to next round...")
        
        # Handle final card scenario
        if len(self.player_deck) == 1 and len(self.ai_deck) == 1:
            self.play_final_card()
        
        # Show final results
        self.show_final_results()
    
    def show_final_results(self):
        """Display final game results."""
        print(f"\n{'='*50}")
        print("FINAL RESULTS")
        print(f"{'='*50}")
        print(f"Final Score: You {self.player_score} - {self.ai_score} AI")
        
        if self.player_score > self.ai_score:
            print(f"🎉🏆 VICTORY! You won the game! 🏆🎉")
        elif self.ai_score > self.player_score:
            print(f"💀 DEFEAT! AI won the game! 💀")
        else:
            print(f"🤝 DRAW! It's a tie game! 🤝")


def rps_game_menu():
    """Rock Paper Scissors game menu."""
    print("\n🎮 Welcome to Rock Paper Scissors Battle Cards! 🎮")
    
    while True:
        print("\n" + "="*50)
        print("ROCK PAPER SCISSORS BATTLE CARDS")
        print("="*50)
        print("1. Start New Game")
        print("2. View Game Rules")
        print("3. Back to Main Menu")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        try:
            if choice == "1":
                player_name = input("\nEnter your name: ").strip() or "Player"
                game = RPSGame(player_name)
                game.setup_game()
                game.play_game()
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


def show_game_rules():
    """Display the game rules."""
    print(f"\n{'='*60}")
    print("ROCK PAPER SCISSORS BATTLE CARDS - RULES")
    print(f"{'='*60}")
    print("""
🎯 OBJECTIVE: Win more rounds than your opponent!

🃏 DECK COMPOSITION:
• Each player gets 22 cards total
• Cards are Rock 🪨, Paper 📄, or Scissors ✂️
• Each card has a power value from 1-13
• You can choose your deck composition or get random

🎮 GAME FLOW:
1. Draw 3 cards to form your hand
2. Play 3 battles per round (1 card each)
3. Winner of most battles wins the round
4. Continue until 1 card remains in each deck
5. If score is tied, choose to play final card or not

⚔️ BATTLE RULES:
• Rock beats Scissors
• Paper beats Rock  
• Scissors beats Paper
• Same symbol = higher power wins
• Same symbol + same power = tie (no winner)

🏆 SCORING:
• Win a round = +1 point
• Most points at end wins the game!
""")
    
    input("\nPress Enter to continue...")


def game_menu():
    """Updated main game menu with RPS game."""
    print("\n🎮 Welcome to Battle Cards! 🎮")
    
    while True:
        print("\n" + "="*40)
        print("BATTLE CARD GAME - MAIN MENU") 
        print("="*40)
        print("1. Play Rock Paper Scissors Battle")
        print("2. View Card Database")
        print("3. Game Statistics")
        print("4. Logout")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        try:
            if choice == "1":
                rps_game_menu()
            elif choice == "2":
                view_card_database()
            elif choice == "3":
                show_card_statistics()
            elif choice == "4":
                print("\nLogging out... Thanks for playing!")
                break
            else:
                print("Invalid choice. Please select 1-4.")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again.")


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