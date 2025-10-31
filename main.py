"""Main entry point for the battle card game."""

from cli.main import CLI


def main():
    """Main entry point."""
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
