# 📘 BattleCards Microservices — Refactoring & Changes Documentation

Full Technical Summary of All Fixes Across Auth, Game, Card, and Leaderboard Services
(January 2025 Refactor — DB Manager Integration & API Normalization)

This document explains every major refactor performed across the four microservices:
* Auth Service
* Card Service
* Game Service
* Leaderboard Service

The goal of this refactor was to:
✔️ Replace direct DB connections with unit_of_work() (DB Manager)
✔️ Standardize API endpoints across all services
✔️ Apply consistent JWT/OAuth2-style authentication behavior
✔️ Enforce centralized security: sanitization, validation, error handling
✔️ Remove duplicate logic and unify codebase architecture
✔️ Fix all SQL statements to be safe, clean, consistent
✔️ Prepare all services for unified integration and automated testing

# 🧩 1. Global Changes Across All Services
1.1 Migration to unit_of_work()

All microservices previously opened raw Postgres connections via:

conn = get_db_connection()
cursor = conn.cursor()

This caused:
- inconsistent transactions
- repeated connection logic
- missing rollback/cleanup handling
- duplicated boilerplate

✔️ Now every DB interaction goes through:
with unit_of_work() as cur:
    cur.execute(...)

# Benefits: #
- Automatic commit/rollback
- Centralized error handling
- Transaction safety
- Cleaner application code
- Consistent cursor behavior

1.2 Unified Input Sanitization Layer

We integrated:

from input_sanitizer import InputSanitizer, SecurityMiddleware, require_sanitized_input

✔️ New security rules applied:

username validation
password validation
email validation
integer validation
allowed characters enforcement
max length constraints

✔️ Endpoints now receive clean, validated, and normalized input.
1.3 Standardization of JWT Authentication

Previously:
- Some services returned 422 for invalid/missing tokens
- Some treated expired tokens incorrectly
- Some used custom token checks

✔️ Now all services use the same handlers:

* invalid_token_loader → 401
* unauthorized_loader → 401
* expired_token_loader → 401

✔️ All secured endpoints now use:
@jwt_required()

✔️ All services issue/validate tokens in OAuth2-style:
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": <seconds>
}

1.4 Unified Error Response Format

* Before refactor:
inconsistent messages
inconsistent status codes
sometimes returning HTML or raw text

✔️ Now all services return:

For errors:
{"error": "<message>"}

For success:
{ "message": "..." }

1.5 Endpoint Normalization

Each microservice now follows:
/api/<service>/<resource>

Examples:
/api/auth/login
/api/cards/<id>
/api/games/<game_id>/play-card
/api/leaderboard/top-players

This makes the API gateway much simpler.

# 🔐 2. Auth Service — Refactoring Summary
✔️ 2.1 Replaced raw DB access with unit_of_work()

All routes (register, login, profile, etc.) now use:
with unit_of_work() as cur:

✔️ 2.2 InputSanitizer integrated everywhere

We added validation for:
- username
- password
- email

JSON request body existence

✔️ 2.3 Corrected token expiration logic

Old code crashed if config provided integer instead of timedelta.

New version:

expires_in = (
    int(jwt_expires.total_seconds())
    if hasattr(jwt_expires, "total_seconds")
    else int(jwt_expires)
)

✔️ 2.4 Fixed duplicate username check

Some earlier versions incorrectly compared unvalidated or unsanitized values.

✔️ 2.5 Fixed profile update endpoint

Originally:

Did not check if user existed
Did not sanitize input
Did not handle missing JSON

** Now all fixed. **

✔️ 2.6 Added missing /api/auth/validate endpoint

Standardized to return:

{"valid": true, "username": "<user>"}

# 🎮 3. Game Service — Refactoring Summary

The Game Service had the most inconsistent DB behavior.

✔️ 3.1 Replaced all DB connections with unit_of_work()

* All queries in:
start game
fetch game
fetch hand
draw hand
play card
resolve round

→ are now transaction-safe and consistent.

✔️ 3.2 Standardized all ownership checks

Before:
some endpoints didn’t verify that the token user belonged to the game

Now each endpoint uses:

if current_user not in (game["player1_name"], game["player2_name"]):
    return jsonify({"error": "Forbidden"}), 403

✔️ 3.3 Normalized all error messages & HTTP codes

Examples:

404 for nonexistent games
403 for unauthorized access
400 for missing card index
401 for missing token

✔️ 3.4 Fixed SQL mismatches and inconsistent column names

Some queries used:

p1_name instead of player1_name
p2_score instead of player2_score

All normalized to correct schema.

✔️ 3.5 Standardized request bodies & responses

All endpoints now return uniform structure.

# 🃏 4. Card Service — Refactoring Summary
✔️ 4.1 Integrated DB manager

All card queries now use:

with unit_of_work() as cur:
    cur.execute(...)

✔️ 4.2 Validated sanitized card type and deck size

Previously missing validation led to:

negative deck size
huge deck requests
invalid type names

Now caught by:

InputSanitizer.validate_integer(...)
InputSanitizer.validate_card_type(...)

✔️ 4.3 Standardized /by-type/<type> route

Now case-insensitive.

✔️ 4.4 Fixed random deck endpoint

Before: possible duplicate cards
Now: guaranteed unique cards.

✔️ 4.5 Unified error format for:

invalid type
missing token
invalid token
card not found

# 🏆 5. Leaderboard Service — Refactoring Summary

This service was the most complicated SQL-wise.

✔️ 5.1 Removed direct psycopg2 connection

Replaced with unit_of_work().

✔️ 5.2 Fixed ranking queries:

unified scoring logic

properly handling ties

fixed win/loss calculations

corrected player_stats FULL JOIN logic

✔️ 5.3 Fixed limit parameter validation

Now sanitized:

limit = InputSanitizer.validate_integer(limit_param, min_val=1, max_val=100)

✔️ 5.4 Normalized player stats endpoint

Issues fixed:

* unsanitized URL path parameter
* incorrect recent games scoring
* missing response structure

✔️ 5.5 Fixed SQL for recent games and statistics pages

All timestamps converted to:

.isoformat()

✔️ 5.6 Added proper error codes

400 for invalid player name
404 for missing player
401 for bad token
500 for internal errors

# 🧩 6. Cross-Service Consistency Improvements
✔️ All services now use:

@jwt_required()

unit_of_work()

InputSanitizer

consistent response schemas

consistent endpoint naming

consistent debugging / logging patterns

✔️ All services now avoid:
- raw DB connections
- unhandled SQL errors
- different return formats
- different token behavior
- duplicated logic

# 🧪 7. Testing Improvements (Post-Refactor)

Although not part of the refactor itself, all changes were made to support:

Postman automated test suites
PyTest integration tests
API gateway integration
CI/CD expandable pipeline
Each service now supports:
valid request tests
invalid input tests
invalid token tests
missing token tests
authorization tests
edge case tests

# 🏁 8. Summary

This refactor unified the entire microservices ecosystem:

Before:
- inconsistent code
- raw database code
- unsanitized inputs
- mismatched endpoint styles
- broken or insecure endpoints
- unpredictable error handling

After:
- clean, safe, centralized DB handling
- robust validation
- unified token logic
- consistent error codes
- production-ready API layer
- integration-friendly endpoints

# 🧪 Verification & tests to run

* Start services (docker-compose or individually).

* Health endpoints:

curl http://localhost:5001/health (auth)
curl http://localhost:5002/health (card)
curl http://localhost:5003/health (game)
curl http://localhost:5004/health (leaderboard)