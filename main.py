"""Main entry point for the battle card game."""

from cli.main import CLI


def main():
    """Main entry point."""
    cli = CLI()
    cli.start_new_game()


if __name__ == "__main__":
    main()
