"""CLI interface for the battle card game."""

from typing import List, Optional

from game.game_service import GameService
from models.card import Card
from models.deck import Deck
from models.game import Game


class CLI:
    """Command-line interface for the battle card game."""

    def __init__(self):
        """Initialize the CLI."""
        self.game_service = GameService()

    def display_card_collection(self):
        """Display all available cards in the collection."""
        collection = self.game_service.get_card_collection()
        print("\n=== Available Cards (39 total) ===\n")

        cards = collection.get_all_cards()
        for i, card in enumerate(cards, 1):
            print(f"{i:2d}. {card}")

        print()

    def select_deck(self) -> List[Card]:
        """Guide the player through selecting 22 cards for their deck.

        Returns:
            List of 22 selected cards
        """
        collection = self.game_service.get_card_collection()
        all_cards = collection.get_all_cards()
        selected_cards: List[Card] = []

        print("\n=== Build Your Deck ===\n")
        print(
            f"Select {Deck.DECK_SIZE} cards for your deck from the collection.\n"
        )

        while len(selected_cards) < Deck.DECK_SIZE:
            remaining = Deck.DECK_SIZE - len(selected_cards)
            print(f"\nCards selected: {len(selected_cards)}/{Deck.DECK_SIZE}")
            print(f"Remaining: {remaining}")

            if len(selected_cards) > 0:
                print("\nSelected cards so far:")
                for i, card in enumerate(selected_cards, 1):
                    print(f"  {i}. {card}")

            print(
                f"\nEnter card number (1-{len(all_cards)}) to add to deck (or 'q' to quit): ",
                end="",
            )
            user_input = input().strip().lower()

            if user_input == "q":
                print("Deck building cancelled.")
                return []

            try:
                card_index = int(user_input) - 1
                if not (0 <= card_index < len(all_cards)):
                    print(
                        f"Invalid card number. Please enter a number between 1 and {len(all_cards)}."
                    )
                    continue

                selected_card = all_cards[card_index]

                if selected_card in selected_cards:
                    print(
                        f"Card {selected_card} is already in your deck. Please select a different card."
                    )
                    continue

                selected_cards.append(selected_card)
                print(f"Added {selected_card} to your deck.")

            except ValueError:
                print("Invalid input. Please enter a number or 'q' to quit.")

        print(
            f"\n✓ Deck complete! You have selected {len(selected_cards)} cards."
        )
        return selected_cards

    def choose_deck_option(self) -> List[Card]:
        """Let the player choose between random deck or manual selection.
        
        Returns:
            List of 22 selected cards, or empty list if cancelled
        """
        print("\n=== Choose Deck Option ===\n")
        print("1. Random deck (quick start)")
        print("2. Build deck manually (select 22 cards)")
        print()
        
        while True:
            choice = input("Enter your choice (1 or 2, or 'q' to quit): ").strip().lower()
            
            if choice == "q":
                print("Deck selection cancelled.")
                return []
            
            if choice == "1":
                # Random deck
                print("\nGenerating random deck...")
                random_deck = self.game_service.create_random_deck()
                selected_cards = random_deck.cards
                
                print(f"\n✓ Random deck generated with {len(selected_cards)} cards:")
                for i, card in enumerate(selected_cards, 1):
                    print(f"  {i:2d}. {card}")
                print()
                
                return selected_cards
            
            elif choice == "2":
                # Manual selection
                self.display_card_collection()
                return self.select_deck()
            
            else:
                print("Invalid choice. Please enter 1, 2, or 'q'.")

    def start_new_game(self):
        """Start a new game - main entry point for the user story."""
        print("\n" + "=" * 50)
        print("  START NEW GAME")
        print("=" * 50)

        # Let player choose deck option
        selected_cards = self.choose_deck_option()

        if not selected_cards:
            print("\nGame start cancelled.")
            return None

        # Validate deck
        is_valid, error_msg = self.game_service.validate_deck_selection(
            selected_cards
        )
        if not is_valid:
            print(f"\nError: {error_msg}")
            return None

        # Create deck
        try:
            deck = self.game_service.create_deck(selected_cards)
        except ValueError as e:
            print(f"\nError creating deck: {e}")
            return None

        # Start game
        try:
            game = self.game_service.start_new_game(deck, save=True)
            print(f"\n{'='*50}")
            print("  GAME STARTED SUCCESSFULLY!")
            print(f"{'='*50}")
            print(f"Game ID: {game.game_id}")
            print(f"Turn: {game.turn}")
            print(f"Deck size: {len(game.deck)}")
            print(f"Deck shuffled: {game.deck.shuffled}")
            print("Game saved to database.")
            print("\nYou can now play the game!")
            return game
        except ValueError as e:
            print(f"\nError starting game: {e}")
            return None

    def display_hand(self, hand):
        """Display the current hand to the player.
        
        Args:
            hand: The Hand object to display
        """
        print("\n=== Your Hand ===")
        for i, card in enumerate(hand.cards, 1):
            print(f"  {i}. {card}")
        print()

    def play_turn(self, game: Game) -> bool:
        """Play a single turn: draw 3 cards, player picks 1, discard 2.
        
        Args:
            game: The current game
        
        Returns:
            True if turn was played successfully, False if game ended or cancelled
        """
        try:
            # Start turn - draw 3 cards
            hand = game.start_turn()
            
            print(f"\n{'='*50}")
            print(f"  TURN {game.turn}")
            print(f"{'='*50}")
            print(f"Cards remaining in deck: {len(game.deck)}")
            
            # Display the hand
            self.display_hand(hand)
            
            # Let player choose which card to play
            while True:
                print("Which card would you like to play?")
                choice = input("Enter card number (1-3, or 'q' to quit turn): ").strip().lower()
                
                if choice == "q":
                    print("Turn cancelled.")
                    return False
                
                try:
                    card_index = int(choice) - 1  # Convert to 0-based index
                    
                    if not (0 <= card_index < len(hand.cards)):
                        print(f"Invalid choice. Please enter a number between 1 and {len(hand.cards)}.")
                        continue
                    
                    # Play the selected card
                    played_card = game.play_turn(card_index)
                    discarded = hand.discarded_cards
                    
                    print(f"\n✓ Played: {played_card}")
                    print(f"✓ Discarded: {', '.join(str(c) for c in discarded)}")
                    print(f"✓ Cards remaining in deck: {len(game.deck)}")
                    
                    # Save game state
                    self.game_service.repository.save_game(game)
                    
                    return True
                    
                except ValueError:
                    print("Invalid input. Please enter a number (1-3) or 'q'.")
                except IndexError as e:
                    print(f"Error: {e}")
                    
        except ValueError as e:
            # Handle cases like "not enough cards"
            print(f"\n⚠ {e}")
            if "Not enough cards" in str(e):
                print("Game ended - deck is empty!")
                game.is_active = False
                self.game_service.repository.save_game(game)
            return False

    def play_game(self, game: Game):
        """Main game loop - play turns until deck runs out or player quits.
        
        Args:
            game: The game to play
        """
        print("\n" + "=" * 50)
        print("  GAME STARTED - BEGIN PLAYING")
        print("=" * 50)
        
        while game.is_active:
            # Check if we can play another turn
            if len(game.deck) < 3:
                print(f"\n⚠ Not enough cards for another turn ({len(game.deck)} remaining).")
                print("Game ended!")
                game.is_active = False
                self.game_service.repository.save_game(game)
                break
            
            # Ask if player wants to play next turn
            print("\n" + "-" * 50)
            response = input("Play next turn? (y/n): ").strip().lower()
            
            if response in ["n", "no", "q", "quit"]:
                print("\nGame paused.")
                print(f"Current turn: {game.turn}")
                print(f"Cards remaining: {len(game.deck)}")
                break
            
            if response in ["y", "yes", ""]:
                success = self.play_turn(game)
                if not success:
                    break
            else:
                print("Invalid response. Please enter 'y' for yes or 'n' for no.")
        
        print("\n" + "=" * 50)
        print("  GAME SESSION ENDED")
        print("=" * 50)


def main():
    """Main entry point for the CLI."""
    cli = CLI()
    game = cli.start_new_game()
    
    if game:
        # Offer to start playing
        print("\n" + "-" * 50)
        response = input("Would you like to start playing? (y/n): ").strip().lower()
        
        if response in ["y", "yes", ""]:
            cli.play_game(game)
        else:
            print("\nGame saved. You can continue later!")


if __name__ == "__main__":
    main()
