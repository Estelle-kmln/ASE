"""
Comprehensive test for game completion and leaderboard integration.
Tests the complete flow: create game, play to completion, verify leaderboard.
"""

import requests
import time
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8443"

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False

def register_user(username, password):
    """Register a new user and return the token."""
    response = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"username": username, "password": password}
    )
    if response.status_code == 201:
        return response.json().get('access_token')
    return None

def create_game(token, player2_name):
    """Create a game invitation."""
    response = session.post(
        f"{BASE_URL}/api/games",
        headers={"Authorization": f"Bearer {token}"},
        json={"player2_name": player2_name}
    )
    if response.status_code == 201:
        return response.json().get('game_id')
    return None

def draw_hand(token, game_id):
    """Draw a hand of cards."""
    response = session.post(
        f"{BASE_URL}/api/games/{game_id}/draw-hand",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return None

def play_card(token, game_id, card_index):
    """Play a card."""
    response = session.post(
        f"{BASE_URL}/api/games/{game_id}/play-card",
        headers={"Authorization": f"Bearer {token}"},
        json={"card_index": card_index}
    )
    return response.status_code == 200, response.json()

def get_game_state(token, game_id):
    """Get the current game state."""
    response = session.get(
        f"{BASE_URL}/api/games/{game_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_leaderboard(token):
    """Get the leaderboard."""
    response = session.get(
        f"{BASE_URL}/api/leaderboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def get_player_stats(token, username):
    """Get player statistics."""
    response = session.get(
        f"{BASE_URL}/api/leaderboard/player/{username}",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def play_complete_game(p1_token, p2_token, game_id):
    """Play a game to completion (or until one player runs out of cards)."""
    rounds_played = 0
    max_rounds = 15  # Safety limit
    
    while rounds_played < max_rounds:
        # Get game state
        game_state = get_game_state(p1_token, game_id)
        
        if not game_state:
            print("❌ Failed to get game state")
            return False
        
        # Check if game is over
        if game_state['game_status'] in ['completed', 'abandoned', 'ignored']:
            print(f"✅ Game completed after {rounds_played} rounds")
            print(f"   Winner: {game_state.get('winner', 'No winner')}")
            print(f"   Final Score: {game_state['player1']['score']} - {game_state['player2']['score']}")
            return True
        
        print(f"\n--- Round {rounds_played + 1} ---")
        
        # Player 1 draws
        if not game_state['player1']['has_drawn']:
            print("Player 1 drawing...")
            draw_result = draw_hand(p1_token, game_id)
            if not draw_result:
                print("❌ Player 1 failed to draw")
                return False
            print(f"Player 1 drew {len(draw_result['hand'])} cards")
        
        # Player 2 draws
        game_state = get_game_state(p1_token, game_id)
        if not game_state['player2']['has_drawn']:
            print("Player 2 drawing...")
            draw_result = draw_hand(p2_token, game_id)
            if not draw_result:
                print("❌ Player 2 failed to draw")
                return False
            print(f"Player 2 drew {len(draw_result['hand'])} cards")
        
        # Player 1 plays
        game_state = get_game_state(p1_token, game_id)
        if not game_state['player1']['has_played']:
            print("Player 1 playing card 0...")
            success, result = play_card(p1_token, game_id, 0)
            if not success:
                print(f"❌ Player 1 failed to play: {result}")
                return False
        
        # Player 2 plays
        game_state = get_game_state(p1_token, game_id)
        if not game_state['player2']['has_played']:
            print("Player 2 playing card 0...")
            success, result = play_card(p2_token, game_id, 0)
            if not success:
                print(f"❌ Player 2 failed to play: {result}")
                return False
            
            if result.get('round_resolved'):
                print(f"Round resolved: {result.get('round_result', {})}")
        
        rounds_played += 1
        time.sleep(0.5)  # Small delay between rounds
    
    print(f"⚠️  Game didn't complete after {max_rounds} rounds")
    return False

def main():
    print("=" * 70)
    print("Testing Complete Game Flow and Leaderboard Integration")
    print("=" * 70)
    
    # Create two test users
    timestamp = int(time.time() * 1000)
    player1_username = f"complete_p1_{timestamp}"
    player2_username = f"complete_p2_{timestamp}"
    password = "test123"
    
    print(f"\n1. Registering test users...")
    player1_token = register_user(player1_username, password)
    player2_token = register_user(player2_username, password)
    
    if not player1_token or not player2_token:
        print("❌ Failed to register users")
        return
    print(f"✅ Users registered: {player1_username}, {player2_username}")
    
    # Get initial stats
    print(f"\n2. Checking initial stats (should be 0 games)...")
    p1_stats_before = get_player_stats(player1_token, player1_username)
    p2_stats_before = get_player_stats(player2_token, player2_username)
    print(f"   Player 1: {p1_stats_before['total_games']} games")
    print(f"   Player 2: {p2_stats_before['total_games']} games")
    
    # Create game
    print(f"\n3. Player 1 creating game...")
    game_id = create_game(player1_token, player2_username)
    
    if not game_id:
        print("❌ Failed to create game")
        return
    print(f"✅ Game created: {game_id}")
    
    # Play the game to completion
    print(f"\n4. Playing game to completion...")
    if not play_complete_game(player1_token, player2_token, game_id):
        print("❌ Failed to complete game")
        return
    
    # Check final game state
    print(f"\n5. Checking final game state...")
    final_state = get_game_state(player1_token, game_id)
    print(f"   game_status: {final_state['game_status']}")
    print(f"   Winner: {final_state.get('winner', 'No winner')}")
    
    # Small delay to ensure database is updated
    time.sleep(1)
    
    # Check stats after playing
    print(f"\n6. Checking stats after game (should be 1 game each)...")
    p1_stats_after = get_player_stats(player1_token, player1_username)
    p2_stats_after = get_player_stats(player2_token, player2_username)
    print(f"   Player 1: {p1_stats_after['total_games']} games, {p1_stats_after['wins']} wins")
    print(f"   Player 2: {p2_stats_after['total_games']} games, {p2_stats_after['wins']} wins")
    
    # Verify the counts increased
    print(f"\n7. Verification:")
    success = True
    
    if p1_stats_after['total_games'] != 1:
        print(f"❌ Player 1 should have 1 game, has {p1_stats_after['total_games']}")
        success = False
    
    if p2_stats_after['total_games'] != 1:
        print(f"❌ Player 2 should have 1 game, has {p2_stats_after['total_games']}")
        success = False
    
    if success:
        print("✅ SUCCESS: Completed games ARE counted in statistics!")
    
    # Check leaderboard
    print(f"\n8. Checking leaderboard...")
    leaderboard = get_leaderboard(player1_token)
    
    # Check if our test users appear in leaderboard
    test_users_in_leaderboard = [
        entry for entry in leaderboard['leaderboard']
        if entry['player'] in [player1_username, player2_username]
    ]
    
    if len(test_users_in_leaderboard) == 2:
        print("✅ SUCCESS: Both players appear in leaderboard!")
        for entry in test_users_in_leaderboard:
            print(f"   {entry['player']}: Rank {entry['rank']}, {entry['wins']} wins, {entry['games']} games")
    else:
        print(f"❌ FAIL: Expected 2 users in leaderboard, found {len(test_users_in_leaderboard)}")
        success = False
    
    print(f"\n" + "=" * 70)
    if success:
        print("All tests PASSED! ✅")
    else:
        print("Some tests FAILED! ❌")
    print("=" * 70)

if __name__ == "__main__":
    main()
