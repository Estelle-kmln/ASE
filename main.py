"""Main entry point for the battle card game."""
from profile import get_profile, update_profile, create_profile
from view_old_matches import display_old_matches

# Support importing both as a package (import ASE.main) and running the
# file directly (python ASE/main.py). Try package-style import first and
# fall back to the module path used when the file is executed as a script.
try:
    # When running via `python -m ASE.main` or importing the package
    from ASE.cli.main import CLI
except Exception:
    # When running the file directly (python ASE/main.py) the package
    # context may not be set; import using the module path relative to
    # the ASE directory.
    from cli.main import CLI

def main():
    """Main entry point."""
    cli = CLI()

#Offer to view past matches before starting a new game
    print("\n" + "-" * 50)
    choice = input("Do you want to view your past matches? (y/n): ").strip().lower()
    if choice in ["y", "yes"]:
        player_name = input("Enter your player name: ").strip().lower()
        display_old_matches(player_name)

 #  Ask before starting a new game
    print("\n" + "-" * 50)
    start_choice = input("Do you want to start a new game? (y/n): ").strip().lower()
    if start_choice not in ["y", "yes", ""]:
        print("Okay! Exiting for now. See you next time!")
        return  # Exit program

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
