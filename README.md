# Advanced Software Engineering Project

A Rock Paper Scissors battle card game implemented using a microservices architecture with REST APIs, JWT authentication, and persistent data storage.

## 📋 Project Overview

The Battle Cards application is a distributed system built with microservices, where players compete in card-based battles following rock-paper-scissors mechanics. The system features user authentication, card management, game logic, leaderboards, and comprehensive security measures.

**Key Features:**
- 🔐 JWT-based authentication with OAuth2-style token responses
- 🃏 Card collection and deck management
- 🎯 Real-time game logic and battle mechanics
- 🏆 Global leaderboards and player statistics
- 🛡️ Input sanitization and security protection
- 📊 Comprehensive testing (unit, integration, performance)
- 🐳 Docker containerization for easy deployment

## 🏗️ Architecture

The application is split into **four microservices** plus supporting infrastructure:

| Service | Port | Gateway Path | Purpose |
|---------|------|--------------|---------|
| **🔐 Auth Service** | 5001 | `/api/auth` | User authentication, registration, profile management |
| **🃏 Card Service** | 5002 | `/api/cards` | Card database, deck generation, statistics |
| **🎯 Game Service** | 5003 | `/api/games` | Game logic, state management, battle resolution |
| **🏆 Leaderboard Service** | 5004 | `/api/leaderboard` | Rankings, player statistics, game history |
| **🌐 Nginx Gateway** | 8080 | `/` | API Gateway and reverse proxy |
| **🗄️ PostgreSQL Database** | 5432 | - | Data persistence |

### Technology Stack

- **Backend**: Python 3.11, Flask 3.0.3, Gunicorn
- **Database**: PostgreSQL 16
- **Authentication**: JWT (Flask-JWT-Extended 4.6.0) with OAuth2-style responses
- **API Gateway**: Nginx (reverse proxy on port 8080)
- **Containerization**: Docker & Docker Compose
- **Security**: HTTPS/TLS, bcrypt password hashing, input sanitization

### API Access

All services are accessed through the Nginx gateway at `http://localhost:8080`. Direct service access is not recommended in production.

**Base URL**: `http://localhost:8080/api`

## 🚀 Quick Start

"The Battle Cards microservices project uses an Nginx API Gateway on port 8080 for all service access. All services (auth, card, game, leaderboard) are accessed through the gateway at <http://localhost:8080/api/>*. The project includes comprehensive testing with pytest (45+ unit tests), Postman/Newman (50 API endpoint tests), and Locust performance tests. All tests are automated via GitHub Actions with 3 parallel test jobs. Complete documentation is available in the documentation/ folder."

## Quick Start

**To build and start all microservices:**

1. **Navigate to the microservices directory:**
   ```bash
   cd microservices
   ```

2. **Build and start all services:**
   ```bash
   ./build-and-start.sh
   ```

   The build script automatically:
   - Generates a secure `GAME_HISTORY_KEY` if one doesn't exist
   - Saves the key to `.env` (gitignored for security)
   - Builds and starts all Docker containers

**Note:** The build script automatically generates and saves a `GAME_HISTORY_KEY` to `.env` if one doesn't exist. This key is required for game history encryption and tamper detection.

3. **Verify services are running:**
   ```bash
   # Check gateway health
   curl http://localhost:8080/health
   
   # Check individual services
   curl http://localhost:8080/api/auth/health
   curl http://localhost:8080/api/cards/health
   curl http://localhost:8080/api/games/health
   curl http://localhost:8080/api/leaderboard/health
   ```

4. **Check container status:**
   ```bash
   docker-compose ps
   ```

### Alternative: Manual Build

If you prefer manual control:

```bash
cd microservices
docker-compose up -d --build
```

**Note**: The `GAME_HISTORY_KEY` is required for game history encryption. The build script generates it automatically, but if building manually, you'll need to set it in the `.env` file.

You can generate one using the following command:
```bash
python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

### Stopping Services

```bash
cd microservices
docker-compose down
```

## 📚 Documentation

Comprehensive documentation is available in the `documentation/` folder:

- **[API Documentation](documentation/API_Documentation.md)** - Complete REST API reference
- **[Security Guide](documentation/SECURITY_GUIDE.md)** - Security features and input validation
- **[Testing Guide](documentation/MICROSERVICE_TESTING.md)** - Unit and integration testing
- **[Performance Testing](documentation/PERFORMANCE_TESTING.md)** - Load testing with Locust
- **[Docker Setup](documentation/README-DOCKER.md)** - Docker configuration details
- **[OpenAPI Specification](openapi.yaml)** - Machine-readable API specification

## 🧪 Testing

The project includes comprehensive testing across multiple levels:

### Unit Tests (pytest)

```bash
# Run all unit tests
python -m pytest tests/ -v

# Run specific service tests
python -m pytest tests/test_auth_service.py -v
python -m pytest tests/test_game_service.py -v
python -m pytest tests/test_card_service.py -v
python -m pytest tests/test_leaderboard_service.py -v
```

**Test Coverage**: 96+ unit tests covering all microservices

### Integration Tests (Postman/Newman)

The project includes a comprehensive Postman collection with automated test scripts that validate response structure, status codes, and data integrity.

**Prerequisites:**
```bash
# Install Newman (Postman CLI)
npm install -g newman
```

**Running Tests:**
```bash
# From project root directory (not microservices folder)
newman run tests/microservices_postman_collection.json \
  --env-var "BASE_URL=http://localhost:8080"

