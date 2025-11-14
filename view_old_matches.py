import sqlite3
from datetime import datetime

DB_PATH = "game.db"

def get_old_matches(player_name: str):
    """
    Fetches a list of finished matches for the given player from the SQLite database.
    A match is considered 'finished' if is_active = 0.
    Returns game_id, player1_name, player2_name, winner, player1_score, player2_score, created_at
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Select matches where player participated and the game is finished (is_active = 0)
    # Include winner and scores
    cursor.execute("""
        SELECT game_id, player1_name, player2_name, winner, player1_score, player2_score, created_at
        FROM games
        WHERE (player1_name = ? OR player2_name = ?)
        AND is_active = 0
        ORDER BY created_at DESC
    """, (player_name, player_name))

    matches = cursor.fetchall()
    conn.close()
    return matches


def display_old_matches(player_name: str):
    """
    Displays the player's past matches in a readable format.
    """
    matches = get_old_matches(player_name)

    if not matches:
        print(f"No old matches found for player '{player_name}'.")
        return

    print(f"\n=== Past Matches for {player_name} ===\n")
    for match in matches:
        game_id, p1, p2, winner, p1_score, p2_score, created_at = match

        # Convert timestamp to readable format
        try:
            created_at = datetime.fromisoformat(created_at)
            created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
        except Exception:
            created_at_str = str(created_at)

        # Handle None values for scores (old games might not have scores)
        p1_score = p1_score if p1_score is not None else 0
        p2_score = p2_score if p2_score is not None else 0

        # Display match information
        print(f"Game ID: {game_id}")
        print(f"Players: {p1} vs {p2}")
        print(f"Score: {p1} {p1_score} - {p2_score} {p2}")
        
        # Display winner
        if winner:
            print(f"Winner: {winner} 🎉")
        else:
            print("Result: Tie ⚖️")
        
        print(f"Date: {created_at_str}")
        print("-" * 40)


if __name__ == "__main__":
    player = input("Enter your player name: ").strip().lower()
    display_old_matches(player)
