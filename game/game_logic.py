"""Rock Paper Scissors Battle Card Game logic."""

import random
from database import get_available_cards, get_all_cards


class RPSCard:
    """Represents a Rock Paper Scissors card with symbol and power."""
    
    def __init__(self, symbol, power):
        self.symbol = symbol.lower()
        self.power = power
    
    def __str__(self):
        symbol_emoji = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
        emoji = symbol_emoji.get(self.symbol, self.symbol)
        return f"{emoji} {self.symbol.title()} {self.power}"
    
    def __repr__(self):
        return f"RPSCard({self.symbol}, {self.power})"


class RPSGame:
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