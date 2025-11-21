# Testing Documentation

This document describes Python unit tests (pytest/unittest), Locust performance tests, and Postman API tests for the Battle Cards game microservices.

## Quick Start

**Before running any tests, ensure Docker Desktop is running and microservices are built and started:**

1. **Start Docker Desktop** (if not already running)
2. **Build and start all microservices:**

```bash
cd microservices
docker-compose up -d --build
```

Wait for all services to be healthy (this may take 1-2 minutes). You can check service status with:

```bash
docker-compose ps
```

**Then run tests:**

**1. Run All Locust Performance Tests:**

```bash
# From project root directory
locust -f tests/locustfile.py
```

Then open `http://localhost:8089` in your browser to configure and run tests.

**2. Run All Postman API Tests:**

```bash
# Run all Postman tests (default URLs are pre-configured)
newman run tests/postman_unit_tests.json
```

---

## Python Unit Tests (Unittest/Pytest)

### Overview

The project includes comprehensive Python unit tests covering all core game functionality. All tests can be run using a single master test runner script that executes both custom test functions and unittest-based tests.

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

### Running Python Unit Tests

#### Run Individual Test Modules

```bash
# Activate virtual environment first
source venv/bin/activate

# Run specific test modules
python3 -m unittest tests.test_game -v
python3 -m unittest tests.test_hand -v
python3 -m unittest tests.test_score -v
python3 -m unittest tests.test_profile -v
python3 -m unittest tests.test_view_card_collection -v
python3 -m unittest tests.test_view_old_matches -v
```

### Test Coverage

**Game Tests** (`test_game.py`):

- Card collection (39 cards, 13 per type)
- Deck creation and shuffling
- Random deck generation
- Deck validation (size, duplicates)
- Game initialization

**Hand Tests** (`test_hand.py`):

- Drawing 3 cards for a turn
- Playing a card and discarding others
- Multiple rounds
- Deck exhaustion handling

**Score Tests** (`test_score.py`):

- Battle scoring logic
- Score tracking across rounds

**Profile Tests** (`test_profile.py`) - *Requires Docker*:

- User account creation
- Username existence checking
- Profile retrieval
- Password updates
- Login verification

**View Tests**:

- Card collection display (`test_view_card_collection.py`)
- Old matches viewing (`test_view_old_matches.py`)

**Total: 21 Python unit tests** covering all core functionality.

### Test Structure

- **Custom Tests**: `test_game.py` and `test_hand.py` use custom test functions with `run_all_tests()`
- **Unittest Tests**: Other tests use Python's `unittest` framework
- **Database Tests**: Profile tests connect to PostgreSQL via Docker (automatic cleanup)

---

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
# From project root directory
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
# Run all Postman tests (from project root)
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

### Requirements Met

✅ **At least 3 internal microservices tested** (Game, User, Card Collection)
✅ **Each endpoint has:**

- One test for valid input (expecting 200 OK)
- One test for invalid input (expecting error response)

### Test Coverage

#### Game Service (8 tests)

- `POST /games/decks/random` - Create random deck (valid/invalid method)
- `POST /games` - Start new game (valid/missing player name)
- `GET /games/{gameId}` - Get game by ID (valid/non-existent ID)
- `POST /games/decks/validate` - Validate deck (valid/wrong number of cards)

#### User Service (8 tests)

- `POST /users/accounts` - Create account (valid/empty username)
- `POST /users/login` - Login (valid/wrong password)
- `GET /users/profile/{username}` - Get profile (valid/non-existent user)
- `PUT /users/profile/{username}` - Update profile (valid/empty password)

#### Card Collection Service (6 tests)

- `GET /cards` - Get all cards (valid/wrong method)
- `GET /cards?type={type}` - Get cards by type (valid/invalid type)
- `GET /cards/{cardId}` - Get card by ID (valid/non-existent ID)

**Total: 22 tests** (11 valid input tests, 11 invalid input tests)

### Setup Instructions

