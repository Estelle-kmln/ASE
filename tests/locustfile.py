"""
Locust Performance Tests for Battle Cards Microservices

This file contains performance test scenarios for all microservices:
- Auth Service (port 5001)
- Card Service (port 5002)
- Game Service (port 5003)
- Leaderboard Service (port 5004)

Run with: locust -f locustfile.py --host=https://localhost:8443
"""

import random
import string
import urllib3
from locust import HttpUser, task, between

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AuthServiceUser(HttpUser):
    """Test user for Auth Service endpoints"""
    host = "https://localhost:8443"
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
    
    def on_start(self):
        """Register and login a new user before starting tests"""
        # Use longer random string to avoid collisions in load testing
        self.username = f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        self.password = "TestPass123!"
        self.token = None
        
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "password": self.password
            },
            catch_response=True,
            name="/api/auth/register"
        ) as response:
            if response.status_code == 201:
                response.success()
                self.token = response.json().get("access_token")
            else:
                response.failure(f"Registration failed: {response.status_code}")
    
    @task(2)
    def get_profile(self):
        """Test get profile endpoint"""
        if self.token:
            self.client.get(
                "/api/auth/profile",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/auth/profile"
            )
    
    @task(2)
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
        with self.client.get("/api/auth/profile", headers={"Authorization": f"Bearer {self.token}"} if self.token else {}, catch_response=True, name="/health [auth]") as response:
            if response.status_code in [200, 401]:
                response.success()


class CardServiceUser(HttpUser):
    """Test user for Card Service endpoints"""
    host = "https://localhost:8443"
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
    
    def on_start(self):
        """Get authentication token"""
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        """Get a valid auth token"""
        # Create unique username to avoid conflicts
        username = f"carduser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        password = "TestPass123!"
        
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={"username": username, "password": password},
            catch_response=True,
            name="/api/auth/register [for card service]"
        ) as response:
            if response.status_code == 201:
                response.success()
                return response.json().get("access_token")
            else:
                response.failure(f"Registration failed: {response.status_code}")
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
        with self.client.get("/api/cards", headers={"Authorization": f"Bearer {self.token}"} if self.token else {}, catch_response=True, name="/health [card]") as response:
            if response.status_code in [200, 401]:
                response.success()


class GameServiceUser(HttpUser):
    """Test user for Game Service endpoints"""
    host = "https://localhost:8443"
    wait_time = between(2, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
    
    def on_start(self):
        """Get authentication token and create an active game with deck selection"""
        self.token = self.get_auth_token()
        self.game_id = None
        self.player2_name = f"opponent_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        
        # Create a game only if we have a valid token
        if not self.token:
            return
        
        # IMPORTANT: Register player2 BEFORE creating the game
        player2_token = self.get_auth_token_for_player2()
        if not player2_token:
            return  # Can't create game without player2
        
        with self.client.post(
            "/api/games",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"player2_name": self.player2_name},
            catch_response=True,
            name="/api/games [create]"
        ) as response:
            if response.status_code == 201:
                response.success()
                self.game_id = response.json().get("game_id")
            else:
                response.failure(f"Game creation failed: {response.status_code}")
                return
        
        # Only continue if game was created
        if self.game_id:
            response = self.client.post(
                f"/api/games/{self.game_id}/accept",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/accept [setup]"
            )
            if response.status_code != 200:
                self.game_id = None
                return
            
            # Select deck for player 1 (transitions to active when both select)
            deck = [
                {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"},
                {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"},
                {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"},
                {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"},
                {"type": "Scissors"}, {"type": "Scissors"}, {"type": "Scissors"}, {"type": "Scissors"},
                {"type": "Scissors"}, {"type": "Scissors"}
            ]
            
            # Player 1 selects deck
            self.client.post(
                f"/api/games/{self.game_id}/select-deck",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"deck": deck},
                name="/api/games/[id]/select-deck [setup p1]"
            )
            
            # Player 2 selects deck (already registered earlier)
            response = self.client.post(
                f"/api/games/{self.game_id}/select-deck",
                headers={"Authorization": f"Bearer {player2_token}"},
                json={"deck": deck},
                name="/api/games/[id]/select-deck [setup p2]"
            )
            # Verify game is now active
            if response.status_code == 200:
                state_response = self.client.get(
                    f"/api/games/{self.game_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    name="/api/games/[id] [verify active]"
                )
                if state_response.status_code == 200:
                    game_state = state_response.json().get("status")
                    if game_state != "active":
                        self.game_id = None  # Mark game as invalid
            else:
                self.game_id = None
    
    def get_auth_token_for_player2(self):
        """Get auth token for player 2 (the opponent)"""
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={"username": self.player2_name, "password": "TestPass123!"},
            catch_response=True,
            name="/api/auth/register [for player2]"
        ) as response:
            if response.status_code == 201:
                response.success()
                return response.json().get("access_token")
            else:
                response.failure(f"Player2 registration failed: {response.status_code}")
                return None
    
    def get_auth_token(self):
        """Get a valid auth token"""
        # Use longer random string to avoid collisions in load testing
        username = f"player_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        password = "TestPass123!"
        
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={"username": username, "password": password},
            catch_response=True,
            name="/api/auth/register [for game service]"
        ) as response:
            if response.status_code == 201:
                response.success()
                return response.json().get("access_token")
            else:
                # If registration fails for any reason, mark as failure
                response.failure(f"Registration failed: {response.status_code}")
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
            with self.client.post(
                f"/api/games/{self.game_id}/play-card",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"card_index": card_index},
                catch_response=True,
                name="/api/games/[id]/play-card"
            ) as response:
                if response.status_code in [200, 400]:
                    response.success()  # 400 is expected if card can't be played
    
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
        if self.token and self.game_id:
            with self.client.get(f"/api/games/{self.game_id}", headers={"Authorization": f"Bearer {self.token}"}, catch_response=True, name="/health [game]") as response:
                if response.status_code in [200, 404]:
                    response.success()


