"""CLI interface for the battle card game."""

from typing import List

from game.game_service import GameService
from models.card import Card
from models.deck import Deck


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

    def start_new_game(self):
        """Start a new game - main entry point for the user story."""
        print("\n" + "=" * 50)
        print("  START NEW GAME")
        print("=" * 50)

        # Display available cards
        self.display_card_collection()

        # Let player select deck
        selected_cards = self.select_deck()

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


def main():
    """Main entry point for the CLI."""
    cli = CLI()
    cli.start_new_game()


if __name__ == "__main__":
    main()
