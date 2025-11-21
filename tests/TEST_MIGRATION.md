# Test Suite Migration Summary

## Overview
All tests have been updated to work with the new microservices architecture.

## Changes Made

### 1. ✅ test_microservices.py
**Status:** UPDATED - Main integration test suite
- Changed `BASE_URL` from `https://localhost:8443` to `http://localhost:8080`
- Fixed urllib3 import to handle both old and new versions
- Tests all microservice endpoints:
  - Auth service (register, login, profile)
  - Card service (get cards, random deck, by type)
  - Game service (create game, get game state, play turns)
  - Leaderboard service (rankings, player stats, recent games)
- Includes negative test cases for error handling

**How to run:**
```powershell
cd tests
python test_microservices.py
```

### 2. ✅ test_profile.py
**Status:** UPDATED - Converted to API tests
- Replaced direct database imports with REST API calls
- Tests auth-service endpoints:
  - User registration
  - User login
  - Profile retrieval
  - Profile updates
- Uses unique usernames per test run to avoid conflicts
- Includes authentication and authorization tests

**How to run:**
```powershell
cd tests
python -m pytest test_profile.py -v
```

### 3. ⚠️ test_game.py
**Status:** DEPRECATED
- Marked as deprecated with helpful message
- Old implementation tested `game.game_service` module which no longer exists
- Game logic now in `microservices/game-service/app.py`
- Use `test_microservices.py` instead

### 4. ⚠️ test_hand.py
**Status:** DEPRECATED
- Marked as deprecated with helpful message
- Old implementation tested `game.game_logic` module which no longer exists
- Hand management logic now in `microservices/game-service/app.py`
- Use `test_microservices.py` instead

### 5. ⚠️ test_score.py
**Status:** DEPRECATED
- Marked as deprecated with helpful message
- Old implementation tested scoring logic from local modules
- Scoring logic now in `microservices/game-service/app.py`
- Use `test_microservices.py` instead

### 6. ⚠️ test_view_card_collection.py
**Status:** DEPRECATED
- Marked as deprecated with helpful message
- Card data now served by `microservices/card-service/app.py`
- Use `test_microservices.py` or direct API: `GET /api/cards`

### 7. ⚠️ test_view_old_matches.py
**Status:** DEPRECATED
- Marked as deprecated with helpful message
- Match history now served by `microservices/leaderboard-service/app.py`
- Use `test_microservices.py` or direct API: `GET /api/leaderboard/recent`

## Running Tests

### Prerequisites
Ensure all microservices are running:
```powershell
cd microservices
docker-compose up -d
```

Verify services are healthy:
```powershell
docker-compose ps
```

All services should show status: `Up (healthy)`

### Run All Active Tests
```powershell
cd tests
python -m pytest test_microservices.py test_profile.py -v
```

### Run Individual Test Suites

**Comprehensive API Integration Tests:**
```powershell
python test_microservices.py
```

**Profile/Auth Tests:**
```powershell
python -m pytest test_profile.py -v
```

## Test Coverage

### Current Coverage
- ✅ Authentication (register, login, token validation)
- ✅ User profiles (create, read, update)
- ✅ Card management (list all, by type, random deck)
- ✅ Game lifecycle (create, join, play, resolve rounds)
- ✅ Leaderboard (rankings, player stats, match history)
- ✅ Error handling and negative cases
- ✅ Authorization (token required for protected endpoints)

### What's Tested
1. **Auth Service** (`localhost:5001`)
   - User registration with validation
   - Login with JWT token generation
   - Profile retrieval and updates
   - Duplicate username handling

2. **Card Service** (`localhost:5002`)
   - Get all 39 cards
   - Filter cards by type (Rock, Paper, Scissors)
   - Generate random 22-card deck
   - Card statistics

3. **Game Service** (`localhost:5003`)
   - Create new game with player2_name
   - Join game by ID
   - Play cards in turns
   - Resolve rounds (win/lose/tie)
   - Auto-resolution when both players play
   - Game state management
   - Game over detection

4. **Leaderboard Service** (`localhost:5004`)
   - Global rankings
   - Player-specific statistics
   - Recent games list
   - Match history

## Migration Notes

### Why Deprecated?
The old test files (`test_game.py`, `test_hand.py`, `test_score.py`, etc.) were written for a monolithic architecture where game logic, card management, and database access were in local Python modules. The application has now migrated to a microservices architecture where:

- **Auth logic** → `microservices/auth-service/`
- **Card logic** → `microservices/card-service/`
- **Game logic** → `microservices/game-service/`
- **Leaderboard logic** → `microservices/leaderboard-service/`

### Benefits of New Architecture
1. **Separation of Concerns:** Each service handles one domain
2. **Independent Scaling:** Scale services based on demand
3. **Technology Flexibility:** Each service can use different tech stacks
4. **Fault Isolation:** Failure in one service doesn't crash everything
5. **Easier Testing:** API contracts are clear and testable via HTTP

### API Gateway
All services are accessed through Nginx API gateway at `http://localhost:8080`:
- `/api/auth/*` → auth-service:5001
- `/api/cards/*` → card-service:5002
- `/api/game/*` → game-service:5003
- `/api/leaderboard/*` → leaderboard-service:5004

## Troubleshooting

### Services Not Running
```powershell
cd microservices
docker-compose up -d
docker-compose ps
```

### Connection Refused
Wait 10-30 seconds for services to initialize. Check health:
```powershell
curl http://localhost:8080/api/auth/health
curl http://localhost:8080/api/cards/health
curl http://localhost:8080/api/game/health
curl http://localhost:8080/api/leaderboard/health
```

### Database Issues
Reset the database:
```powershell
docker-compose down -v
docker-compose up -d
```

### Port Conflicts
Ensure ports are free:
- 8080 (nginx)
- 5432 (postgresql)
- 5001-5004 (microservices)

## Next Steps

1. ✅ Tests updated for microservices
2. ✅ Deprecated old test files with helpful messages
3. ✅ Main integration test suite works with HTTP
4. ⏭️ Add more edge case tests as needed
5. ⏭️ Consider adding performance tests with Locust
6. ⏭️ Add end-to-end frontend tests (Selenium/Playwright)

## Documentation
- See `TESTING_GUIDE.md` for detailed testing instructions
- See `API_Documentation.md` for API specifications
- See `README.md` for deployment instructions
