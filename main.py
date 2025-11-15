from database import init_database
from users.profile import create_account_flow, login_flow, view_profile, update_profile, logout, is_logged_in
from game import play_rps_game, view_card_database, show_card_statistics


def main_menu():
    """Show the main menu after successful login."""
    while True:
        print("\n🎮 Welcome to Battle Cards! 🎮")
        print("\n" + "=" * 40)
        print("BATTLE CARD GAME - MAIN MENU")
        print("=" * 40)
        print("1. Play Rock Paper Scissors Battle")
        print("2. View Profile")
        print("3. Update Profile") 
        print("4. View Card Database")
        print("5. Game Statistics")
        print("6. Logout")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == "1":
            play_rps_game()
        elif choice == "2":
            view_profile()
        elif choice == "3":
            update_profile()
        elif choice == "4":
            view_card_database()
        elif choice == "5":
            show_card_statistics()
        elif choice == "6":
            if logout():
                break
        else:
            print("Invalid choice. Please select 1, 2, 3, 4, 5, or 6.")


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
            if create_account_flow():
                # Account created and user is logged in
                main_menu()
        elif choice == "2":
            if login_flow():
                # User successfully logged in
                main_menu()
        elif choice == "3":
            print("\nThank you for playing!")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()

