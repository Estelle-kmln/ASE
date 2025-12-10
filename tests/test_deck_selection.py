"""
Test suite for deck selection feature
Tests the complete flow: create game -> select decks -> start game
"""

import requests
import json
import time
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Base URL
BASE_URL = "https://localhost:8443/api"

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False

# Test users
PLAYER1 = {"username": "decktest_p1", "password": "testpass123"}
PLAYER2 = {"username": "decktest_p2", "password": "testpass123"}

def register_and_login(player):
    """Register and login a test user."""
    # Try to register
    session.post(f"{BASE_URL}/auth/register", json={
        "username": player["username"],
        "password": player["password"]
    })
    
    # Login
    response = session.post(f"{BASE_URL}/auth/login", json={
        "username": player["username"],
        "password": player["password"]
    })
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Login failed: {response.text}")

def test_deck_selection_flow():
    """Test the complete deck selection flow."""
    print("\n" + "="*80)
    print("DECK SELECTION FLOW TEST")
    print("="*80)
    
    # Step 1: Register/login both players
    print("\n1. Registering and logging in players...")
    token1 = register_and_login(PLAYER1)
    token2 = register_and_login(PLAYER2)
    print("✓ Both players logged in")
    
    # Step 2: Player 1 creates a game
    print("\n2. Player 1 creates a game...")
    response = session.post(
        f"{BASE_URL}/games",
        headers={"Authorization": f"Bearer {token1}"},
        json={"player2_name": PLAYER2["username"]}
    )
    assert response.status_code == 201, f"Failed to create game: {response.text}"
    game_data = response.json()
    game_id = game_data["game_id"]
    print(f"✓ Game created: {game_id}")
    print(f"  Status: {game_data['status']}")
    assert game_data["status"] == "deck_selection", "Expected deck_selection status"
    
    # Step 3: Check initial game status
    print("\n3. Checking initial game status...")
    response = session.get(
        f"{BASE_URL}/games/{game_id}/status",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200, f"Failed to get status: {response.text}"
    status = response.json()
    print(f"✓ Status: {status['status']}")
    print(f"  Player 1 deck selected: {status['player1_deck_selected']}")
    print(f"  Player 2 deck selected: {status['player2_deck_selected']}")
    assert not status["player1_deck_selected"], "Player 1 shouldn't have deck selected"
    assert not status["player2_deck_selected"], "Player 2 shouldn't have deck selected"
    
    # Step 4: Player 1 selects manual deck
    print("\n4. Player 1 selects manual deck (8 Rock, 7 Paper, 7 Scissors)...")
    deck1 = (
        [{"type": "Rock"}] * 8 +
        [{"type": "Paper"}] * 7 +
        [{"type": "Scissors"}] * 7
    )
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={"deck": deck1}
    )
    assert response.status_code == 200, f"Failed to select deck: {response.text}"
    result1 = response.json()
    print(f"✓ Deck selected")
    print(f"  Both selected: {result1['both_selected']}")
    print(f"  Status: {result1['status']}")
    print(f"  Deck size: {len(result1['deck'])}")
    assert not result1["both_selected"], "Both shouldn't be selected yet"
    assert result1["status"] == "deck_selection", "Should still be in deck_selection"
    
    # Verify deck has powers assigned
    for i, card in enumerate(result1['deck']):
        assert 'power' in card, f"Card {i} missing power"
        assert 'type' in card, f"Card {i} missing type"
        assert 'id' in card, f"Card {i} missing id"
    print(f"  Sample cards: {result1['deck'][:3]}")
    
    # Step 5: Check status after Player 1 selection
    print("\n5. Checking status after Player 1 selection...")
    response = session.get(
        f"{BASE_URL}/games/{game_id}/status",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 200
    status = response.json()
    print(f"✓ Player 1 deck selected: {status['player1_deck_selected']}")
    print(f"  Player 2 deck selected: {status['player2_deck_selected']}")
    assert status["player1_deck_selected"], "Player 1 should have deck selected"
    assert not status["player2_deck_selected"], "Player 2 shouldn't have deck selected yet"
    
    # Step 6: Player 2 selects random-style deck
    print("\n6. Player 2 selects random-style deck (mixed types)...")
    deck2 = (
        [{"type": "Rock"}] * 8 +
        [{"type": "Paper"}] * 7 +
        [{"type": "Scissors"}] * 7
    )
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token2}"},
        json={"deck": deck2}
    )
    assert response.status_code == 200, f"Failed to select deck: {response.text}"
    result2 = response.json()
    print(f"✓ Deck selected")
    print(f"  Both selected: {result2['both_selected']}")
    print(f"  Status: {result2['status']}")
    assert result2["both_selected"], "Both should be selected now"
    assert result2["status"] == "active", "Should transition to active"
    
    # Step 7: Verify final game status
    print("\n7. Verifying final game status...")
    response = session.get(
        f"{BASE_URL}/games/{game_id}/status",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    status = response.json()
    print(f"✓ Status: {status['status']}")
    print(f"  Player 1 deck selected: {status['player1_deck_selected']}")
    print(f"  Player 2 deck selected: {status['player2_deck_selected']}")
    assert status["status"] == "in_progress", "Should be in_progress (active)"
    assert status["player1_deck_selected"], "Player 1 should have deck selected"
    assert status["player2_deck_selected"], "Player 2 should have deck selected"
    
    # Step 8: Verify game can be retrieved and has correct decks
    print("\n8. Verifying game state...")
    response = session.get(
        f"{BASE_URL}/games/{game_id}",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200, f"Failed to get game: {response.text}"
    game = response.json()
    print(f"✓ Game retrieved")
    print(f"  Player 1 deck size: {game['player1']['deck_size']}")
    print(f"  Player 2 deck size: {game['player2']['deck_size']}")
    assert game['player1']['deck_size'] == 22, "Player 1 should have 22 cards"
    assert game['player2']['deck_size'] == 22, "Player 2 should have 22 cards"
    
    print("\n" + "="*80)
    print("✓ ALL DECK SELECTION TESTS PASSED!")
    print("="*80)
    
    return game_id

def test_deck_selection_validation():
    """Test deck selection validation."""
    print("\n" + "="*80)
    print("DECK SELECTION VALIDATION TEST")
    print("="*80)
    
    # Setup
    print("\n1. Setting up test users and game...")
    token1 = register_and_login(PLAYER1)
    token2 = register_and_login(PLAYER2)
    
    response = session.post(
        f"{BASE_URL}/games",
        headers={"Authorization": f"Bearer {token1}"},
        json={"player2_name": PLAYER2["username"]}
    )
    game_id = response.json()["game_id"]
    print(f"✓ Game created: {game_id}")
    
    # Test 1: Invalid deck size (too few)
    print("\n2. Testing invalid deck size (too few)...")
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={"deck": [{"type": "Rock"}] * 5}
    )
    assert response.status_code == 400, "Should reject deck with wrong size"
    print(f"✓ Rejected: {response.json()['error']}")
    
    # Test 2: Invalid deck size (too many)
    print("\n3. Testing invalid deck size (too many)...")
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={"deck": [{"type": "Rock"}] * 15}
    )
    assert response.status_code == 400, "Should reject deck with wrong size"
    print(f"✓ Rejected: {response.json()['error']}")
    
    # Test 3: Invalid card type
    print("\n4. Testing invalid card type...")
    invalid_deck = [{"type": "InvalidType"}] * 10
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={"deck": invalid_deck}
    )
    assert response.status_code == 400, "Should reject invalid card type"
    print(f"✓ Rejected: {response.json()['error']}")
    
    # Test 4: Missing deck field
    print("\n5. Testing missing deck field...")
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={}
    )
    assert response.status_code == 400, "Should reject missing deck"
    print(f"✓ Rejected: {response.json()['error']}")
    
    # Test 5: Valid deck
    print("\n6. Testing valid deck...")
    valid_deck = [{"type": "Rock"}] * 22
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={"deck": valid_deck}
    )
    assert response.status_code == 200, f"Should accept valid deck: {response.text}"
    print("✓ Valid deck accepted")
    
    # Test 6: Try to select deck again (should fail)
    print("\n7. Testing duplicate deck selection...")
    response = session.post(
        f"{BASE_URL}/games/{game_id}/select-deck",
        headers={"Authorization": f"Bearer {token1}"},
        json={"deck": valid_deck}
    )
    assert response.status_code == 400, "Should reject duplicate deck selection"
    print(f"✓ Rejected: {response.json()['error']}")
    
    print("\n" + "="*80)
    print("✓ ALL VALIDATION TESTS PASSED!")
    print("="*80)

if __name__ == "__main__":
    try:
        # Run tests
        test_deck_selection_flow()
        print("\n")
        test_deck_selection_validation()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
