"""Display leaderboard for the battle card game."""

from database.game_repository import GameRepository


def display_leaderboard():
    """
    Displays the leaderboard showing all players ranked by wins and win rate.
    """
    repository = GameRepository()
    leaderboard = repository.get_leaderboard()

    if not leaderboard:
        print("\n=== Leaderboard ===")
        print("No completed games found. Play some games to see the leaderboard!")
        print("=" * 50 + "\n")
        return

    print("\n" + "=" * 70)
    print("  LEADERBOARD - TOP PLAYERS")
    print("=" * 70)
    print(f"\n{'Rank':<6} {'Player':<20} {'Wins':<8} {'Losses':<8} {'Ties':<8} {'Total':<8} {'Win Rate':<10}")
    print("-" * 70)

    for rank, player in enumerate(leaderboard, 1):
        player_name = player["player_name"]
        wins = player["wins"]
        losses = player["losses"]
        ties = player["ties"]
        total = player["total_games"]
        win_rate = player["win_rate"]

        # Truncate long player names
        if len(player_name) > 18:
            player_name = player_name[:15] + "..."

        print(f"{rank:<6} {player_name:<20} {wins:<8} {losses:<8} {ties:<8} {total:<8} {win_rate:<9}%")

    print("=" * 70)
    print("\n")


if __name__ == "__main__":
    display_leaderboard()

