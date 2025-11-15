#!/usr/bin/env python3
"""
Battle Cards Microservices Test Suite
Tests all microservice endpoints to ensure proper functionality.
"""

import requests
import json
import time
import sys
from urllib3.packages.urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# API Gateway base URL
BASE_URL = "https://localhost:8443"

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

    def wait_for_services(self, timeout=60):
        """Wait for all services to be available."""
        self.log("Waiting for services to be available...")
        
        services = [
            "/auth/health",
            "/cards/health",
            "/game/health",
            "/leaderboard/health"
        ]
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_ready = True
            for service in services:
                try:
                    response = requests.get(f"{BASE_URL}{service}", verify=False, timeout=5)
                    if response.status_code != 200:
                        all_ready = False
                        break
                except:
                    all_ready = False
                    break
            
            if all_ready:
                self.log("All services are ready!")
                return True
            
            time.sleep(2)
        
        self.log("Timeout waiting for services", "FAIL")
        return False

    def run_all_tests(self):
        """Run the complete test suite."""
        self.log("Starting Battle Cards Microservices Test Suite")
        self.log("=" * 50)
        
        # Wait for services
        if not self.wait_for_services():
            return False
        
        # Run tests
        self.test_auth_service()
        self.test_card_service()
        self.test_game_service()
        self.test_leaderboard_service()
        
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