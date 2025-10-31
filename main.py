from database import init_database, create_account, username_exists

def main():
    """Main CLI entry point for account creation."""
    # Initialize database on startup
    init_database()
    
    print("=== Battle Card Game - Account Creation ===")
    print()
    
    while True:
        username = input("Enter username: ").strip()
        
        if not username:
            print("Username cannot be empty. Please try again.\n")
            continue
        
        # Check if username already exists
        if username_exists(username):
            print(f"Error: Username '{username}' already exists. Please choose a different username.\n")
            continue
        
        password = input("Enter password: ").strip()
        
        if not password:
            print("Password cannot be empty. Please try again.\n")
            continue
        
        # Create the account
        if create_account(username, password):
            print(f"\n✓ Account created successfully! Welcome, {username}!\n")
        else:
            print(f"Error: Failed to create account. Please try again.\n")
        
        # Ask if user wants to create another account
        again = input("Create another account? (y/n): ").strip().lower()
        if again != 'y':
            break
    
    print("\nThank you for playing!")

if __name__ == "__main__":
    main()

