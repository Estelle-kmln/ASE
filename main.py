from database import init_database
from auth import create_account_flow, login_flow
from game import game_menu


def main():
    """Main CLI entry point."""
    # Initialize database on startup
    init_database()
    
    print("=== Battle Card Game ===")
    
    while True:
        print("\n1. Create Account")
        print("2. Login")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == "1":
            create_account_flow()
        elif choice == "2":
            if login_flow():
                # User successfully logged in - start the game!
                game_menu()
                break
        elif choice == "3":
            print("\nThank you for playing!")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()

