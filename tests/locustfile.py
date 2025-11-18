"""
Locust Performance Tests for Battle Cards Microservices

This file contains performance test scenarios for all microservices:
- Auth Service (port 5001)
- Card Service (port 5002)
- Game Service (port 5003)
- Leaderboard Service (port 5004)

Run with: locust -f locustfile.py --host=http://localhost
"""

import random
import string
from locust import HttpUser, task, between


class AuthServiceUser(HttpUser):
    """Test user for Auth Service endpoints"""
    host = "http://localhost:5001"
    wait_time = between(1, 3)
    
    def on_start(self):
        """Register and login a new user before starting tests"""
        self.username = f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        self.password = "testpass123"
        self.token = None
        
        # Register
        response = self.client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "password": self.password
            },
            name="/api/auth/register"
        )
        
        if response.status_code == 201:
            self.token = response.json().get("access_token")
        else:
            # If registration fails, try to login
            response = self.client.post(
                "/api/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                },
                name="/api/auth/login"
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
    
    @task(3)
    def login(self):
        """Test login endpoint"""
        self.client.post(
            "/api/auth/login",
            json={
                "username": self.username,
                "password": self.password
            },
            name="/api/auth/login"
        )
    
    @task(2)
    def get_profile(self):
        """Test get profile endpoint"""
        if self.token:
            self.client.get(
                "/api/auth/profile",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/auth/profile"
            )
    
    @task(1)
    def validate_token(self):
        """Test token validation"""
        if self.token:
            self.client.post(
                "/api/auth/validate",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/auth/validate"
            )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health", name="/health [auth]")


class CardServiceUser(HttpUser):
    """Test user for Card Service endpoints"""
    host = "http://localhost:5002"
    wait_time = between(1, 3)
    
    def on_start(self):
        """Get authentication token"""
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        """Get a valid auth token"""
        # Try to login with a test user
        username = "testuser_perf"
        password = "testpass123"
        
        # First try to register
        response = self.client.post(
            "http://localhost:5001/api/auth/register",
            json={"username": username, "password": password},
            name="/api/auth/register [for card service]"
        )
        
        if response.status_code == 201:
            return response.json().get("access_token")
        
        # If registration fails, try login
        response = self.client.post(
            "http://localhost:5001/api/auth/login",
            json={"username": username, "password": password},
            name="/api/auth/login [for card service]"
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        
        return None
    
    @task(5)
    def get_all_cards(self):
        """Test get all cards endpoint"""
        if self.token:
            self.client.get(
                "/api/cards",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/cards"
            )
    
    @task(3)
    def get_cards_by_type(self):
        """Test get cards by type"""
        if self.token:
            card_type = random.choice(["rock", "paper", "scissors"])
            self.client.get(
                f"/api/cards/by-type/{card_type}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/cards/by-type/[type]"
            )
    
    @task(2)
    def get_card_by_id(self):
        """Test get specific card by ID"""
        if self.token:
            card_id = random.randint(1, 39)  # Assuming 39 cards
            self.client.get(
                f"/api/cards/{card_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/cards/[id]"
            )
    
    @task(4)
    def create_random_deck(self):
        """Test create random deck"""
        if self.token:
            self.client.post(
                "/api/cards/random-deck",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"size": 22},
                name="/api/cards/random-deck"
            )
    
    @task(2)
    def get_card_statistics(self):
        """Test get card statistics"""
        if self.token:
            self.client.get(
                "/api/cards/statistics",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/cards/statistics"
            )
    
    @task(1)
    def get_card_types(self):
        """Test get card types"""
        if self.token:
            self.client.get(
                "/api/cards/types",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/cards/types"
            )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health", name="/health [card]")


class GameServiceUser(HttpUser):
    """Test user for Game Service endpoints"""
    host = "http://localhost:5003"
    wait_time = between(2, 5)
    
    def on_start(self):
        """Get authentication token and create a game"""
        self.token = self.get_auth_token()
        self.game_id = None
        self.player2_name = f"opponent_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        
        # Create a game
        if self.token:
            response = self.client.post(
                "/api/games",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"player2_name": self.player2_name},
                name="/api/games [create]"
            )
            if response.status_code == 201:
                self.game_id = response.json().get("game_id")
    
    def get_auth_token(self):
        """Get a valid auth token"""
        username = f"player_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        password = "testpass123"
        
        # Register
        response = self.client.post(
            "http://localhost:5001/api/auth/register",
            json={"username": username, "password": password},
            name="/api/auth/register [for game service]"
        )
        
        if response.status_code == 201:
            return response.json().get("access_token")
        
        # Try login
        response = self.client.post(
            "http://localhost:5001/api/auth/login",
            json={"username": username, "password": password},
            name="/api/auth/login [for game service]"
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        
        return None
    
    @task(3)
    def get_game_state(self):
        """Test get game state"""
        if self.token and self.game_id:
            self.client.get(
                f"/api/games/{self.game_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]"
            )
    
    @task(2)
    def get_player_hand(self):
        """Test get player hand"""
        if self.token and self.game_id:
            self.client.get(
                f"/api/games/{self.game_id}/hand",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/hand"
            )
    
    @task(2)
    def draw_hand(self):
        """Test draw hand"""
        if self.token and self.game_id:
            self.client.post(
                f"/api/games/{self.game_id}/draw-hand",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/draw-hand"
            )
    
    @task(2)
    def play_card(self):
        """Test play card"""
        if self.token and self.game_id:
            card_index = random.randint(0, 2)  # Assuming 3 cards in hand
            self.client.post(
                f"/api/games/{self.game_id}/play-card",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"card_index": card_index},
                name="/api/games/[id]/play-card"
            )
    
    @task(1)
    def get_turn_info(self):
        """Test get turn info"""
        if self.token and self.game_id:
            self.client.get(
                f"/api/games/{self.game_id}/turn-info",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/turn-info"
            )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health", name="/health [game]")


