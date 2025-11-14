# USER STORY: As a player, I want to check or modify my profile so that I can update my information

# Simulated database
users = {
    "player1": {"username": "player1", "email": "player1@example.com"}
}

# Currently logged-in user (None until logged in or created)
current_user = None


def create_profile(username, email):
    """
    Create a new user profile if username is not taken.
    """
    if username in users:
        print("⚠️  That username already exists. Please choose another one.")
        return None

    users[username] = {"username": username, "email": email}
    print(f"✅ Profile created successfully for '{username}'!")
    return username


def get_profile():
    """
    Return the profile of the currently logged-in user.
    """
    global current_user  # <-- added this line
    if current_user and current_user in users:
        return users[current_user]
    return None


def update_profile(new_data: dict):
    """
    Update the profile of the currently logged-in user.
    """
    global current_user  # <-- added this line
    if not current_user or current_user not in users:
        print("⚠️  No profile logged in.")
        return None

    user = users[current_user]

    for key in ["username", "email"]:
        if key in new_data and new_data[key]:
            user[key] = new_data[key]

    return user


def show_menu():
    """
    Show the main menu for profile management.
    """
    global current_user

    while True:
        print("\n--- PROFILE MENU ---")
        print("1. Create profile")
        print("2. View profile")
        print("3. Update profile")
        print("4. Exit")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            print("\n--- Create a new profile ---")
            username = input("Enter username: ").strip()
            email = input("Enter email: ").strip()
            if username and email:
                created_user = create_profile(username, email)
                if created_user:
                    current_user = created_user
            else:
                print("⚠️  Username and email cannot be empty.")

        elif choice == "2":
            profile = get_profile()
            if profile:
                print("\nYour current profile:")
                print(f"Username: {profile['username']}")
                print(f"Email: {profile['email']}")
            else:
                print("⚠️  No profile found or logged in.")

        elif choice == "3":
            if not current_user:
                print("⚠️  You need to create or select a profile first.")
                continue

            print("\n--- Update your profile ---")
            username = input("New username (press Enter to skip): ").strip()
            email = input("New email (press Enter to skip): ").strip()

            updated = update_profile({"username": username, "email": email})
            if updated:
                print("\n✅ Profile successfully updated!")
                print(f"New username: {updated['username']}")
                print(f"New email: {updated['email']}")
            else:
                print("⚠️  Failed to update profile.")

        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    show_menu()