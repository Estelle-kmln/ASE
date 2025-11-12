"""Main entry point for the battle card game."""

from profile import get_profile, update_profile, create_profile

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
