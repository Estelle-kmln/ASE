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
            choice = (
                input("Enter your choice (1 or 2, or 'q' to quit): ")
                .strip()
                .lower()
            )

            if choice == "q":
                print("Deck selection cancelled.")
                return []

            if choice == "1":
                # Random deck
                print("\nGenerating random deck...")
                random_deck = self.game_service.create_random_deck()
                selected_cards = random_deck.cards

                print(
                    f"\n✓ Random deck generated with {len(selected_cards)} cards:"
                )
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

    def get_player_name(
        self, player_number: int, default_name: str = ""
    ) -> str:
        """Get a player's name.

        Args:
            player_number: 1 or 2
            default_name: Default name to suggest

        Returns:
            Player's name
        """
        prompt = f"Enter name for Player {player_number}"
        if default_name:
            prompt += f" (default: {default_name})"
        prompt += ": "

        name = input(prompt).strip()

        if not name and default_name:
            return default_name
        elif not name:
            return f"Player {player_number}"

        return name

    def setup_player_deck(self, player_name: str) -> List[Card]:
        """Setup deck for a player.

        Args:
            player_name: Name of the player

        Returns:
            List of selected cards, or empty list if cancelled
        """
        print(f"\n{'='*50}")
        print(f"  SETUP DECK FOR {player_name.upper()}")
        print(f"{'='*50}")
        return self.choose_deck_option()

    def start_new_game(self):
        """Start a new game with 2 players - main entry point."""
        print("\n" + "=" * 50)
        print("  START NEW GAME - 2 PLAYERS")
        print("=" * 50)

        # Get player names
        player1_name = self.get_player_name(1, "alex")
        player2_name = self.get_player_name(2, "katrine")

        print(f"\nPlayers: {player1_name} vs {player2_name}")

        # Setup Player 1 deck
        player1_cards = self.setup_player_deck(player1_name)
        if not player1_cards:
            print("\nGame start cancelled.")
            return None

        # Setup Player 2 deck
        player2_cards = self.setup_player_deck(player2_name)
        if not player2_cards:
            print("\nGame start cancelled.")
            return None

        # Validate both decks
        is_valid1, error_msg1 = self.game_service.validate_deck_selection(
            player1_cards
        )
        is_valid2, error_msg2 = self.game_service.validate_deck_selection(
            player2_cards
        )

        if not is_valid1:
            print(f"\nError with {player1_name}'s deck: {error_msg1}")
            return None
        if not is_valid2:
            print(f"\nError with {player2_name}'s deck: {error_msg2}")
            return None

        # Check for overlapping cards (if needed - cards can overlap between players)
        # For now, we'll allow overlapping cards

        # Create decks
        try:
            player1_deck = self.game_service.create_deck(player1_cards)
            player2_deck = self.game_service.create_deck(player2_cards)
        except ValueError as e:
            print(f"\nError creating deck: {e}")
            return None

        # Start game
        try:
            game = self.game_service.start_new_game(
                player1_name,
                player1_deck,
                player2_name,
                player2_deck,
                save=True,
            )
            print(f"\n{'='*50}")
            print("  GAME STARTED SUCCESSFULLY!")
            print(f"{'='*50}")
            print(f"Game ID: {game.game_id}")
            print(f"Players: {player1_name} vs {player2_name}")
            print(f"{player1_name}'s deck: {len(player1_deck)} cards")
            print(f"{player2_name}'s deck: {len(player2_deck)} cards")
            print(f"Starting player: {game.current_player.name}")
            print("Game saved to database.")
            print("\nReady to play!")
            return game
        except ValueError as e:
            print(f"\nError starting game: {e}")
            return None

    def display_hand(self, hand, player_name: str):
        """Display the current hand to the player.

        Args:
            hand: The Hand object to display
            player_name: Name of the player
        """
        print(f"\n=== {player_name}'s Hand ===")
        for i, card in enumerate(hand.cards, 1):
            print(f"  {i}. {card}")
        print()

    def get_player_card_choice(self, player, hand) -> Optional[int]:
        """Get a player's card choice.

        Args:
            player: The player choosing
            hand: The player's hand

        Returns:
            Card index (0-based) or None if cancelled
        """
        while True:
            print(f"\nWhich card would you like to play, {player.name}?")
            choice = (
                input("Enter card number (1-3, or 'q' to quit): ")
                .strip()
                .lower()
            )

            if choice == "q":
                return None

            try:
                card_index = int(choice) - 1  # Convert to 0-based index

                if not (0 <= card_index < len(hand.cards)):
                    print(
                        f"Invalid choice. Please enter a number between 1 and {len(hand.cards)}."
                    )
                    continue

                return card_index

            except ValueError:
                print("Invalid input. Please enter a number (1-3) or 'q'.")

    def play_round(self, game: Game) -> bool:
        """Play a complete round: both players draw, choose, and battle.

        Args:
            game: The current game

        Returns:
            True if round was played successfully, False if cancelled or game ended
        """
        try:
            # Draw cards for both players
            print(f"\n{'='*50}")
            print(f"  ROUND {game.turn + 1}")
            print(f"{'='*50}")

            # Player 1 draws
            game.current_player = game.player1
            game.start_turn()  # This sets game.player1.hand
            print(
                f"\n{game.player1.name}'s deck: {len(game.player1.deck)} cards remaining"
            )
            self.display_hand(game.player1.hand, game.player1.name)
            card_index1 = self.get_player_card_choice(
                game.player1, game.player1.hand
            )

            if card_index1 is None:
                print("Round cancelled.")
                return False

            # Player 1 plays card
            played_card1 = game.play_card_for_current_player(card_index1)
            print(f"\n✓ {game.player1.name} played: {played_card1}")
            print(
                f"✓ Discarded: {', '.join(str(c) for c in game.player1.hand.discarded_cards)}"
            )

            # Player 2 draws
            game.current_player = game.player2
            game.start_turn()  # This sets game.player2.hand
            print(f"\n{'='*50}")
            print(
                f"{game.player2.name}'s deck: {len(game.player2.deck)} cards remaining"
            )
            self.display_hand(game.player2.hand, game.player2.name)
            card_index2 = self.get_player_card_choice(
                game.player2, game.player2.hand
            )

            if card_index2 is None:
                print("Round cancelled.")
                return False

            # Player 2 plays card
            played_card2 = game.play_card_for_current_player(card_index2)
            print(f"\n✓ {game.player2.name} played: {played_card2}")
            print(
                f"✓ Discarded: {', '.join(str(c) for c in game.player2.hand.discarded_cards)}"
            )

            # Battle!
            print(f"\n{'='*50}")
            print("  BATTLE!")
            print(f"{'='*50}")
            print(f"{game.player1.name} plays: {played_card1}")
            print(f"{game.player2.name} plays: {played_card2}")

            battle_result = game.battle()

            print(f"\n🎯 {battle_result['winner']} wins!")
            print(f"Reason: {battle_result['reason']}")

            # Save game state
            self.game_service.repository.save_game(game)

            return True

        except ValueError as e:
            # Handle cases like "not enough cards"
            print(f"\n⚠ {e}")
            if "Not enough cards" in str(e):
                print("Game ended - a player ran out of cards!")
                # End game and decide winner by round-win score (not remaining cards)
                game.is_active = False
                self.game_service.repository.save_game(game)
                # Show final round-win score
                self.keep_score(game)
                p1s = getattr(game, "player1_score", 0)
                p2s = getattr(game, "player2_score", 0)
                if p1s > p2s:
                    print(f"\n🎉 {game.player1.name} wins by score! ({p1s}–{p2s})")
                elif p2s > p1s:
                    print(f"\n🎉 {game.player2.name} wins by score! ({p2s}–{p1s})")
                else:
                    print("\n⚖️ Game ended in a tie by score!")
            return False
        
    def keep_score(self, game: Game):
        """Display the per-round win score for the current game.

        The Game object maintains `player1_score` and `player2_score` which are
        incremented by `Game.battle()` whenever a player wins a round.
        """
        player1_score = getattr(game, "player1_score", 0)
        player2_score = getattr(game, "player2_score", 0)

        print(f"\n=== Round Wins ===")
        print(f"{game.player1.name}: {player1_score} points")
        print(f"{game.player2.name}: {player2_score} points")
        print("=================\n")
        
        # if player1_score > player2_score:
        #     winner = game.player1.name
        # elif player2_score > player1_score:
        #     winner = game.player2.name

        # # if winner:
        # #     print(f"\n🎉 {winner} wins!)")
        # # print("=================\n")

    def play_game(self, game: Game):
        """Main game loop - play rounds until a deck runs out or player quits.

        Args:
            game: The game to play
        """
        print("\n" + "=" * 50)
        print("  GAME STARTED - BEGIN PLAYING")
        print("=" * 50)
        print("\nBattle Rules:")
        print(
            "1. Suit comparison: rock beats scissors, scissors beats paper, paper beats rock"
        )
        print("2. If suits match: higher number wins (except 1 beats 13)")
        print("=" * 50)

        while game.is_active:
            # Check if game should end (either player can't draw a full hand)
            if game.check_game_over():
                # Decide final winner using round-win score (preferred) and
                # fall back to remaining cards as a tiebreaker.
                p1s = getattr(game, "player1_score", 0)
                p2s = getattr(game, "player2_score", 0)

                if len(game.player1.deck) < 3 and len(game.player2.deck) < 3:
                    print("\n⚠ Both players are out of cards!")
                    if p1s > p2s:
                        print(f"\n🎉 {game.player1.name} wins the game with the score of: ({p1s}–{p2s})")
                    elif p2s > p1s:
                        print(f"\n🎉 {game.player2.name} wins the game with the score of: ({p2s}–{p1s})")
                    else:
                        print("\n⚖️ Game ended in a tie by score!")
                else:
                    # One player cannot continue; still decide by score first
                    if p1s > p2s:
                        print(f"\n🎉 {game.player1.name} wins by score! ({p1s}–{p2s})")
                    elif p2s > p1s:
                        print(f"\n🎉 {game.player2.name} wins by score! ({p2s}–{p1s})")
                    else:
                        # Tie on score — use remaining cards as tiebreaker
                        if len(game.player1.deck) > len(game.player2.deck):
                            print(f"\n🎉 {game.player1.name} wins by remaining cards (tiebreaker)!")
                        elif len(game.player2.deck) > len(game.player1.deck):
                            print(f"\n🎉 {game.player2.name} wins by remaining cards (tiebreaker)!")
                        else:
                            print("\n⚖️ Game ended in a tie (even score and cards)!")

                game.is_active = False
                self.game_service.repository.save_game(game)
                break

            # Show status
            print(f"\n{'-'*50}")
            print(f"Status:")
            print(f"{game.player1.name}'s deck: {len(game.player1.deck)} cards")
            print(f"{game.player2.name}'s deck: {len(game.player2.deck)} cards")

            # Ask if players want to play next round
            print("\n" + "-" * 50)
            response = input("Ready for next round? (y/n): ").strip().lower()

            if response in ["n", "no", "q", "quit"]:
                print("\nGame paused.")
                print(f"Current round: {game.turn}")
                break

            if response in ["y", "yes", ""]:
                success = self.play_round(game)
                # Show updated round-win score kept on the Game object
                self.keep_score(game)
                if not success:
                    break
            else:
                print(
                    "Invalid response. Please enter 'y' for yes or 'n' for no."
                )

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
        response = (
            input("Would you like to start playing? (y/n): ").strip().lower()
        )

        if response in ["y", "yes", ""]:
            cli.play_game(game)
        else:
            print("\nGame saved. You can continue later!")


if __name__ == "__main__":
    main()
