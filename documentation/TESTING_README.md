# Testing Documentation

This document describes Python unit tests (pytest/unittest), Locust performance tests, and Postman API tests for the Battle Cards game microservices.

## Quick Start

**Before running any tests, ensure Docker Desktop is running and microservices are built and started:**

1. **Start Docker Desktop** (if not already running)
2. **Build and start all microservices:**

**Recommended: Use the automated build script** (handles GAME_HISTORY_KEY automatically):

```bash
cd microservices
./build-and-start.sh
```

**Alternative: Manual build** (requires setting GAME_HISTORY_KEY manually):

```bash
cd microservices
docker-compose up -d --build
```

**Note**: The build script automatically generates and saves a `GAME_HISTORY_KEY` to `.env` if one doesn't exist. This key is required for game history encryption and is gitignored for security.

## Running Tests Locally to Match GitHub Actions

⚠️ **CRITICAL**: Always start with fresh containers when running tests!

To replicate the same clean-slate testing environment that GitHub Actions uses (fresh database, no pre-existing test data):

### Option 1: Fresh Database Reset (Recommended - Use This Every Time)

```bash
# 1. Stop all services and remove volumes (clears database)
cd microservices
docker-compose down -v

# 2. Rebuild and start services (fresh database with init scripts only)
docker-compose up -d --build

# 3. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 4. Run your tests
cd ..
pytest tests/                                    # Python unit tests
newman run tests/microservices_postman_collection.json  # Postman tests
locust -f tests/locustfile.py                   # Locust performance tests
```

**Key Points:**
- The `-v` flag in `docker-compose down -v` removes all volumes, including the PostgreSQL database
- This ensures a completely fresh database with only the SQL initialization scripts (`01-init-cards.sql`, `02-game-history.sql`, etc.)
- Tests must properly set up all required data (register users, create games, select decks) before testing gameplay
- This matches GitHub Actions behavior where the database is fresh on every run

### Option 2: Manual Database Cleanup

If you prefer to keep services running and only reset the database:

```bash
# Connect to PostgreSQL container
docker exec -it microservices-postgresql-1 psql -U battlecards_user -d battlecards_db

# Drop and recreate the database
DROP DATABASE battlecards_db;
CREATE DATABASE battlecards_db;
\q

# Restart services to re-run init scripts
docker-compose restart

# Wait for services to be healthy
docker-compose ps
```

### Why This Matters

**GitHub Actions Environment:**
- Fresh database on every test run
- No pre-existing users, games, or test data
- All tests must create their own setup data

**Local Development:**
- Database persists between runs
- Old test data accumulates
- Tests may pass locally due to existing data but fail in CI

**Example Issue:**
```python
# This test passes locally (user already exists from previous run)
# but fails in GitHub Actions (fresh database)
def test_game_play():
    game_id = "some-game-id"  # From previous test run
    response = client.post(f"/api/games/{game_id}/draw-hand")
    # ❌ Fails in CI: game doesn't exist
```

**Proper Test Setup:**
```python
def test_game_play():
    # Create complete game setup
    token = register_and_login_user("player1")
    game_id = create_game(token, "player2")
    accept_invitation(game_id, token)
    select_deck_player1(game_id, token)
    select_deck_player2(game_id, player2_token)
    # ✓ Now the game is active and ready for testing
    response = client.post(f"/api/games/{game_id}/draw-hand")
```

Wait for all services to be healthy (this may take 1-2 minutes). You can check service status with:

```bash
docker-compose ps
```

**Then run tests:**

**1. Run All Locust Performance Tests:**

```bash
# From project root directory (not microservices folder)
locust -f tests/locustfile.py --host=https://localhost:8443
```

Then open `http://localhost:8089` in your browser to configure and run tests.

**Note**: Locust automatically handles HTTPS connections. The tests will work with self-signed certificates.

**2. Run All Postman API Tests:**