#### 1. Import the Collection

1. Open Postman
2. Click **Import** button
3. Select the `postman_unit_tests.json` file
4. The collection will appear in your Postman workspace

#### 2. Verify Environment Variables

The collection uses the following variables (pre-configured with correct defaults):

- `game_service_url` - Base URL for Game Service (default: `http://localhost:5003`)
- `user_service_url` - Base URL for Auth Service (default: `http://localhost:5001`)
- `card_service_url` - Base URL for Card Service (default: `http://localhost:5002`)
- `game_id` - Game ID for testing (set dynamically after creating a game)

**Default values are already configured correctly** in the collection file. If you need to override them:

1. Open Postman
2. Select the "Battle Cards - Unit Tests" collection
3. Click on the **Variables** tab
4. Update values if your services run on different ports
5. Click **Save** to persist the changes

**Or override via Command Line:**

```bash
# Override variables via command line if needed
newman run tests/postman_unit_tests.json \
  --env-var "game_service_url=http://localhost:5003" \
  --env-var "user_service_url=http://localhost:5001" \
  --env-var "card_service_url=http://localhost:5002"
```

#### 3. Running Unit Tests

**Option A: Run Individual Tests**

1. Select a test request in the collection
2. Click **Send**
3. View the test results in the **Test Results** tab

**Option B: Run All Tests in a Folder**

1. Right-click on a folder (e.g., "Game Service")
2. Select **Run folder**
3. Click **Run** to execute all tests in that folder

**Option C: Run Entire Collection**

1. Click on the collection name
2. Click **Run** button
3. Select which tests to run
4. Click **Run Battle Cards - Unit Tests**

### Test Structure

Each test includes:

1. **Request** - HTTP method, URL, headers, and body (if applicable)
2. **Test Scripts** - Automated assertions that verify:
   - Status code (200 OK for valid, 400/401/404/405 for invalid)
   - Response structure
   - Error messages (for invalid inputs)

### Expected Responses

#### Valid Input Tests

- **Status Code**: 200 OK (or 201 Created for POST requests)
- **Response Body**: Contains expected data structure
- **No Error**: Response should not contain error messages

#### Invalid Input Tests

- **Status Code**: 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), or 405 (Method Not Allowed)
- **Response Body**: Contains error message
- **Error Field**: Response includes an `error` or `error_message` field

### Integration Testing

The same Postman collection can be used for **integration testing** against the API Gateway:

1. Update the collection variables to point to the API Gateway URL
2. Update request paths to include the gateway routing (e.g., `/api/games/...`)
3. Run the same tests to verify end-to-end functionality

### Notes

- **Unit Tests**: Test each microservice in isolation (direct service URLs)
- **Integration Tests**: Test through the API Gateway with full architecture running
- Some tests may need adjustment based on your actual API implementation
- Ensure microservices are running before executing tests
- Some tests depend on data existing in the database (e.g., user accounts, games)

### Troubleshooting

#### Tests Failing with Connection Errors

- Verify Docker Desktop is running
- Ensure microservices are running: `cd microservices && docker-compose ps`
- Rebuild and restart services if code changed: `docker-compose up -d --build`
- **Verify Postman collection variables** (defaults are pre-configured, but check if you modified them):
  - `game_service_url` should be `http://localhost:5003`
  - `user_service_url` should be `http://localhost:5001`
  - `card_service_url` should be `http://localhost:5002`
- Check that ports match the configured URLs
- Test service health endpoints:

  ```bash
  curl http://localhost:5001/health
  curl http://localhost:5002/health
  curl http://localhost:5003/health
  ```

- Ensure Docker containers are healthy

#### Tests Failing with 404 Errors

- Verify the endpoint paths match your API implementation
- Check that routes are properly configured in your microservices

#### Tests Failing with Wrong Status Codes

- Review your API implementation to ensure it returns expected status codes
- Update test assertions if your API uses different status codes

### Example: Running Tests for Game Service

