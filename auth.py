"""Authentication flows for user account management."""

from database import create_account, username_exists, verify_login


def create_account_flow():
    """Handle account creation flow."""
    print("\n=== Create Account ===")
    username = input("Enter username: ").strip()

    if not username:
        print("Username cannot be empty. Please try again.\n")
        return

    # Check if username already exists
    if username_exists(username):
        print(
            f"Error: Username '{username}' already exists. Please choose a different username.\n"
        )
        return

    password = input("Enter password: ").strip()

    if not password:
        print("Password cannot be empty. Please try again.\n")
        return

    # Create the account
    if create_account(username, password):
        print(f"\n✓ Account created successfully! Welcome, {username}!\n")
    else:
        print(f"Error: Failed to create account. Please try again.\n")


def login_flow():
    """Handle login flow."""
    print("\n=== Login ===")
    username = input("Enter username: ").strip()

    if not username:
        print("Username cannot be empty. Please try again.\n")
        return False

    password = input("Enter password: ").strip()

    if not password:
        print("Password cannot be empty. Please try again.\n")
        return False

    # Verify login credentials
    if verify_login(username, password):
        print(f"\n✓ Login successful! Welcome back, {username}!\n")
        return True
    else:
        print("Error: Invalid username or password. Please try again.\n")
        return False

