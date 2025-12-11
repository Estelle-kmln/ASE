"""
Unit tests for Leaderboard Service endpoints
Tests all leaderboard service methods with valid and invalid inputs.
"""

import unittest
import requests
import time
import os
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Gateway base URL
BASE_URL = os.getenv('BASE_URL', 'https://localhost:8443')

# Create a session with SSL verification disabled for self-signed certs
session = requests.Session()
session.verify = False


class TestLeaderboardServiceSetup(unittest.TestCase):
    """Setup class to get authentication token for tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up authentication token for all leaderboard service tests."""
        cls.unique_id = int(time.time() * 1000)
        cls.test_username = f"lbuser_{cls.unique_id}"
        cls.test_password = "LbPass123!"
        
        # Register and get token
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": cls.test_username, "password": cls.test_password}
        )
        cls.token = response.json().get('access_token')
        cls.headers = {"Authorization": f"Bearer {cls.token}"}


class TestLeaderboardServiceGetLeaderboard(TestLeaderboardServiceSetup):
    """Test cases for GET /api/leaderboard endpoint."""
    
    def test_get_leaderboard_success(self):
        """Test successfully retrieving the global leaderboard."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('leaderboard', data)
        self.assertIn('total_players', data)
        self.assertIsInstance(data['leaderboard'], list)
        
        # Verify leaderboard entry structure if entries exist
        if len(data['leaderboard']) > 0:
            entry = data['leaderboard'][0]
            self.assertIn('rank', entry)
            self.assertIn('player', entry)
            self.assertIn('wins', entry)
            self.assertIn('games', entry)
            self.assertIn('losses', entry)
            self.assertIn('win_percentage', entry)
    
    def test_get_leaderboard_with_limit(self):
        """Test retrieving leaderboard with custom limit."""
        limit = 5
        response = session.get(
            f"{BASE_URL}/api/leaderboard?limit={limit}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('leaderboard', data)
        # Should return at most 'limit' entries
        self.assertLessEqual(len(data['leaderboard']), limit)
    
    def test_get_leaderboard_limit_exceeds_max(self):
        """Test that limit is capped at 100 even if higher requested."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard?limit=200",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should cap at 100 even if we requested 200
        self.assertLessEqual(len(data['leaderboard']), 100)
    
    def test_get_leaderboard_no_token(self):
        """Test getting leaderboard fails without authentication token."""
        response = session.get(f"{BASE_URL}/api/leaderboard")
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_leaderboard_invalid_token(self):
        """Test getting leaderboard fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(
            f"{BASE_URL}/api/leaderboard",
            headers=invalid_headers
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_leaderboard_ranking_order(self):
        """Test that leaderboard is ordered correctly by rank."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            leaderboard = data['leaderboard']
            
            # Verify ranks are sequential starting from 1
            for i, entry in enumerate(leaderboard, 1):
                self.assertEqual(entry['rank'], i)


