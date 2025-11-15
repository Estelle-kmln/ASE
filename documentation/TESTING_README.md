# Testing Documentation

This document describes both Python unit tests and Postman API tests for the Battle Cards game.

## Python Unit Tests

### Overview

The project includes comprehensive Python unit tests covering all core game functionality. All tests can be run using a single master test runner script.

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
   - Ensure Docker is running
   - Start PostgreSQL: `docker-compose up -d postgresql`
   - Database available at `localhost:5432`

### Running Python Unit Tests

#### Run All Tests (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python3 tests/run_all_tests.py
```

This will execute:

- Custom test functions (game logic, hand management)
- Unittest-based tests (scoring, profiles, views)
- Display a comprehensive summary

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

## Postman API Tests

### Overview

The Postman collection (`postman_unit_tests.json`) contains unit tests for **three internal microservices**:

1. **Game Service** - Game operations and deck management
2. **User Service** - User account management and authentication
3. **Card Collection Service** - Card retrieval and filtering

## Requirements Met

✅ **At least 3 internal microservices tested** (Game, User, Card Collection)
✅ **Each endpoint has:**

- One test for valid input (expecting 200 OK)
- One test for invalid input (expecting error response)

## Test Coverage

### Game Service (8 tests)

- `POST /games/decks/random` - Create random deck (valid/invalid method)
- `POST /games` - Start new game (valid/missing player name)
- `GET /games/{gameId}` - Get game by ID (valid/non-existent ID)
- `POST /games/decks/validate` - Validate deck (valid/wrong number of cards)

### User Service (8 tests)

- `POST /users/accounts` - Create account (valid/empty username)
- `POST /users/login` - Login (valid/wrong password)
- `GET /users/profile/{username}` - Get profile (valid/non-existent user)
- `PUT /users/profile/{username}` - Update profile (valid/empty password)

### Card Collection Service (6 tests)

- `GET /cards` - Get all cards (valid/wrong method)
- `GET /cards?type={type}` - Get cards by type (valid/invalid type)
- `GET /cards/{cardId}` - Get card by ID (valid/non-existent ID)

**Total: 22 tests** (11 valid input tests, 11 invalid input tests)

## Setup Instructions

### 1. Import the Collection

1. Open Postman
2. Click **Import** button
3. Select the `postman_unit_tests.json` file
4. The collection will appear in your Postman workspace

### 2. Configure Environment Variables

The collection uses the following variables (set in the collection variables):

- `game_service_url` - Base URL for Game Service (default: `http://localhost:8001`)
- `user_service_url` - Base URL for User Service (default: `http://localhost:8002`)
- `card_service_url` - Base URL for Card Collection Service (default: `http://localhost:8003`)
- `game_id` - Game ID for testing (set dynamically after creating a game)

**To update these values:**

1. Select the collection in Postman
2. Go to the **Variables** tab
3. Update the values to match your microservice URLs

### 3. Running Unit Tests

#### Option A: Run Individual Tests

1. Select a test request in the collection
2. Click **Send**
3. View the test results in the **Test Results** tab

#### Option B: Run All Tests in a Folder

1. Right-click on a folder (e.g., "Game Service")
2. Select **Run folder**
3. Click **Run** to execute all tests in that folder

#### Option C: Run Entire Collection

1. Click on the collection name
2. Click **Run** button
3. Select which tests to run
4. Click **Run Battle Cards - Unit Tests**

## Test Structure

Each test includes:

1. **Request** - HTTP method, URL, headers, and body (if applicable)
2. **Test Scripts** - Automated assertions that verify:
   - Status code (200 OK for valid, 400/401/404/405 for invalid)
   - Response structure
   - Error messages (for invalid inputs)

## Expected Responses

### Valid Input Tests

- **Status Code**: 200 OK (or 201 Created for POST requests)
- **Response Body**: Contains expected data structure
- **No Error**: Response should not contain error messages

### Invalid Input Tests

- **Status Code**: 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), or 405 (Method Not Allowed)
- **Response Body**: Contains error message
- **Error Field**: Response includes an `error` or `error_message` field

## Integration Testing

The same Postman collection can be used for **integration testing** against the API Gateway:

1. Update the collection variables to point to the API Gateway URL
2. Update request paths to include the gateway routing (e.g., `/api/games/...`)
3. Run the same tests to verify end-to-end functionality

## Notes

- **Unit Tests**: Test each microservice in isolation (direct service URLs)
- **Integration Tests**: Test through the API Gateway with full architecture running
- Some tests may need adjustment based on your actual API implementation
- Ensure microservices are running before executing tests
- Some tests depend on data existing in the database (e.g., user accounts, games)

## Troubleshooting

### Tests Failing with Connection Errors

- Verify microservices are running
- Check that ports match the configured URLs
- Ensure Docker containers are up if using Docker Compose

### Tests Failing with 404 Errors

- Verify the endpoint paths match your API implementation
- Check that routes are properly configured in your microservices

### Tests Failing with Wrong Status Codes

- Review your API implementation to ensure it returns expected status codes
- Update test assertions if your API uses different status codes

## Example: Running Tests for Game Service

```bash
# 1. Start your microservices
docker-compose up -d

# 2. Verify Game Service is running on port 8001
curl http://localhost:8001/health

# 3. In Postman:
#    - Import postman_unit_tests.json
#    - Select "Game Service" folder
#    - Click "Run folder"
#    - Review test results
```

## Exporting Test Results

To export test results:

1. After running tests, click **Export Results**
2. Save as JSON or HTML
3. Include in your project documentation
