I've created comprehensive unit tests for the authentication service with **45 test cases** covering:

## Test Coverage:

**1. Registration Tests (9 tests)**
- Successful registration
- Missing username/password
- Username too short (<3 chars)
- Password too short (<4 chars)
- Duplicate username (409 conflict)
- Whitespace trimming

**2. Login Tests (8 tests)**
- Successful login
- Wrong password
- Non-existent user
- Missing credentials
- Case-sensitive username validation

**3. Profile Management Tests (11 tests)**
- Get profile with valid token
- Get profile without/invalid token
- Update password successfully
- Password too short validation
- No data provided error
- Verify old password stops working after update

**4. Token Validation Tests (4 tests)**
- Valid token validation
- Invalid token rejection
- Missing token handling
- Malformed authorization header

**5. Edge Cases (5 tests)**
- Special characters in username
- Multiple concurrent sessions
- Empty string password
- Very long username
- Unicode/encoding handling

You can run these tests with:

```bash
python tests\test_auth_service.py
```

Or with pytest:

```bash
pytest tests\test_auth_service.py -v
```

The tests use unique timestamps to avoid conflicts and validate all response codes, error messages, and data structures returned by each endpoint.

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