```bash
# Run all Postman tests with HTTPS (use --insecure for self-signed certificates)
newman run tests/microservices_postman_collection.json \
  --env-var "BASE_URL=https://localhost:8443" \
  --insecure

# With HTML report
newman run tests/microservices_postman_collection.json \
  --env-var "BASE_URL=https://localhost:8443" \
  --insecure \
  --reporters html --reporter-html-export report.html
```

---

## Python Unit Tests (Unittest/Pytest)

### Overview

The project includes comprehensive Python unit tests covering all core game functionality. All tests can be run using a single master test runner script that executes both custom test functions and unittest-based tests.

### Test Files Available

- `test_auth_service.py` - Authentication, registration, profile, token refresh, sessions (45+ tests)
- `test_account_lockout.py` - Account lockout after failed login attempts
- `test_token_refresh.py` - Automatic token refresh functionality
- `test_concurrent_sessions.py` - Concurrent session management (strict mode)
- `test_game_service.py` - Game logic, invitations, deck selection
- `test_card_service.py` - Card database and deck generation
- `test_leaderboard_service.py` - Rankings and statistics
- `test_deck_selection.py` - Deck selection feature (manual and random)
- `test_complete_game_flow.py` - End-to-end game workflow
- `test_security.py` - Security features and input validation
- `test_password_requirements.py` - Password strength validation
- `comprehensive_logging_test.py` - User action logging
- `locustfile.py` - Performance testing with load simulation

### Prerequisites

1. **Python Virtual Environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   Note: `psycopg2-binary` requires PostgreSQL development libraries. On macOS with Homebrew:

   ```bash
   brew install postgresql@15
   ```

3. **Docker (for database-dependent tests)**:
   - Start Docker Desktop (if not already running)
   - Build and start PostgreSQL: `cd microservices && docker-compose up -d --build postgresql`
   - Database available at `localhost:5432`

## Locust Performance Tests

### Overview

Locust performance tests are designed to test the microservices architecture under load. The test suite includes dedicated user classes for each microservice and a combined user class that simulates realistic game workflows.

### Prerequisites

1. **Start Docker Desktop**:
   - Ensure Docker Desktop is running on your machine
   - You can verify Docker is running with: `docker ps`

2. **Install Locust**:

   ```bash
   pip install locust
   ```

3. **Build and Start Microservices**:

   **Important**: Always use `--build` flag when starting services to ensure code changes are included:

   ```bash
   cd microservices
   docker-compose up -d --build
   ```

   This will:
   - Rebuild Docker images with your latest code changes
   - Start all microservices containers
   - Wait for services to become healthy

   Wait for all services to be ready (check with `docker-compose ps`). Services should be available at:
   - Auth Service: `http://localhost:5001`
   - Card Service: `http://localhost:5002`
   - Game Service: `http://localhost:5003`
   - Leaderboard Service: `http://localhost:5004`

### Running Locust Tests

#### Quick Start (Web UI)

You can run Locust from either the project root or the tests directory:

**Option 1: From project root (recommended)**

```bash
# From project root directory (not microservices folder)
locust -f tests/locustfile.py
```

**Option 2: From tests directory**

```bash
# Navigate to tests directory
cd tests

# Start Locust web UI
locust -f locustfile.py
```

Then open your browser to `http://localhost:8089` to configure and run tests through the web interface.

#### Quick Start Script

```bash
# Use the quick start script (checks services and starts Locust)
./tests/quick-start-locust.sh
```

#### Advanced: Run Specific User Classes

```bash
# Test only Auth Service
locust -f tests/locustfile.py --host=http://localhost:5001 AuthServiceUser

# Test only Card Service
locust -f tests/locustfile.py --host=http://localhost:5002 CardServiceUser

# Test only Game Service
locust -f tests/locustfile.py --host=http://localhost:5003 GameServiceUser

# Test only Leaderboard Service
locust -f tests/locustfile.py --host=http://localhost:5004 LeaderboardServiceUser

# Test combined workflow (all services)
locust -f tests/locustfile.py --host=http://localhost:5001 CombinedUser
```

#### Headless Mode (Automated)

