# Battle Cards Microservices

A Rock Paper Scissors battle card game implemented using microservices architecture with REST APIs, HTTPS communication, and persistent data storage.

## Key Features

- 🔐 **JWT Authentication** - OAuth2-style tokens with automatic refresh
- 🔒 **Session Management** - Concurrent session control (strict mode - one session per user)
- 🛡️ **Account Security** - Lockout after 3 failed login attempts (15-minute timeout)
- 📝 **Action Logging** - Comprehensive audit trail of all user actions
- 🎴 **Deck Selection** - Players build custom decks (22 cards) before games start
- 🎯 **Game Invitations** - Send, accept, decline, or cancel game invitations
- ⏱️ **Live Timer** - Real-time countdown displayed in frontend
- 🏆 **Leaderboards** - Player rankings and game history
- 🔐 **HTTPS/TLS** - Encrypted communication with SSL certificates
- 🐳 **Dockerized** - Full containerization for easy deployment

## Architecture

The application is split into five microservices:

1. **Auth Service** (Port 5001) - User authentication, profile management, session control, token refresh
2. **Card Service** (Port 5002) - Card database, deck generation, and statistics  
3. **Game Service** (Port 5003) - Game logic, state management, invitations, deck selection
4. **Leaderboard Service** (Port 5004) - Game results, rankings, and player statistics
5. **Logs Service** (Port 5005) - User action logging and security audit trails

All services communicate through an Nginx API Gateway (Port 8443 for HTTPS, Port 8080 redirects to HTTPS) and use PostgreSQL for data persistence.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL (for SSL certificate generation)

## Get Started

### 1. Clone the Repository

```bash
git clone https://github.com/Estelle-kmln/ASE.git
cd ASE/microservices
```

### 2. Install Dependencies

All dependencies are managed through Docker containers. No local Python installation required.

### 3. Build and Run the Backend

**Recommended: Use the automated build script** (handles GAME_HISTORY_KEY automatically):

```bash
# Build and start all services (automatically generates GAME_HISTORY_KEY if needed)
./build-and-start.sh

# Check service health
docker-compose ps
```

**Alternative: Manual build** (requires setting GAME_HISTORY_KEY manually):

```bash
# Build all services
docker-compose build

# Start all services in detached mode
docker-compose up -d

# Check service health
docker-compose ps
```

**Note:** The build script automatically generates and saves a `GAME_HISTORY_KEY` to `.env` if one doesn't exist. This key is required for game history encryption and is gitignored for security.

### 4. Verify Installation

Check that all services are running:
```bash
curl -k https://localhost:8443/health
```

**Note:** The `-k` flag is required for self-signed certificates. Your browser will show a security warning for self-signed certificates - this is expected in development. Click "Advanced" and "Proceed to localhost" to continue.

Expected response:
```json
{"status":"healthy","gateway":"api-gateway"}
```

### 5. Run Tests

```bash
# Run integration tests
python -m pytest tests/ -v

# Test specific service
curl -k https://localhost:8443/api/auth/health
curl -k https://localhost:8443/api/cards/health  
curl -k https://localhost:8443/api/games/health
curl -k https://localhost:8443/api/leaderboard/health
```

## API Documentation

### Base URL
```
https://localhost:8443/api
```

**Note:** All HTTP requests to port 8080 are automatically redirected to HTTPS on port 8443. The application uses self-signed SSL certificates for development. Browsers will show a security warning - click "Advanced" and "Proceed to localhost" to continue.

### Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Service Endpoints

#### Auth Service (`/api/auth/`)
- `POST /register` - Register new user
- `POST /login` - User login (returns access_token and refresh_token)
- `POST /refresh` - Refresh access token using refresh token
- `POST /logout` - Logout and invalidate tokens
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile
- `POST /validate` - Validate JWT token
- `GET /sessions` - Get user's active sessions
- `DELETE /sessions/{session_id}` - Logout from specific device
- `POST /sessions/revoke-all` - Logout from all devices

#### Card Service (`/api/cards/`)
- `GET /` - Get all cards
- `GET /by-type/{type}` - Get cards by type (rock/paper/scissors)
- `GET /{id}` - Get specific card
- `POST /random-deck` - Create random deck of cards
- `GET /statistics` - Get card database statistics
- `GET /types` - Get available card types and powers

#### Game Service (`/api/games/`)
- `POST /` - Create new game and send invitation
- `GET /{game_id}` - Get game state
- `POST /{game_id}/accept-invitation` - Accept game invitation
- `POST /{game_id}/decline-invitation` - Decline game invitation
- `POST /{game_id}/cancel-invitation` - Cancel sent invitation
- `POST /{game_id}/select-deck` - Select deck (manual or random)
- `GET /{game_id}/hand` - Get player's current hand
- `POST /{game_id}/draw-hand` - Draw new hand from deck
- `POST /{game_id}/play-card` - Play a card from hand
- `POST /{game_id}/resolve-round` - Resolve round after both players play
- `POST /{game_id}/end` - End game
- `GET /user/{username}` - Get user's games
- `GET /pending-invitations` - Get user's pending invitations

