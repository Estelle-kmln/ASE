# Simulated database
users = {
    "player1": {"username": "player1", "email": "player1@example.com"}
}

# Currently logged-in user
current_user = "player1"


def get_profile():
    """
    Return the profile of the currently logged-in user.
    """
    user = users.get(current_user)
    if user:
        return user
    return None


def update_profile(new_data: dict):
    """
    Update the profile of the currently logged-in user, 
    new data can cointain: {"username":...,"email":...}
    """
    user = users.get(current_user)
    if not user:
        return None

    for key in ["username", "email"]:
        if key in new_data and new_data[key]:
            user[key] = new_data[key]

    return user


# CLI testing
if __name__ == "__main__":
    print("Current profile:", get_profile())

    username = input("New username (press enter to skip): ").strip()
    email = input("New email (press enter to skip): ").strip()

    updated = update_profile({"username": username, "email": email})
    print("Profile after update:", updated)