```bash
# Run with specific parameters (no web UI)
locust -f tests/locustfile.py \
  --host=http://localhost:5001 \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --html=report.html \
  CombinedUser
```

#### Using the Advanced Test Runner

```bash
# Use the advanced test runner script
./tests/run-locust-tests.sh -u 100 -r 10 -t 5m -m headless -c CombinedUser
```

Options:

- `-u, --users NUM`: Number of concurrent users (default: 50)
- `-r, --spawn-rate NUM`: Users to spawn per second (default: 5)
- `-t, --time TIME`: Test duration (e.g., 2m, 5m, 1h) (default: 2m)
- `-m, --mode MODE`: Test mode: web, headless (default: web)
- `-c, --class CLASS`: User class to test (default: CombinedUser)
- `-h, --host HOST`: Base host URL (default: <http://localhost:5001>)

### Test Coverage

The Locust test suite includes the following user classes:

#### AuthServiceUser

Tests authentication service endpoints:

- User registration (`POST /api/auth/register`)
- User login (`POST /api/auth/login`)
- Get profile (`GET /api/auth/profile`)
- Token validation (`POST /api/auth/validate`)
- Health check (`GET /health`)

**Host**: `http://localhost:5001`

#### CardServiceUser

Tests card service endpoints:

- Get all cards (`GET /api/cards`)
- Get cards by type (`GET /api/cards/by-type/{type}`)
- Get card by ID (`GET /api/cards/{card_id}`)
- Create random deck (`POST /api/cards/random-deck`)
- Get card statistics (`GET /api/cards/statistics`)
- Get card types (`GET /api/cards/types`)
- Health check (`GET /health`)

**Host**: `http://localhost:5002`

#### GameServiceUser

Tests game service endpoints:

- Create game (`POST /api/games`)
- Get game state (`GET /api/games/{game_id}`)
- Get player hand (`GET /api/games/{game_id}/hand`)
- Draw hand (`POST /api/games/{game_id}/draw-hand`)
- Play card (`POST /api/games/{game_id}/play-card`)
- Get turn info (`GET /api/games/{game_id}/turn-info`)
- Health check (`GET /health`)

**Host**: `http://localhost:5003`

#### LeaderboardServiceUser

Tests leaderboard service endpoints:

- Get leaderboard (`GET /api/leaderboard`)
- Get player statistics (`GET /api/leaderboard/player/{player_name}`)
- Get recent games (`GET /api/leaderboard/recent-games`)
- Get top players (`GET /api/leaderboard/top-players`)
- Get global statistics (`GET /api/leaderboard/statistics`)
- Health check (`GET /health`)

**Host**: `http://localhost:5004`

#### CombinedUser

Simulates realistic game workflows across all services:

- Complete game workflow (register → get cards → create deck → create game → play)
- View leaderboard and statistics
- Get user profile

**Host**: `http://localhost:5001` (starts at auth service)

### Test Configuration

Each user class has configurable:

- **Wait time**: Time between requests (e.g., `between(1, 3)` seconds)
- **Task weights**: Relative frequency of different tasks (higher number = more frequent)
- **Authentication**: Automatic token management for protected endpoints

### Understanding Results

When running Locust tests, you'll see:

- **Request statistics**: Response times, request counts, failure rates
- **Response time percentiles**: p50, p66, p75, p80, p90, p95, p98, p99, p100
- **Failure information**: Which requests failed and why
- **Real-time charts**: Visual representation of performance metrics

### Best Practices

1. **Start Small**: Begin with low user counts (10-50) to verify tests work correctly
2. **Gradual Ramp-up**: Use spawn-rate to gradually increase load
3. **Monitor Services**: Watch service logs and resource usage during tests
4. **Test Individual Services**: Use specific user classes to isolate performance issues
5. **Test Realistic Workflows**: Use CombinedUser for end-to-end performance testing

### Troubleshooting

#### Services Not Responding

```bash
# Check if services are running
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
```

#### Authentication Failures

- Ensure auth service is running and accessible
- Check that test users can be created/authenticated
- Verify token format matches service expectations

#### High Failure Rates

- Check service logs for errors
- Verify database connections
- Monitor resource usage (CPU, memory, network)
- Reduce user count or spawn rate

#### Connection Errors

- Verify Docker Desktop is running
- Ensure all services are running: `cd microservices && docker-compose ps`
- Rebuild and restart services if code changed: `docker-compose up -d --build`
- Check firewall/network settings
- Ensure ports are not blocked
- Verify Docker containers are healthy

---

## Postman API Tests

### Overview

The Postman collection (`postman_unit_tests.json`) contains unit tests for **three internal microservices**:

1. **Game Service** - Game operations and deck management
2. **User Service** - User account management and authentication
3. **Card Collection Service** - Card retrieval and filtering

### Prerequisites

1. **Start Docker Desktop**:
   - Ensure Docker Desktop is running on your machine
   - You can verify Docker is running with: `docker ps`

2. **Build and Start Microservices**:

   **Important**: Always use `--build` flag when starting services to ensure code changes are included:

   ```bash
   cd microservices
   docker-compose up -d --build
   ```

   Wait for all services to be ready (check with `docker-compose ps`).

3. **Install Newman** (Postman's CLI collection runner):

   ```bash
   # Install newman globally
   npm install -g newman
   ```

### Running Tests from Command Line

**Before running, ensure:**

1. Docker Desktop is running
2. Microservices are built and started: `cd microservices && docker-compose up -d --build`
3. Postman collection variables are updated (see Setup Instructions above)

```bash
# Run all Postman tests (from project root directory, not microservices folder)
newman run tests/postman_unit_tests.json

# Or with explicit environment variables
newman run tests/postman_unit_tests.json \
  --env-var "game_service_url=http://localhost:5003" \
  --env-var "user_service_url=http://localhost:5001" \
  --env-var "card_service_url=http://localhost:5002"
```

For more options (HTML reports, environment variables, etc.):

```bash
# Run with HTML report
newman run tests/postman_unit_tests.json --reporters html --reporter-html-export report.html

# Run with verbose output
newman run tests/postman_unit_tests.json --verbose
```

---

## Testing Checklist: Local vs CI/CD

Use this checklist to ensure your tests will pass in both environments:

### Before Committing Code

- [ ] **Fresh database test**: Run `docker-compose down -v && docker-compose up -d --build`
- [ ] **All unit tests pass**: `pytest tests/` (should see 0 failures)
- [ ] **All Postman tests pass**: `newman run tests/microservices_postman_collection.json`
- [ ] **Locust tests run without errors**: `locust -f tests/locustfile.py` (check for 400/401 errors)
- [ ] **Test setup is complete**: Every test creates all required data (users, games, decks)
- [ ] **No hardcoded IDs**: Tests don't rely on specific game IDs or user data from previous runs

### Common Issues and Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 UNAUTHORIZED` on player 2 | Trying to login before registering | Register player 2 first, then login if needed |
| `400 BAD REQUEST` on draw-hand | Game not in `active` state | Complete full game flow: create → accept → both players select deck |
| `404 NOT FOUND` on game endpoint | Game ID from previous test run | Create new game in test setup |
| Tests pass locally but fail in CI | Database has old test data | Reset database with `docker-compose down -v` |
| `405 METHOD NOT ALLOWED` | Missing game state transition | Ensure game goes through: `pending` → `deck_selection` → `active` |

### Quick Commands Reference

```bash
# Fresh start (replicates GitHub Actions)
cd microservices && docker-compose down -v && docker-compose up -d --build && cd ..

# Run all test suites
pytest tests/                                              # Python unit tests
newman run tests/microservices_postman_collection.json     # Postman API tests  
locust -f tests/locustfile.py                              # Locust performance tests

# Check service health
curl http://localhost:5001/health  # Auth
curl http://localhost:5002/health  # Card
curl http://localhost:5003/health  # Game
curl http://localhost:5004/health  # Leaderboard

# View service logs
docker-compose -f microservices/docker-compose.yml logs -f game-service
docker-compose -f microservices/docker-compose.yml logs -f auth-service
```
