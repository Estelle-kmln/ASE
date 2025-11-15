"""Module for displaying the full card collection."""

from database import get_all_cards


def get_full_card_collection():
    """
    Get the full card collection from the database.

    Returns:
        A list of all card dictionaries from the database.
    """
    return get_all_cards()


def display_card_collection():
    """
    Print all cards in the collection in a structured, readable format.
    """
    print("\n" + "=" * 50)
    print("🃏  CARD COLLECTION - ALL AVAILABLE CARDS")
    print("=" * 50)

    all_cards = get_full_card_collection()
    
    # Group by type
    rock_cards = [c for c in all_cards if c['type'].lower() == 'rock']
    paper_cards = [c for c in all_cards if c['type'].lower() == 'paper']
    scissors_cards = [c for c in all_cards if c['type'].lower() == 'scissors']

    for card_type, cards in [('Rock', rock_cards), ('Paper', paper_cards), ('Scissors', scissors_cards)]:
        print(f"\n{card_type.upper()} CARDS:")
        print("-" * 50)
        for card in sorted(cards, key=lambda x: x['power']):
            print(f"  {card['type']} {card['power']}")
    
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    display_card_collection()