class TestLeaderboardServiceGetPlayerStats(TestLeaderboardServiceSetup):
    """Test cases for GET /api/leaderboard/player/<player_name> endpoint."""
    
    def test_get_player_stats_success(self):
        """Test successfully retrieving player statistics."""
        # Use our own username for testing
        response = session.get(
            f"{BASE_URL}/api/leaderboard/player/{self.test_username}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('player', data)
        self.assertIn('wins', data)
        self.assertIn('losses', data)
        self.assertIn('total_games', data)
        self.assertIn('win_percentage', data)
        self.assertIn('recent_games', data)
        self.assertEqual(data['player'], self.test_username)
        self.assertIsInstance(data['recent_games'], list)
    
    def test_get_player_stats_nonexistent_player(self):
        """Test getting stats for non-existent player returns empty stats."""
        fake_player = "nonexistent_player_12345"
        response = session.get(
            f"{BASE_URL}/api/leaderboard/player/{fake_player}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should return zeros for non-existent player
        self.assertEqual(data['wins'], 0)
        self.assertEqual(data['losses'], 0)
        self.assertEqual(data['total_games'], 0)
    
    def test_get_player_stats_no_token(self):
        """Test getting player stats fails without token."""
        response = session.get(f"{BASE_URL}/api/leaderboard/player/{self.test_username}")
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_player_stats_invalid_token(self):
        """Test getting player stats fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(
            f"{BASE_URL}/api/leaderboard/player/{self.test_username}",
            headers=invalid_headers
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_player_stats_recent_games_structure(self):
        """Test recent games have correct structure."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/player/{self.test_username}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            recent_games = data['recent_games']
            
            # Verify structure if games exist
            for game in recent_games:
                self.assertIn('game_id', game)
                self.assertIn('opponent', game)
                self.assertIn('player_score', game)
                self.assertIn('opponent_score', game)
                self.assertIn('result', game)
                self.assertIn('date', game)
                self.assertIn(game['result'], ['win', 'loss', 'tie'])


class TestLeaderboardServiceGetRecentGames(TestLeaderboardServiceSetup):
    """Test cases for GET /api/leaderboard/recent-games endpoint."""
    
    def test_get_recent_games_success(self):
        """Test successfully retrieving recent completed games."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/recent-games",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('recent_games', data)
        self.assertIn('total_games', data)
        self.assertIsInstance(data['recent_games'], list)
        
        # Verify game structure if games exist
        if len(data['recent_games']) > 0:
            game = data['recent_games'][0]
            self.assertIn('game_id', game)
            self.assertIn('player1_name', game)
            self.assertIn('player2_name', game)
            self.assertIn('player1_score', game)
            self.assertIn('player2_score', game)
            self.assertIn('winner', game)
            self.assertIn('duration_turns', game)
    
    def test_get_recent_games_with_limit(self):
        """Test retrieving recent games with custom limit."""
        limit = 5
        response = session.get(
            f"{BASE_URL}/api/leaderboard/recent-games?limit={limit}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should return at most 'limit' entries
        self.assertLessEqual(len(data['recent_games']), limit)
    
    def test_get_recent_games_limit_exceeds_max(self):
        """Test that limit is capped at 50 even if higher requested."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/recent-games?limit=100",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should cap at 50 even if we requested 100
        self.assertLessEqual(len(data['recent_games']), 50)
    
    def test_get_recent_games_no_token(self):
        """Test getting recent games fails without token."""
        response = session.get(f"{BASE_URL}/api/leaderboard/recent-games")
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_recent_games_invalid_token(self):
        """Test getting recent games fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(
            f"{BASE_URL}/api/leaderboard/recent-games",
            headers=invalid_headers
        )
        
        self.assertEqual(response.status_code, 401)


class TestLeaderboardServiceGetTopPlayers(TestLeaderboardServiceSetup):
    """Test cases for GET /api/leaderboard/top-players endpoint."""
    
    def test_get_top_players_success(self):
        """Test successfully retrieving top players by various metrics."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/top-players",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('top_by_wins', data)
        self.assertIn('top_by_win_percentage', data)
        self.assertIn('most_active', data)
        
        # Verify each list structure
        for player in data['top_by_wins']:
            self.assertIn('player', player)
            self.assertIn('wins', player)
        
        for player in data['top_by_win_percentage']:
            self.assertIn('player', player)
            self.assertIn('wins', player)
            self.assertIn('games', player)
            self.assertIn('win_percentage', player)
        
        for player in data['most_active']:
            self.assertIn('player', player)
            self.assertIn('total_games', player)
    
    def test_get_top_players_no_token(self):
        """Test getting top players fails without token."""
        response = session.get(f"{BASE_URL}/api/leaderboard/top-players")
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_top_players_invalid_token(self):
        """Test getting top players fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(
            f"{BASE_URL}/api/leaderboard/top-players",
            headers=invalid_headers
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_top_players_list_sizes(self):
        """Test that each top players list is limited appropriately."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/top-players",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            # Each list should have at most 5 entries
            self.assertLessEqual(len(data['top_by_wins']), 5)
            self.assertLessEqual(len(data['top_by_win_percentage']), 5)
            self.assertLessEqual(len(data['most_active']), 5)


class TestLeaderboardServiceGetStatistics(TestLeaderboardServiceSetup):
    """Test cases for GET /api/leaderboard/statistics endpoint."""
    
    def test_get_statistics_success(self):
        """Test successfully retrieving global game statistics."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/statistics",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_completed_games', data)
        self.assertIn('unique_players', data)
        self.assertIn('games_with_winner', data)
        self.assertIn('tied_games', data)
        self.assertIn('average_game_turns', data)
        self.assertIn('shortest_game_turns', data)
        self.assertIn('longest_game_turns', data)
        self.assertIn('games_last_week', data)
        
        # Verify data types
        self.assertIsInstance(data['total_completed_games'], int)
        self.assertIsInstance(data['unique_players'], int)
        self.assertIsInstance(data['games_with_winner'], int)
        self.assertIsInstance(data['tied_games'], int)
    
    def test_get_statistics_no_token(self):
        """Test getting statistics fails without token."""
        response = session.get(f"{BASE_URL}/api/leaderboard/statistics")
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_statistics_invalid_token(self):
        """Test getting statistics fails with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = session.get(
            f"{BASE_URL}/api/leaderboard/statistics",
            headers=invalid_headers
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_statistics_consistency(self):
        """Test that statistics are internally consistent."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard/statistics",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Total games should equal games with winner + tied games
            total = data['games_with_winner'] + data['tied_games']
            self.assertEqual(total, data['total_completed_games'])
            
            # Shortest game should be <= longest game
            if data['shortest_game_turns'] and data['longest_game_turns']:
                self.assertLessEqual(
                    data['shortest_game_turns'], 
                    data['longest_game_turns']
                )


class TestLeaderboardServiceEdgeCases(TestLeaderboardServiceSetup):
    """Test edge cases and special scenarios."""
    
    def test_leaderboard_with_zero_limit(self):
        """Test leaderboard with limit of 0."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard?limit=0",
            headers=self.headers
        )
        
        # Should either return empty list or use default
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data['leaderboard'], list)
    
    def test_leaderboard_with_negative_limit(self):
        """Test leaderboard with negative limit."""
        response = session.get(
            f"{BASE_URL}/api/leaderboard?limit=-5",
            headers=self.headers
        )
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 200)
    
    def test_player_stats_special_characters(self):
        """Test getting stats for player with special characters in name."""
        # Create player with special chars
        unique_id = int(time.time() * 1000)
        username = f"player_test-123_{unique_id}"
        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "password": "pass1234"}
        )
        
        if response.status_code == 201:
            token = response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            
            response = session.get(
                f"{BASE_URL}/api/leaderboard/player/{username}",
                headers=headers
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['player'], username)


if __name__ == "__main__":
    unittest.main(verbosity=2)
