"""View details of a specific match in the Battle Card Game."""

from database.game_repository import GameRepository
from models.card import Card
from models.game import Hand
from datetime import datetime


def format_card(card: Card) -> str:
    """Format card nicely for printing."""
    return f"{card.value} of {card.suit.capitalize()}"


def view_match_details():
    """Allow a player to view details of one of their matches."""
    repo = GameRepository()
    games = repo.list_games()

    if not games:
        print("\n⚠️  No games found in the database.")
        return

    print("\n=== Saved Matches ===")
    for i, game in enumerate(games, start=1):
        status = "ACTIVE" if game["is_active"] else "FINISHED"
        created_at = game["created_at"]
        if isinstance(created_at, str):
            created_at = created_at.split(".")[0]
        print(f"{i}. ID: {game['game_id']} | Turn: {game['turn']} | Status: {status} | Created: {created_at}")

    # Let user pick a game
    try:
        choice = int(input("\nEnter the number of the match to view details: "))
        if choice < 1 or choice > len(games):
            print("❌ Invalid selection.")
            return
    except ValueError:
        print("❌ Please enter a valid number.")
        return

    selected_game_id = games[choice - 1]["game_id"]
    game = repo.load_game(selected_game_id)

    if not game:
        print("❌ Could not load selected match.")
        return

    # Display details
    print("\n=== Match Details ===")
    print(f"Game ID: {game.game_id}")
    print(f"Turn: {game.turn}")
    print(f"Active: {'Yes' if game.is_active else 'No'}")
    print(f"Current Player: {game.current_player.name}")
    print("\n--- Player 1 ---")
    print(f"Name: {game.player1.name}")
    print(f"Remaining cards in deck: {len(game.player1.deck.cards)}")

    if game.player1.hand:
        print("Current hand:")
        for card in game.player1.hand.cards:
            print(f"  - {format_card(card)}")
        if game.player1.hand.played_card:
            print(f"Played card: {format_card(game.player1.hand.played_card)}")
        if game.player1.hand.discarded_cards:
            print("Discarded cards:")
            for card in game.player1.hand.discarded_cards:
                print(f"  - {format_card(card)}")

    print("\n--- Player 2 ---")
    print(f"Name: {game.player2.name}")
    print(f"Remaining cards in deck: {len(game.player2.deck.cards)}")

    if game.player2.hand:
        print("Current hand:")
        for card in game.player2.hand.cards:
            print(f"  - {format_card(card)}")
        if game.player2.hand.played_card:
            print(f"Played card: {format_card(game.player2.hand.played_card)}")
        if game.player2.hand.discarded_cards:
            print("Discarded cards:")
            for card in game.player2.hand.discarded_cards:
                print(f"  - {format_card(card)}")

    print("\n✅ End of match details.\n")


if __name__ == "__main__":
    view_match_details()