# With HTML report
newman run tests/microservices_postman_collection.json \
  --env-var "BASE_URL=http://localhost:8080" \
  --reporters html --reporter-html-export report.html
```

**Test Coverage**: 50+ API endpoint tests with automated assertions covering:
- Request/response validation
- Status code verification
- Data structure checks
- Error handling validation

See [TESTING_README.md](documentation/TESTING_README.md) for detailed Postman testing instructions.

### Performance Tests (Locust)

```bash
# Run Locust performance tests
cd tests
locust -f locustfile.py --host=http://localhost:8080
```

See [PERFORMANCE_TESTING.md](documentation/PERFORMANCE_TESTING.md) for detailed instructions.

### Automated Testing (GitHub Actions)

All tests run automatically on push/PR via GitHub Actions with 3 parallel test jobs.

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) with OAuth2-style responses:

1. **Register or Login** to receive a token:
   ```bash
   curl -X POST http://localhost:8080/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"player1","password":"pass1234"}'
   ```

2. **Response includes OAuth2-style fields:**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer",
     "expires_in": 86400,
     "user": {"id": 1, "username": "player1"}
   }
   ```

3. **Use token in subsequent requests:**
   ```bash
   curl -X GET http://localhost:8080/api/cards \
     -H "Authorization: Bearer <your_token>"
   ```

## 📖 API Endpoints Overview

### Auth Service (`/api/auth`)
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /profile` - Get user profile (requires auth)
- `PUT /profile` - Update user profile (requires auth)
- `POST /validate` - Validate JWT token (requires auth)

### Card Service (`/api/cards`)
- `GET /` - Get all cards (requires auth)
- `GET /by-type/{type}` - Get cards by type (requires auth)
- `GET /{id}` - Get specific card (requires auth)
- `POST /random-deck` - Create random deck (requires auth)
- `GET /statistics` - Get card database statistics (requires auth)
- `GET /types` - Get available card types (requires auth)

### Game Service (`/api/games`)
- `POST /` - Create new game (requires auth)
- `GET /{game_id}` - Get game state (requires auth)
- `GET /{game_id}/hand` - Get player's current hand (requires auth)
- `POST /{game_id}/draw-hand` - Draw new hand (requires auth)
- `POST /{game_id}/play-card` - Play a card (requires auth)
- `POST /{game_id}/resolve-round` - Resolve round (requires auth)
- `POST /{game_id}/end` - End game (requires auth)
- `GET /user/{username}` - Get user's games (requires auth)

### Leaderboard Service (`/api/leaderboard`)
- `GET /` - Get global leaderboard (requires auth)
- `GET /player/{name}` - Get player statistics (requires auth)
- `GET /recent-games` - Get recent completed games (requires auth)
- `GET /top-players` - Get top players by metrics (requires auth)
- `GET /statistics` - Get global game statistics (requires auth)

For complete API documentation, see [API_Documentation.md](documentation/API_Documentation.md) or [openapi.yaml](openapi.yaml).

## 🛠️ Development

### Local Development Setup

```bash
# Start only PostgreSQL
cd microservices
docker-compose up -d postgresql

# Run service locally (example: auth-service)
cd microservices/auth-service
pip install -r requirements.txt
export DATABASE_URL="postgresql://gameuser:gamepassword@localhost:5432/battlecards"
export JWT_SECRET_KEY="your-secret-key"
python app.py
```

### Environment Variables

The `build-and-start.sh` script automatically creates a `.env` file. You can also configure manually:

```env
# Database
DATABASE_URL=postgresql://gameuser:gamepassword@postgresql:5432/battlecards

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# Game History Encryption (auto-generated by build script)
GAME_HISTORY_KEY=<32-byte-base64-encoded-key>

# Service URLs (for inter-service communication)
AUTH_SERVICE_URL=http://auth-service:5001
CARD_SERVICE_URL=http://card-service:5002
```

**Important:** The `.env` file is gitignored for security. Never commit secrets to version control.

## 🔍 Troubleshooting

### Services Not Starting

```bash
cd microservices
# Check service logs
docker-compose logs auth-service
docker-compose logs postgresql

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
cd microservices
# Reset database
docker-compose down -v
docker-compose up postgresql -d
# Wait for database to be ready, then start other services
docker-compose up -d
```

### Health Checks

```bash
# Check all services
curl http://localhost:8080/health

# Check individual services
curl http://localhost:8080/api/auth/health
curl http://localhost:8080/api/cards/health
curl http://localhost:8080/api/games/health
curl http://localhost:8080/api/leaderboard/health
```

## 📊 Project Statistics

- **Microservices**: 4 (Auth, Card, Game, Leaderboard)
- **Unit Tests**: 96+ tests
- **Integration Tests**: 50+ Postman tests
- **Performance Tests**: Locust load testing
- **API Endpoints**: 30+ REST endpoints
- **Documentation**: 7 comprehensive guides

## 🎯 Project Status

✅ **Completed Features:**
- User authentication and authorization (OAuth2-style JWT)
- Card collection and deck management
- Game logic and battle mechanics
- Leaderboards and statistics
- Input sanitization and security
- Comprehensive testing suite
- Docker containerization
- API Gateway with Nginx
- Game history encryption and tamper detection

## 📝 License

MIT License - see LICENSE file for details.

---

**For detailed documentation, see the [documentation/](documentation/) folder.**