class LeaderboardServiceUser(HttpUser):
    """Test user for Leaderboard Service endpoints"""
    host = "http://localhost:5004"
    wait_time = between(1, 3)
    
    def on_start(self):
        """Get authentication token"""
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        """Get a valid auth token"""
        username = "testuser_leaderboard"
        password = "testpass123"
        
        # Register
        response = self.client.post(
            "http://localhost:5001/api/auth/register",
            json={"username": username, "password": password},
            name="/api/auth/register [for leaderboard service]"
        )
        
        if response.status_code == 201:
            return response.json().get("access_token")
        
        # Try login
        response = self.client.post(
            "http://localhost:5001/api/auth/login",
            json={"username": username, "password": password},
            name="/api/auth/login [for leaderboard service]"
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        
        return None
    
    @task(5)
    def get_leaderboard(self):
        """Test get leaderboard"""
        if self.token:
            limit = random.choice([10, 20, 50])
            self.client.get(
                f"/api/leaderboard?limit={limit}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/leaderboard"
            )
    
    @task(3)
    def get_player_stats(self):
        """Test get player statistics"""
        if self.token:
            player_name = f"player_{random.randint(1, 10)}"
            self.client.get(
                f"/api/leaderboard/player/{player_name}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/leaderboard/player/[name]"
            )
    
    @task(3)
    def get_recent_games(self):
        """Test get recent games"""
        if self.token:
            limit = random.choice([10, 20, 30])
            self.client.get(
                f"/api/leaderboard/recent-games?limit={limit}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/leaderboard/recent-games"
            )
    
    @task(2)
    def get_top_players(self):
        """Test get top players"""
        if self.token:
            self.client.get(
                "/api/leaderboard/top-players",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/leaderboard/top-players"
            )
    
    @task(2)
    def get_statistics(self):
        """Test get global statistics"""
        if self.token:
            self.client.get(
                "/api/leaderboard/statistics",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/leaderboard/statistics"
            )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get("/health", name="/health [leaderboard]")


class CombinedUser(HttpUser):
    """Combined user that tests all services in a realistic workflow"""
    host = "http://localhost:5001"
    wait_time = between(2, 5)
    
    def on_start(self):
        """Set up user for complete game flow"""
        # Register and login
        self.username = f"user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        self.password = "testpass123"
        self.token = None
        self.game_id = None
        
        # Register
        response = self.client.post(
            "/api/auth/register",
            json={"username": self.username, "password": self.password},
            name="/api/auth/register [combined]"
        )
        
        if response.status_code == 201:
            self.token = response.json().get("access_token")
        else:
            # Try login
            response = self.client.post(
                "/api/auth/login",
                json={"username": self.username, "password": self.password},
                name="/api/auth/login [combined]"
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
    
    @task(10)
    def complete_game_workflow(self):
        """Simulate a complete game workflow"""
        if not self.token:
            return
        
        # 1. Get cards
        self.client.get(
            "http://localhost:5002/api/cards",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/cards [combined]"
        )
        
        # 2. Create random deck
        deck_response = self.client.post(
            "http://localhost:5002/api/cards/random-deck",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"size": 22},
            name="/api/cards/random-deck [combined]"
        )
        
        # 3. Create game
        player2 = f"opponent_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        game_response = self.client.post(
            "http://localhost:5003/api/games",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"player2_name": player2},
            name="/api/games [create combined]"
        )
        
        if game_response.status_code == 201:
            game_id = game_response.json().get("game_id")
            
            # 4. Get game state
            self.client.get(
                f"http://localhost:5003/api/games/{game_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id] [combined]"
            )
            
            # 5. Draw hand
            self.client.post(
                f"http://localhost:5003/api/games/{game_id}/draw-hand",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/draw-hand [combined]"
            )
            
            # 6. Get hand
            self.client.get(
                f"http://localhost:5003/api/games/{game_id}/hand",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/hand [combined]"
            )
            
            # 7. Play card
            self.client.post(
                f"http://localhost:5003/api/games/{game_id}/play-card",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"card_index": random.randint(0, 2)},
                name="/api/games/[id]/play-card [combined]"
            )
    
    @task(5)
    def view_leaderboard(self):
        """View leaderboard and statistics"""
        if not self.token:
            return
        
        # Get leaderboard
        self.client.get(
            "http://localhost:5004/api/leaderboard",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/leaderboard [combined]"
        )
        
        # Get statistics
        self.client.get(
            "http://localhost:5004/api/leaderboard/statistics",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/leaderboard/statistics [combined]"
        )
    
    @task(3)
    def get_profile(self):
        """Get user profile"""
        if self.token:
            self.client.get(
                "/api/auth/profile",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/auth/profile [combined]"
            )