```bash
# 1. Ensure Docker Desktop is running

# 2. Build and start your microservices (with --build to include code changes)
cd microservices
docker-compose up -d --build

# 3. Wait for services to be healthy, then verify Game Service is running
curl http://localhost:5003/health

# 4. In Postman:
#    - Import postman_unit_tests.json
#    - Select "Game Service" folder
#    - Click "Run folder"
#    - Review test results
```

### Exporting Test Results

To export test results:

1. After running tests, click **Export Results**
2. Save as JSON or HTML
3. Include in your project documentation


## **Card Service Tests** (`test_card_service.py`) - 29 tests

**Endpoints tested:**
- ✅ `GET /api/cards` - Get all cards (3 tests: success, no token, invalid token)
- ✅ `GET /api/cards/by-type/<type>` - Get cards by type (6 tests: rock/paper/scissors success, invalid type, no token, case insensitive)
- ✅ `GET /api/cards/<id>` - Get card by ID (4 tests: success, not found, no token, invalid format)
- ✅ `POST /api/cards/random-deck` - Create random deck (7 tests: default size, custom size, too small, too large, negative, no token, randomness)
- ✅ `GET /api/cards/statistics` - Get card statistics (3 tests: success, no token, percentage validation)
- ✅ `GET /api/cards/types` - Get available types (3 tests: success, no token, valid types check)

## **Game Service Tests** (`test_game_service.py`) - 35 tests

**Endpoints tested:**
- ✅ `POST /api/games` - Create game (5 tests: success, missing player2, no token, invalid token, empty name)
- ✅ `GET /api/games/<game_id>` - Get game state (6 tests: player1/player2 success, not found, unauthorized, no token)
- ✅ `GET /api/games/<game_id>/hand` - Get player hand (4 tests: success, not found, unauthorized, no token)
- ✅ `POST /api/games/<game_id>/draw-hand` - Draw hand (4 tests: success, not found, unauthorized, no token)
- ✅ `POST /api/games/<game_id>/play-card` - Play card (6 tests: success, missing index, invalid index, negative index, not found, no token)
- ✅ `POST /api/games/<game_id>/resolve-round` - Resolve round (4 tests: success, not found, no token, cards not played)

## **Leaderboard Service Tests** (`test_leaderboard_service.py`) - 32 tests

**Endpoints tested:**
- ✅ `GET /api/leaderboard` - Global leaderboard (6 tests: success, with limit, max limit, no token, invalid token, ranking order)
- ✅ `GET /api/leaderboard/player/<name>` - Player stats (5 tests: success, nonexistent player, no token, invalid token, recent games structure)
- ✅ `GET /api/leaderboard/recent-games` - Recent games (5 tests: success, with limit, max limit, no token, invalid token)
- ✅ `GET /api/leaderboard/top-players` - Top players (4 tests: success, no token, invalid token, list sizes)
- ✅ `GET /api/leaderboard/statistics` - Global statistics (4 tests: success, no token, invalid token, consistency)
- ✅ Edge cases (3 tests: zero limit, negative limit, special characters)

## **Total Test Coverage: 96 tests**

Each test suite follows the same pattern as the auth service tests:
- **Valid input tests** - Verify successful operations with correct data
- **Invalid input tests** - Test error handling for bad data, missing fields, invalid values
- **Authentication tests** - Verify token requirements and invalid token handling
- **Authorization tests** - Check that users can only access their own resources
- **Edge cases** - Test boundary conditions, special characters, and unusual scenarios

You can run all the tests with:

```bash
# Run individual service tests
pytest tests\test_card_service.py -v
pytest tests\test_game_service.py -v
pytest tests\test_leaderboard_service.py -v

# Run all service tests together
pytest tests\test_card_service.py tests\test_game_service.py tests\test_leaderboard_service.py -v

# Run all tests including auth service
pytest tests\test_auth_service.py tests\test_card_service.py tests\test_game_service.py tests\test_leaderboard_service.py -v
```

Made changes.