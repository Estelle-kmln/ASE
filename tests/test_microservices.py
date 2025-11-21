#!/usr/bin/env python3
"""
Battle Cards Microservices Test Suite
Tests all microservice endpoints to ensure proper functionality.
"""

import requests
import json
import time
import sys

# Try to disable SSL warnings for self-signed certificates
try:
    import urllib3
    urllib3.disable_warnings()
except:
    pass

# API Gateway base URL
BASE_URL = "http://localhost:8080"

# Test user data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # Allow self-signed certificates
        self.token = None
        self.passed = 0
        self.failed = 0

    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")

    def test_request(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Make a test request and validate the response."""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code == expected_status:
                self.log(f"✓ {method} {endpoint} - Status: {response.status_code}", "PASS")
                self.passed += 1
                return response.json() if response.content else None
            else:
                self.log(f"✗ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}", "FAIL")
                self.log(f"  Response: {response.text}", "FAIL")
                self.failed += 1
                return None

        except Exception as e:
            self.log(f"✗ {method} {endpoint} - Exception: {str(e)}", "FAIL")
            self.failed += 1
            return None

    def get_auth_headers(self):
        """Get headers with JWT token."""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def test_auth_service(self):
        """Test authentication service endpoints."""
        self.log("Testing Authentication Service", "TEST")
        
        # Test health check
        self.test_request("GET", "/auth/health")
        
        # Test user registration
        response = self.test_request("POST", "/auth/register", TEST_USER, expected_status=201)
        if response:
            self.log("User registered successfully")
        
        # Test user login
        login_data = {"username": TEST_USER["username"], "password": TEST_USER["password"]}
        response = self.test_request("POST", "/auth/login", login_data)
        if response and "access_token" in response:
            self.token = response["access_token"]
            self.log("Login successful, token obtained")
        
        # Test profile retrieval
        self.test_request("GET", "/auth/profile", headers=self.get_auth_headers())
        
        # Test profile update
        update_data = {"email": "updated@example.com"}
        self.test_request("PUT", "/auth/profile", update_data, headers=self.get_auth_headers())

    def test_card_service(self):
        """Test card service endpoints."""
        self.log("Testing Card Service", "TEST")
        
        # Test health check
        self.test_request("GET", "/cards/health")
        
        # Test get all cards
        self.test_request("GET", "/cards", headers=self.get_auth_headers())
        
        # Test get cards by type
        self.test_request("GET", "/cards/type/creature", headers=self.get_auth_headers())
        
        # Test card statistics
        self.test_request("GET", "/cards/stats", headers=self.get_auth_headers())
        
        # Test random deck generation
        self.test_request("GET", "/cards/deck/random", headers=self.get_auth_headers())

    def test_game_service(self):
        """Test game service endpoints."""
        self.log("Testing Game Service", "TEST")
        
        # Test health check
        self.test_request("GET", "/game/health")
        
        # Test create game
        game_data = {"player_name": TEST_USER["username"]}
        response = self.test_request("POST", "/game", game_data, headers=self.get_auth_headers(), expected_status=201)
        
        game_id = None
        if response and "game_id" in response:
            game_id = response["game_id"]
            self.log(f"Game created with ID: {game_id}")
            
            # Test get game state
            self.test_request("GET", f"/game/{game_id}", headers=self.get_auth_headers())
            
            # Test play a card (assuming we have cards in hand)
            play_data = {"card_index": 0}
            self.test_request("POST", f"/game/{game_id}/play", play_data, headers=self.get_auth_headers())
            
            # Test end turn
            self.test_request("POST", f"/game/{game_id}/end-turn", headers=self.get_auth_headers())

    def test_leaderboard_service(self):
        """Test leaderboard service endpoints."""
        self.log("Testing Leaderboard Service", "TEST")
        
        # Test health check
        self.test_request("GET", "/leaderboard/health")
        
        # Test global leaderboard
        self.test_request("GET", "/leaderboard", headers=self.get_auth_headers())
        
        # Test player stats
        self.test_request("GET", f"/leaderboard/player/{TEST_USER['username']}", headers=self.get_auth_headers())
        
        # Test recent games
        self.test_request("GET", "/leaderboard/recent", headers=self.get_auth_headers())

    def test_auth_negative_cases(self):
        """Test authentication service negative cases."""
        self.log("Testing Authentication Service Negative Cases", "TEST")
        
        # Test login with invalid credentials
        invalid_login = {"username": "nonexistent", "password": "wrongpassword"}
        self.test_request("POST", "/auth/login", invalid_login, expected_status=401)
        
        # Test login with missing password
        incomplete_login = {"username": TEST_USER["username"]}
        self.test_request("POST", "/auth/login", incomplete_login, expected_status=400)
        
        # Test registration with duplicate username
        duplicate_user = {
            "username": TEST_USER["username"],
            "email": "duplicate@example.com",
            "password": "password123"
        }
        self.test_request("POST", "/auth/register", duplicate_user, expected_status=400)
        
        # Test profile access without token
        self.test_request("GET", "/auth/profile", expected_status=401)
        
        # Test profile access with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        self.test_request("GET", "/auth/profile", headers=invalid_headers, expected_status=401)
        
        # Test profile update without token
        update_data = {"email": "new@example.com"}
        self.test_request("PUT", "/auth/profile", update_data, expected_status=401)

    def test_card_service_negative_cases(self):
        """Test card service negative cases."""
        self.log("Testing Card Service Negative Cases", "TEST")
        
        # Test accessing cards without authentication (if required)
        # Note: Some endpoints might allow unauthenticated access, adjust expected_status accordingly
        # Test invalid card type
        self.test_request("GET", "/cards/type/invalid_type", headers=self.get_auth_headers(), expected_status=404)
        
        # Test accessing cards with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        self.test_request("GET", "/cards", headers=invalid_headers, expected_status=401)

    def test_game_service_negative_cases(self):
        """Test game service negative cases."""
        self.log("Testing Game Service Negative Cases", "TEST")
        
        # Test creating game without authentication
        game_data = {"player2_name": "Opponent"}
        self.test_request("POST", "/game", game_data, expected_status=401)
        
        # Test creating game with missing player2_name
        incomplete_game = {}
        self.test_request("POST", "/game", incomplete_game, headers=self.get_auth_headers(), expected_status=400)
        
        # Test getting game with invalid game ID
        fake_game_id = "00000000-0000-0000-0000-000000000000"
        self.test_request("GET", f"/game/{fake_game_id}", headers=self.get_auth_headers(), expected_status=404)
        
        # Test playing card with invalid game ID
        play_data = {"card_index": 0}
        self.test_request("POST", f"/game/{fake_game_id}/play", play_data, headers=self.get_auth_headers(), expected_status=404)
        
        # Test playing card without authentication
        if self.token:
            # Create a real game first
            game_data = {"player2_name": "Opponent"}
            response = self.test_request("POST", "/game", game_data, headers=self.get_auth_headers(), expected_status=201)
            if response and "game_id" in response:
                game_id = response["game_id"]
                # Test playing with invalid card index (negative)
                invalid_play = {"card_index": -1}
                self.test_request("POST", f"/game/{game_id}/play", invalid_play, headers=self.get_auth_headers(), expected_status=400)
                
                # Test playing with invalid card index (too large)
                invalid_play2 = {"card_index": 10}
                self.test_request("POST", f"/game/{game_id}/play", invalid_play2, headers=self.get_auth_headers(), expected_status=400)
                
                # Test playing without card_index
                incomplete_play = {}
                self.test_request("POST", f"/game/{game_id}/play", incomplete_play, headers=self.get_auth_headers(), expected_status=400)
        
        # Test end turn without authentication
        if self.token:
            game_data = {"player2_name": "Opponent"}
            response = self.test_request("POST", "/game", game_data, headers=self.get_auth_headers(), expected_status=201)
            if response and "game_id" in response:
                game_id = response["game_id"]
                self.test_request("POST", f"/game/{game_id}/end-turn", expected_status=401)

    def test_leaderboard_negative_cases(self):
        """Test leaderboard service negative cases."""
        self.log("Testing Leaderboard Service Negative Cases", "TEST")
        
        # Test accessing leaderboard without authentication (if required)
        # Test player stats for non-existent player
        self.test_request("GET", "/leaderboard/player/nonexistent_player_12345", headers=self.get_auth_headers(), expected_status=404)
        
        # Test accessing leaderboard with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        self.test_request("GET", "/leaderboard", headers=invalid_headers, expected_status=401)

    def test_nonexistent_endpoints(self):
        """Test accessing non-existent endpoints."""
        self.log("Testing Non-existent Endpoints", "TEST")
        
        # Test various non-existent endpoints
        self.test_request("GET", "/nonexistent", expected_status=404)
        self.test_request("GET", "/auth/invalid", expected_status=404)
        self.test_request("GET", "/cards/invalid/endpoint", expected_status=404)
        self.test_request("GET", "/game/invalid/endpoint", expected_status=404)
        self.test_request("POST", "/invalid/service", expected_status=404)

    def wait_for_services(self, timeout=60):
        """Wait for all services to be available."""
        self.log("Waiting for services to be available...")
        
        services = [
            ("/auth/health", "Auth Service"),
            ("/cards/health", "Card Service"),
            ("/game/health", "Game Service"),
            ("/leaderboard/health", "Leaderboard Service")
        ]
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_ready = True
            failed_services = []
            
            for endpoint, name in services:
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", verify=False, timeout=5)
                    if response.status_code != 200:
                        all_ready = False
                        failed_services.append(f"{name} (HTTP {response.status_code})")
                except Exception as e:
                    all_ready = False
                    failed_services.append(f"{name} ({type(e).__name__})")
            
            if all_ready:
                self.log("All services are ready!")
                return True
            
            time.sleep(2)
        
        self.log("Timeout waiting for services", "FAIL")
        if failed_services:
            self.log(f"Failed services: {', '.join(failed_services)}", "FAIL")
        self.log(f"\nTroubleshooting:", "INFO")
        self.log(f"  1. Check Docker: cd microservices && docker-compose ps", "INFO")
        self.log(f"  2. Test directly: curl {BASE_URL}/api/auth/health", "INFO")
        self.log(f"  3. Check logs: docker-compose logs api-gateway", "INFO")
        self.log(f"  4. Restart: docker-compose restart", "INFO")
        return False

    def run_all_tests(self):
        """Run the complete test suite."""
        self.log("Starting Battle Cards Microservices Test Suite")
        self.log("=" * 50)
        
        # Wait for services
        if not self.wait_for_services():
            return False
        
        # Run positive tests
        self.test_auth_service()
        self.test_card_service()
        self.test_game_service()
        self.test_leaderboard_service()
        
        # Run negative tests
        self.test_auth_negative_cases()
        self.test_card_service_negative_cases()
        self.test_game_service_negative_cases()
        self.test_leaderboard_negative_cases()
        self.test_nonexistent_endpoints()
        
        # Print summary
        self.log("=" * 50)
        self.log(f"Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.failed == 0:
            self.log("All tests passed! ✓", "PASS")
            return True
        else:
            self.log("Some tests failed! ✗", "FAIL")
            return False

def main():
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()