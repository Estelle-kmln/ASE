# Battle Cards Microservices

A Rock Paper Scissors battle card game implemented using microservices architecture with REST APIs, HTTPS communication, and persistent data storage.

## Architecture

The application is split into four microservices:

1. **Auth Service** (Port 5001) - User authentication and profile management
2. **Card Service** (Port 5002) - Card database and statistics  
3. **Game Service** (Port 5003) - Game logic and state management
4. **Leaderboard Service** (Port 5004) - Game results and rankings

All services communicate over HTTPS through an Nginx API Gateway (Port 8443) and use PostgreSQL for data persistence.

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

### 3. Generate SSL Certificates

For HTTPS support, generate self-signed certificates:

**On Linux/macOS:**
```bash
chmod +x generate-ssl.sh
./generate-ssl.sh
```

**On Windows (PowerShell):**
```powershell
.\generate-ssl.ps1
```

**Manual SSL Setup (if scripts fail):**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/server.key \
    -out nginx/ssl/server.crt \
    -subj "/C=US/ST=State/L=City/O=BattleCards/CN=localhost"
```

### 4. Build and Run the Backend

```bash
# Build all services
docker-compose build

# Start all services in detached mode
docker-compose up -d

# Check service health
docker-compose ps
```

### 5. Verify Installation

Check that all services are running:
```bash
curl -k https://localhost:8443/health
```

Expected response:
```json
{"status":"healthy","gateway":"api-gateway"}
```

### 6. Run Tests

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

### Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Service Endpoints

#### Auth Service (`/api/auth/`)
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile
- `POST /validate` - Validate JWT token

#### Card Service (`/api/cards/`)
- `GET /` - Get all cards
- `GET /by-type/{type}` - Get cards by type (rock/paper/scissors)
- `GET /{id}` - Get specific card
- `POST /random-deck` - Create random deck of cards
- `GET /statistics` - Get card database statistics
- `GET /types` - Get available card types and powers

#### Game Service (`/api/games/`)
- `POST /` - Create new game
- `GET /{game_id}` - Get game state
- `GET /{game_id}/hand` - Get player's current hand
- `POST /{game_id}/draw-hand` - Draw new hand
- `POST /{game_id}/play-card` - Play a card
- `POST /{game_id}/resolve-round` - Resolve round after both players play
- `POST /{game_id}/end` - End game
- `GET /user/{username}` - Get user's games

#### Leaderboard Service (`/api/leaderboard/`)
- `GET /` - Get global leaderboard
- `GET /player/{name}` - Get player statistics
- `GET /recent-games` - Get recent completed games
- `GET /top-players` - Get top players by various metrics
- `GET /statistics` - Get global game statistics

## Environment Variables

Create a `.env` file for custom configuration:

```env
# Database
DATABASE_URL=postgresql://gameuser:gamepassword@postgresql:5432/battlecards

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# Service URLs (for inter-service communication)
AUTH_SERVICE_URL=http://auth-service:5001
CARD_SERVICE_URL=http://card-service:5002
```

## Development

### Adding New Services

1. Create service directory: `mkdir microservices/new-service`
2. Add `requirements.txt` with pinned versions
3. Create Flask app in `app.py`
4. Add `Dockerfile`
5. Update `docker-compose.yml`
6. Add routes to `nginx/nginx.conf`

### Testing with Postman

Import the API endpoints into Postman for testing:

1. **Register User:**
   ```
   POST https://localhost:8443/api/auth/register
   Body: {"username": "testuser", "password": "testpass"}
   ```

2. **Login:**
   ```
   POST https://localhost:8443/api/auth/login
   Body: {"username": "testuser", "password": "testpass"}
   ```
   
3. **Get Cards:**
   ```
   GET https://localhost:8443/api/cards/
   Headers: Authorization: Bearer <token>
   ```

4. **Create Game:**
   ```
   POST https://localhost:8443/api/games/
   Headers: Authorization: Bearer <token>
   Body: {"player2_name": "opponent"}
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

2. **Use proper SSL certificates:**
   - Replace self-signed certificates with CA-signed certificates
   - Configure proper DNS and domains

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

**SSL Certificate errors:**
```bash
# Regenerate certificates
rm -rf nginx/ssl/*
./generate-ssl.sh
docker-compose restart api-gateway
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
curl -k https://localhost:8443/health

# Check individual services
curl -k https://localhost:8443/api/auth/health
curl -k https://localhost:8443/api/cards/health
curl -k https://localhost:8443/api/games/health
curl -k https://localhost:8443/api/leaderboard/health
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