"""Module for displaying the full card collection."""

from models.card import Card


def get_full_card_collection() -> list[Card]:
    """
    Generate the full card collection of 39 cards (13 values × 3 suits).

    Returns:
        A list of all Card objects.
    """
    suits = ["rock", "paper", "scissors"]
    values = list(range(1, 14))  # 1 to 13
    return [Card(value, suit) for suit in suits for value in values]


def display_card_collection():
    """
    Print all cards in the collection in a structured, readable format.
    """
    print("\n" + "=" * 50)
    print("🃏  CARD COLLECTION - ALL AVAILABLE CARDS")
    print("=" * 50)

    suits = ["rock", "paper", "scissors"]
    all_cards = get_full_card_collection()

    for suit in suits:
        print(f"\n{suit.upper()} CARDS:")
        print("-" * 50)
        suit_cards = [card for card in all_cards if card.suit == suit]
        for card in suit_cards:
            print(f"  {card.suit.capitalize()} {card.value}")
    
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    display_card_collection()
