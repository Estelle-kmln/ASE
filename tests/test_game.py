"""Test script for the game functionality.

DEPRECATED: These tests were written for the old monolithic implementation.
The game logic has now moved to microservices architecture.
Please use test_microservices.py for comprehensive API testing instead.

The game-service microservice (microservices/game-service/) now handles all game logic.
"""

# Old imports - no longer available
# from game.game_service import GameService
# from models.card import Card, CardCollection
# from models.deck import Deck

def main():
    print("=" * 80)
    print("DEPRECATED TEST FILE")
    print("=" * 80)
    print()
    print("This test file is deprecated as the codebase has migrated to microservices.")
    print()
    print("The game logic previously tested here has been moved to:")
    print("  - microservices/game-service/app.py")
    print("  - microservices/card-service/app.py")
    print()
    print("To test the application, use:")
    print("  1. test_microservices.py - Comprehensive API integration tests")
    print("  2. Manual testing via the frontend at http://localhost:8080")
    print()
    print("To run the microservices tests:")
    print("  cd tests")
    print("  python test_microservices.py")
    print()
    print("=" * 80)
    return 0

if __name__ == "__main__":
    exit(main())
