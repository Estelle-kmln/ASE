"""Game logic for the battle card game."""

import random
from database import get_all_cards, get_cards_by_type, get_card_by_id


def display_card(card):
    """Display a card in a formatted way."""
    print(f"\n┌─ {card['name']} ─┐")
    print(f"│ Type: {card['type'].title()}")
    print(f"│ Cost: {card['cost']}")
    if card['attack'] is not None:
        print(f"│ Attack: {card['attack']}")
    if card['defense'] is not None:
        print(f"│ Defense: {card['defense']}")
    if card['damage'] is not None:
        print(f"│ Damage: {card['damage']}")
    if card['healing'] is not None:
        print(f"│ Healing: {card['healing']}")
    if card['defense_boost'] is not None:
        print(f"│ Defense Boost: {card['defense_boost']}")
    print(f"│ Rarity: {card['rarity'].title()}")
    print(f"│ {card['description']}")
    print("└─────────────────┘")


def view_all_cards():
    """Display all available cards."""
    print("\n=== All Cards ===")
    cards = get_all_cards()
    
    if not cards:
        print("No cards found in the database.")
        return
    
    for card in cards:
        display_card(card)
    
    print(f"\nTotal cards: {len(cards)}")


def view_cards_by_type():
    """Display cards filtered by type."""
    print("\n=== View Cards by Type ===")
    print("1. Creatures")
    print("2. Spells")
    print("3. All Cards")
    
    choice = input("\nSelect card type (1-3): ").strip()
    
    if choice == "1":
        cards = get_cards_by_type("creature")
        print("\n=== Creature Cards ===")
    elif choice == "2":
        cards = get_cards_by_type("spell")
        print("\n=== Spell Cards ===")
    elif choice == "3":
        view_all_cards()
        return
    else:
        print("Invalid choice.")
        return
    
    if not cards:
        print("No cards found.")
        return
    
    for card in cards:
        display_card(card)
    
    print(f"\nTotal cards: {len(cards)}")


def build_random_deck():
    """Build a random deck of 5 cards."""
    print("\n=== Building Random Deck ===")
    all_cards = get_all_cards()
    
    if len(all_cards) < 5:
        print("Not enough cards in database to build a deck.")
        return None
    
    deck = random.sample(all_cards, 5)
    
    print("Your random deck:")
    for i, card in enumerate(deck, 1):
        print(f"\n{i}. {card['name']} (Cost: {card['cost']}, Rarity: {card['rarity']})")
    
    return deck


def simple_battle():
    """Simulate a simple battle with random cards."""
    print("\n=== Simple Battle Simulation ===")
    
    # Get random creature cards for battle
    creatures = get_cards_by_type("creature")
    if len(creatures) < 2:
        print("Not enough creature cards for battle.")
        return
    
    # Pick two random creatures
    player_card, enemy_card = random.sample(creatures, 2)
    
    print(f"\nYour card:")
    display_card(player_card)
    
    print(f"\nEnemy card:")
    display_card(enemy_card)
    
    # Simple battle logic
    player_attack = player_card['attack'] or 0
    player_defense = player_card['defense'] or 0
    enemy_attack = enemy_card['attack'] or 0
    enemy_defense = enemy_card['defense'] or 0
    
    print("\n⚔️  Battle Results:")
    print(f"Your {player_card['name']} attacks for {player_attack} damage!")
    print(f"Enemy {enemy_card['name']} attacks for {enemy_attack} damage!")
    
    # Determine winner based on attack vs defense
    player_damage_dealt = max(0, player_attack - enemy_defense)
    enemy_damage_dealt = max(0, enemy_attack - player_defense)
    
    print(f"\nDamage dealt to enemy: {player_damage_dealt}")
    print(f"Damage dealt to you: {enemy_damage_dealt}")
    
    if player_damage_dealt > enemy_damage_dealt:
        print(f"\n🎉 Victory! Your {player_card['name']} wins!")
    elif enemy_damage_dealt > player_damage_dealt:
        print(f"\n💀 Defeat! Enemy {enemy_card['name']} wins!")
    else:
        print("\n⚖️ It's a tie! Both creatures survive!")


def card_collection_stats():
    """Show statistics about the card collection."""
    print("\n=== Card Collection Statistics ===")
    
    all_cards = get_all_cards()
    creatures = get_cards_by_type("creature")
    spells = get_cards_by_type("spell")
    
    print(f"Total Cards: {len(all_cards)}")
    print(f"Creatures: {len(creatures)}")
    print(f"Spells: {len(spells)}")
    
    # Rarity breakdown
    rarity_counts = {}
    for card in all_cards:
        rarity = card['rarity']
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
    
    print("\nRarity Breakdown:")
    for rarity, count in sorted(rarity_counts.items()):
        print(f"  {rarity.title()}: {count}")
    
    # Cost distribution
    cost_counts = {}
    for card in all_cards:
        cost = card['cost']
        cost_counts[cost] = cost_counts.get(cost, 0) + 1
    
    print("\nCost Distribution:")
    for cost in sorted(cost_counts.keys()):
        print(f"  Cost {cost}: {cost_counts[cost]} cards")


def game_menu():
    """Main game menu after login."""
    print("\n🎮 Welcome to Battle Cards! 🎮")
    
    while True:
        print("\n" + "="*40)
        print("BATTLE CARD GAME - MAIN MENU")
        print("="*40)
        print("1. View All Cards")
        print("2. View Cards by Type")
        print("3. Build Random Deck")
        print("4. Simple Battle")
        print("5. Collection Statistics")
        print("6. Logout")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
        try:
            if choice == "1":
                view_all_cards()
            elif choice == "2":
                view_cards_by_type()
            elif choice == "3":
                build_random_deck()
            elif choice == "4":
                simple_battle()
            elif choice == "5":
                card_collection_stats()
            elif choice == "6":
                print("\nLogging out... Thanks for playing!")
                break
            else:
                print("Invalid choice. Please select 1-6.")
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again.")