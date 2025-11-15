"""Unified user management system combining authentication and profile management.

This module handles all user-related operations including account creation, login,
profile viewing, and profile updates. It integrates with the PostgreSQL database
for persistent user data storage.
"""

from database import create_account, username_exists, verify_login, get_user_profile, update_user_password

# Global variable to track the currently logged-in user
current_user = None


def create_account_flow():
    """Handle account creation flow."""
    print("\n=== Create Account ===")
    username = input("Enter username: ").strip()

    if not username:
        print("Username cannot be empty. Please try again.\n")
        return False

    # Clean and validate username
    try:
        username = username.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        print("Invalid characters in username. Please use only standard characters.\n")
        return False

    # Check if username already exists
    if username_exists(username):
        print(
            f"Error: Username '{username}' already exists. Please choose a different username.\n"
        )
        return False

    password = input("Enter password: ").strip()

    if not password:
        print("Password cannot be empty. Please try again.\n")
        return False

    # Clean and validate password
    try:
        password = password.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        print("Invalid characters in password. Please use only standard characters.\n")
        return False

    # Create the account
    if create_account(username, password):
        print(f"\n✓ Account created successfully! Welcome, {username}!\n")
        global current_user
        current_user = username
        return True
    else:
        print(f"Error: Failed to create account. Please try again.\n")
        return False


def login_flow():
    """Handle login flow."""
    print("\n=== Login ===")
    username = input("Enter username: ").strip()

    if not username:
        print("Username cannot be empty. Please try again.\n")
        return False

    # Clean and validate username
    try:
        username = username.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        print("Invalid characters in username.\n")
        return False

    password = input("Enter password: ").strip()

    if not password:
        print("Password cannot be empty. Please try again.\n")
        return False

    # Clean and validate password
    try:
        password = password.encode('utf-8', errors='ignore').decode('utf-8')
    except Exception:
        print("Invalid characters in password.\n")
        return False

    # Verify login credentials
    if verify_login(username, password):
        print(f"\n✓ Login successful! Welcome back, {username}!\n")
        global current_user
        current_user = username
        return True
    else:
        print("Error: Invalid username or password. Please try again.\n")
        return False


def view_profile():
    """Display the current user's profile information."""
    global current_user
    if not current_user:
        print("⚠️  You must be logged in to view your profile.")
        return
    
    profile = get_user_profile(current_user)
    if profile:
        print("\n📋 Your Profile Information:")
        print("=" * 30)
        print(f"👤 Username: {profile['username']}")
        print("=" * 30)
    else:
        print("⚠️  Profile not found.")


def update_profile():
    """Handle profile update flow."""
    global current_user
    if not current_user:
        print("⚠️  You must be logged in to update your profile.")
        return
    
    print("\n=== Update Profile ===")
    print("Leave field empty to keep current value.\n")
    
    # Show current profile
    profile = get_user_profile(current_user)
    if not profile:
        print("⚠️  Profile not found.")
        return
        
    print(f"Current username: {profile['username']}")
    
    # Only allow password updates for now (username changes would be complex)
    new_password = input("New password (press Enter to skip): ").strip()
    
    if new_password:
        if update_user_password(current_user, new_password):
            print("\n✅ Password updated successfully!")
        else:
            print("\n⚠️  Failed to update password. Please try again.")
    else:
        print("\n📝 No changes made.")


def logout():
    """Handle user logout."""
    global current_user
    if current_user:
        username = current_user
        current_user = None
        print(f"\n👋 Goodbye, {username}! You have been logged out.")
        return True
    else:
        print("\n⚠️  You are not currently logged in.")
        return False


def get_current_user():
    """Return the currently logged-in username."""
    return current_user