#### Leaderboard Service (`/api/leaderboard/`)
- `GET /` - Get global leaderboard
- `GET /player/{name}` - Get player statistics
- `GET /recent-games` - Get recent completed games
- `GET /top-players` - Get top players by various metrics
- `GET /statistics` - Get global game statistics

#### Logs Service (`/api/logs/`) - Admin Only
- `GET /list` - Get paginated list of logs
- `GET /user/{username}` - Get logs for specific user
- `GET /action/{action_type}` - Get logs by action type
- `GET /search` - Search logs with filters
- `GET /statistics` - Get logging statistics

## Environment Variables

The `build-and-start.sh` script automatically creates a `.env` file with a generated `GAME_HISTORY_KEY` if one doesn't exist. You can also create a `.env` file manually for custom configuration:

```env
# Database
DATABASE_URL=postgresql://gameuser:gamepassword@postgresql:5432/battlecards

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# Game History Encryption (automatically generated by build script if not set)
GAME_HISTORY_KEY=<32-byte-base64-encoded-key>

# Service URLs (for inter-service communication)
AUTH_SERVICE_URL=http://auth-service:5001
CARD_SERVICE_URL=http://card-service:5002
```

**Important:** The `.env` file is gitignored for security. Never commit secrets to version control.

## Development

### Adding New Services

1. Create service directory: `mkdir microservices/new-service`
2. Add `requirements.txt` with pinned versions
3. Create Flask app in `app.py`
4. Add `Dockerfile`
5. Update `docker-compose.yml`
6. Add routes to `nginx/nginx.conf`

### Testing with Postman

Import the API endpoints into Postman for testing. **Important**: Disable SSL certificate verification in Postman settings for self-signed certificates.

1. **Register User:**
   ```
   POST https://localhost:8443/api/auth/register
   Body: {"username": "testuser", "password": "testpass123"}
   ```

2. **Login (receives access_token and refresh_token):**
   ```
   POST https://localhost:8443/api/auth/login
   Body: {"username": "testuser", "password": "testpass123"}
   ```
   
3. **Refresh Token:**
   ```
   POST https://localhost:8443/api/auth/refresh
   Headers: Authorization: Bearer <refresh_token>
   ```

4. **Get Cards:**
   ```
   GET https://localhost:8443/api/cards/
   Headers: Authorization: Bearer <access_token>
   ```

5. **Create Game with Invitation:**
   ```
   POST https://localhost:8443/api/games/
   Headers: Authorization: Bearer <access_token>
   Body: {"player2_name": "opponent"}
   ```

6. **View Logs (Admin Only):**
   ```
   GET https://localhost:8443/api/logs/list?page=0&size=20
   Headers: Authorization: Bearer <admin_access_token>
   ```

### Local Development

Run individual services for development:

```bash
# Start database only
docker-compose up postgresql -d

# Run auth service locally
cd microservices/auth-service
pip install -r requirements.txt
python app.py
```

## Production Deployment

### Security Considerations

1. **Change default secrets:**
   ```env
   JWT_SECRET_KEY=<strong-random-secret>
   POSTGRES_PASSWORD=<strong-db-password>
   ```

2. **SSL Certificates:**
   - The application uses self-signed certificates for development (located in `nginx/ssl/`)
   - For production, replace with CA-signed certificates (e.g., Let's Encrypt)
   - Configure proper DNS and domains for production deployment
   - Self-signed certificates will trigger browser security warnings - this is expected in development

3. **Enable security features:**
   - Database connection encryption
   - Rate limiting
   - API authentication for inter-service communication

### Scaling

Scale individual services based on load:

```bash
# Scale specific services
docker-compose up -d --scale auth-service=3
docker-compose up -d --scale game-service=2
```

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check service logs
docker-compose logs auth-service
docker-compose logs postgresql

# Restart services
docker-compose restart
```

**Database connection issues:**
```bash
# Reset database
docker-compose down -v
docker-compose up postgresql -d
# Wait for database to be ready
docker-compose up -d
```

### Health Checks

Monitor service health:
```bash
# Check all services
curl http://localhost:8080/health

# Check individual services
curl http://localhost:8080/api/auth/health
curl http://localhost:8080/api/cards/health
curl http://localhost:8080/api/games/health
curl http://localhost:8080/api/leaderboard/health
```

## Tech Stack

- **Backend:** Python 3.11, Flask 3.0.3
- **Database:** PostgreSQL 16
- **Authentication:** JWT (Flask-JWT-Extended 4.6.0)
- **API Gateway:** Nginx
- **Containerization:** Docker & Docker Compose
- **Security:** HTTPS/TLS, bcrypt password hashing

## License

MIT License - see LICENSE file for details.