class LeaderboardServiceUser(HttpUser):
    """Test user for Leaderboard Service endpoints"""
    host = "https://localhost:8443"
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
    
    def on_start(self):
        """Get authentication token"""
        self.token = self.get_auth_token()
    
    def get_auth_token(self):
        """Get a valid auth token"""
        username = f"lbuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        password = "TestPass123!"
        
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={"username": username, "password": password},
            catch_response=True,
            name="/api/auth/register [for leaderboard service]"
        ) as response:
            if response.status_code == 201:
                response.success()
                return response.json().get("access_token")
            else:
                response.failure(f"Registration failed: {response.status_code}")
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
        with self.client.get("/api/leaderboard", headers={"Authorization": f"Bearer {self.token}"} if self.token else {}, catch_response=True, name="/health [leaderboard]") as response:
            if response.status_code in [200, 401]:
                response.success()


class CombinedUser(HttpUser):
    """Combined user that tests all services in a realistic workflow"""
    host = "https://localhost:8443"
    wait_time = between(2, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
    
    def on_start(self):
        """Set up user for complete game flow"""
        # Register new user
        self.username = f"user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        self.password = "TestPass123!"
        self.token = None
        self.game_id = None
        
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={"username": self.username, "password": self.password},
            catch_response=True,
            name="/api/auth/register [combined]"
        ) as response:
            if response.status_code == 201:
                response.success()
                self.token = response.json().get("access_token")
            else:
                response.failure(f"Registration failed: {response.status_code}")
    
    @task(10)
    def complete_game_workflow(self):
        """Simulate a complete game workflow"""
        if not self.token:
            return
        
        # 1. Get cards
        self.client.get(
            "/api/cards",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/cards [combined]"
        )
        
        # 2. Create random deck
        deck_response = self.client.post(
            "/api/cards/random-deck",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"size": 22},
            name="/api/cards/random-deck [combined]"
        )
        
        # 3. Register player2 BEFORE creating game (required by game service)
        player2 = f"opponent_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
        player2_token = self._get_player2_token(player2)
        if not player2_token:
            return  # Can't create game without player2
        
        # 4. Create game (now that player2 exists)
        with self.client.post(
            "/api/games",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"player2_name": player2},
            catch_response=True,
            name="/api/games [create combined]"
        ) as game_response:
            if game_response.status_code == 201:
                game_response.success()
            else:
                game_response.failure(f"Cannot create game: {game_response.status_code}")
                return
        
        if game_response.status_code == 201:
            game_id = game_response.json().get("game_id")
            
            # 3a. Accept invitation (transitions to deck_selection)
            self.client.post(
                f"/api/games/{game_id}/accept",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/accept [combined]"
            )
            
            # 3b. Select deck for player 1
            deck = [
                {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"},
                {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"}, {"type": "Rock"},
                {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"},
                {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"}, {"type": "Paper"},
                {"type": "Scissors"}, {"type": "Scissors"}, {"type": "Scissors"}, {"type": "Scissors"},
                {"type": "Scissors"}, {"type": "Scissors"}
            ]
            self.client.post(
                f"/api/games/{game_id}/select-deck",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"deck": deck},
                name="/api/games/[id]/select-deck [combined p1]"
            )
            
            # 5c. Player 2 selects deck (already registered earlier)
            p2_deck_response = self.client.post(
                f"/api/games/{game_id}/select-deck",
                headers={"Authorization": f"Bearer {player2_token}"},
                json={"deck": deck},
                name="/api/games/[id]/select-deck [combined p2]"
            )
            
            if p2_deck_response.status_code != 200:
                return  # Deck selection failed, can't continue
            
            # 6. Get game state and verify it's active
            state_response = self.client.get(
                f"/api/games/{game_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id] [combined]"
            )
            
            if state_response.status_code != 200:
                return
            
            game_state = state_response.json().get("status")
            if game_state != "active":
                return  # Game not active, can't draw hand
            
            # 7. Draw hand (only if game is active)
            self.client.post(
                f"/api/games/{game_id}/draw-hand",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/draw-hand [combined]"
            )
            
            # 8. Get hand
            self.client.get(
                f"/api/games/{game_id}/hand",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/games/[id]/hand [combined]"
            )
            
            # 9. Play card
            with self.client.post(
                f"/api/games/{game_id}/play-card",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"card_index": random.randint(0, 2)},
                catch_response=True,
                name="/api/games/[id]/play-card [combined]"
            ) as response:
                if response.status_code in [200, 400]:
                    response.success()
    
    @task(5)
    def view_leaderboard(self):
        """View leaderboard and statistics"""
        if not self.token:
            return
        
        # Get leaderboard
        self.client.get(
            "/api/leaderboard",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/leaderboard [combined]"
        )
        
        # Get statistics
        self.client.get(
            "/api/leaderboard/statistics",
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
    
    def _get_player2_token(self, player2_name):
        """Get auth token for player 2"""
        # Always register new users to avoid concurrent session conflicts
        with self.client.post(
            "/api/auth/register",
            json={"username": player2_name, "password": "TestPass123!"},
            catch_response=True,
            name="/api/auth/register [player2 combined]"
        ) as response:
            if response.status_code == 201:
                response.success()
                return response.json().get("access_token")
            else:
                response.failure(f"Player2 registration failed: {response.status_code}")
                return None

