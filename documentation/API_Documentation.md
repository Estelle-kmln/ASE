# 🎮 **Battle Card Game API Documentation**

## **Executive Summary**

This document provides comprehensive documentation for the Battle Card Game microservices architecture. The system implements a rock-paper-scissors card battle game with user authentication, card management, game logic, and leaderboards.

**Document Version**: 1.0  
**Date**: November 15, 2025  
**Team**: Advanced Software Engineering Project  

---

## **🏗️ System Architecture**

### **Service Overview**

The Battle Card Game consists of 5 microservices running on different ports:

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **🔐 Auth Service** | 5001 | User authentication and profile management | ✅ Active |
| **🃏 Card Service** | 5002 | Card collection and deck management | ✅ Active |
| **🎯 Game Service** | 5003 | Game logic and battle mechanics | ✅ Active |
| **🏆 Leaderboard Service** | 5004 | Rankings and statistics | ✅ Active |
| **🗄️ PostgreSQL Database** | 5432 | Data persistence | ✅ Active |

### **Technology Stack**
- **Backend**: Python Flask with Gunicorn
- **Database**: PostgreSQL 16
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker & Docker Compose
- **API Gateway**: Nginx (reverse proxy)

---

## **🔐 Authentication Service** (`localhost:5001`)

All API endpoints except health checks require authentication using Bearer tokens.

### **Health Check**
```http
GET /health
```
**Purpose**: Service health status monitoring  
**Authentication**: Not required  
**Example**:
```bash
curl http://localhost:5001/health
```
**Response**:
```json
{"status": "healthy", "service": "auth-service"}
```

### **User Registration**
```http
POST /api/auth/register
```
**Purpose**: Create a new user account  
**Authentication**: Not required  
**Request Body**:
```json
{
  "username": "string (min 3 chars)",
  "email": "string (valid email)",
  "password": "string (min 4 chars)"
}
```
**Example**:
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","email":"player1@example.com","password":"password123"}'
```
**Response**:
```json
{
  "message": "User registered successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "player1"
  }
}
```

### **User Login**
```http
POST /api/auth/login
```
**Purpose**: Authenticate existing user and receive JWT token  
**Authentication**: Not required  
**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```
**Example**:
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"player1","password":"password123"}'
```

### **Get User Profile**
```http
GET /api/auth/profile
```
**Purpose**: Retrieve current user's profile information  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5001/api/auth/profile
```

### **Update User Profile**
```http
PUT /api/auth/profile
```
**Purpose**: Update user profile details  
**Authentication**: Bearer token required

### **Token Validation**
```http
POST /api/auth/validate
```
**Purpose**: Validate JWT token (internal service use)  
**Authentication**: Bearer token required

---

## **🃏 Card Service** (`localhost:5002`)

Manages the card collection and deck operations for the battle card game.

### **Health Check**
```http
GET /health
```
**Purpose**: Service health status  
**Authentication**: Not required

### **Get All Cards**
```http
GET /api/cards
```
**Purpose**: Retrieve all 39 cards in the game (13 Rock, 13 Paper, 13 Scissors)  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/cards
```
**Response**:
```json
{
  "cards": [
    {"id": 1, "type": "Rock", "power": 1},
    {"id": 2, "type": "Rock", "power": 2},
    ...
  ]
}
```

### **Get Cards by Type**
```http
GET /api/cards/by-type/<type>
```
**Purpose**: Filter cards by type (rock, paper, or scissors)  
**Authentication**: Bearer token required  
**Parameters**: `<type>` must be "rock", "paper", or "scissors"  
**Examples**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/cards/by-type/rock

curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/cards/by-type/paper

curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/cards/by-type/scissors
```

### **Get Specific Card**
```http
GET /api/cards/<card_id>
```
**Purpose**: Retrieve details of a specific card by ID  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/cards/1
```

### **Get Available Card Types**
```http
GET /api/cards/types
```
**Purpose**: Get list of all available card types  
**Authentication**: Bearer token required

### **Create Random Deck**
```http
POST /api/cards/random-deck
```
**Purpose**: Generate a random deck of cards for gameplay  
**Authentication**: Bearer token required  
**Request Body** (optional):
```json
{
  "size": 22
}
```
**Example**:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"size":22}' \
  http://localhost:5002/api/cards/random-deck
```
**Response**:
```json
{
  "deck": [
    {"id": 5, "type": "Rock", "power": 5},
    {"id": 12, "type": "Paper", "power": 12},
    ...
  ],
  "size": 22
}
```

### **Get Card Statistics**
```http
GET /api/cards/statistics
```
**Purpose**: Retrieve database statistics and card distribution  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5002/api/cards/statistics
```

---

## **🎯 Game Service** (`localhost:5003`)

Handles all game logic, battle mechanics, and game state management.

### **Health Check**
```http
GET /health
```
**Purpose**: Service health status  
**Authentication**: Not required

### **Create New Game**
```http
POST /api/games
```
**Purpose**: Initialize a new game between two players  
**Authentication**: Bearer token required  
**Request Body**:
```json
{
  "player2_name": "string"
}
```
**Example**:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player2_name":"opponent"}' \
  http://localhost:5003/api/games
```
**Response**:
```json
{
  "game_id": "uuid-string",
  "player1_name": "authenticated_user",
  "player2_name": "opponent",
  "status": "created",
  "turn": 1,
  "current_player": 1
}
```

### **Get Game State**
```http
GET /api/games/<game_id>
```
**Purpose**: Retrieve current game state and player information  
**Authentication**: Bearer token required (must be a player in the game)  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5003/api/games/GAME_ID
```
**Response**:
```json
{
  "game_id": "uuid-string",
  "turn": 1,
  "is_active": true,
  "current_player": 1,
  "player1": {
    "name": "player1",
    "deck_size": 22,
    "hand_size": 0,
    "score": 0
  },
  "player2": {
    "name": "player2", 
    "deck_size": 22,
    "hand_size": 0,
    "score": 0
  },
  "winner": null
}
```

### **Get Player's Hand**
```http
GET /api/games/<game_id>/hand
```
**Purpose**: View current player's cards in hand  
**Authentication**: Bearer token required

### **Draw Cards to Hand**
```http
POST /api/games/<game_id>/draw-hand
```
**Purpose**: Draw 3 cards from deck to hand (only if hand is empty)  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5003/api/games/GAME_ID/draw-hand
```

### **Play a Card**
```http
POST /api/games/<game_id>/play-card
```
**Purpose**: Play a card from hand (remaining cards are discarded)  
**Authentication**: Bearer token required  
**Request Body**:
```json
{
  "card_id": 1
}
```
**Example**:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"card_id":1}' \
  http://localhost:5003/api/games/GAME_ID/play-card
```

### **Resolve Round**
```http
POST /api/games/<game_id>/resolve-round
```
**Purpose**: Calculate battle result based on rock-paper-scissors rules  
**Authentication**: Bearer token required  
**Game Rules**:
- Rock beats Scissors
- Scissors beats Paper  
- Paper beats Rock
- Same type: Higher power wins (except 1 beats 13)
**Example**:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5003/api/games/GAME_ID/resolve-round
```

### **End Game**
```http
POST /api/games/<game_id>/end
```
**Purpose**: Force end the current game  
**Authentication**: Bearer token required

### **Get User's Games**
```http
GET /api/games/user/<username>
```
**Purpose**: Retrieve all games for a specific user  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5003/api/games/user/player1
```

---

## **🏆 Leaderboard Service** (`localhost:5004`)

Provides rankings, statistics, and game history analysis.

### **Health Check**
```http
GET /health
```
**Purpose**: Service health status  
**Authentication**: Not required

### **Global Leaderboard**
```http
GET /api/leaderboard?limit=10
```
**Purpose**: Get top players ranked by wins  
**Authentication**: Bearer token required  
**Query Parameters**:
- `limit` (optional): Number of players to return (max 100, default 10)
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5004/api/leaderboard

curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:5004/api/leaderboard?limit=20"
```
**Response**:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "player": "player1",
      "wins": 15,
      "games": 20,
      "losses": 5,
      "win_percentage": 75.0
    },
    ...
  ],
  "total_players": 10
}
```

### **Player Statistics**
```http
GET /api/leaderboard/player/<player_name>
```
**Purpose**: Get detailed statistics for a specific player  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5004/api/leaderboard/player/player1
```

### **Recent Games**
```http
GET /api/leaderboard/recent-games?limit=10
```
**Purpose**: Get recently completed games  
**Authentication**: Bearer token required  
**Query Parameters**:
- `limit` (optional): Number of games to return (max 50, default 10)
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5004/api/leaderboard/recent-games
```

### **Top Players**
```http
GET /api/leaderboard/top-players
```
**Purpose**: Get top performers with advanced metrics  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5004/api/leaderboard/top-players
```

### **Game Statistics**
```http
GET /api/leaderboard/statistics
```
**Purpose**: Get overall game statistics and platform metrics  
**Authentication**: Bearer token required  
**Example**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5004/api/leaderboard/statistics
```

---

## **🎮 Complete Game Flow Example**

### **Step-by-Step Gameplay**

#### **1. User Registration and Authentication**
```bash
# Register Player 1
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"password123"}'

# Register Player 2  
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","email":"bob@example.com","password":"password123"}'

# Login as Alice and save token
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | jq -r '.access_token')
```

#### **2. Game Creation and Setup**
```bash
# Create a new game
GAME_ID=$(curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player2_name":"bob"}' \
  http://localhost:5003/api/games | jq -r '.game_id')

# Check game state
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5003/api/games/$GAME_ID
```

#### **3. Gameplay Actions**
```bash
# Draw cards to hand (3 cards)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:5003/api/games/$GAME_ID/draw-hand

# View current hand
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5003/api/games/$GAME_ID/hand

# Play a card (others discarded automatically)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"card_id":1}' \
  http://localhost:5003/api/games/$GAME_ID/play-card

# Resolve the round (determine winner)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:5003/api/games/$GAME_ID/resolve-round
```

#### **4. Statistics and Leaderboards**
```bash
# Check leaderboard
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5004/api/leaderboard

# View player statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5004/api/leaderboard/player/alice

# Check recent games
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5004/api/leaderboard/recent-games
```

---

## **⚡ Quick Testing Commands**

### **Health Check All Services**
```bash
curl http://localhost:5001/health  # Auth Service
curl http://localhost:5002/health  # Card Service  
curl http://localhost:5003/health  # Game Service
curl http://localhost:5004/health  # Leaderboard Service
```

### **Create Test User and Explore**
```bash
# Create test user
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Login and get token
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# View all cards (use token from login response)
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:5002/api/cards

# Get card statistics
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:5002/api/cards/statistics
```

---

## **🔧 System Status & Deployment**

### **Current Service Status**
All services are operational and healthy:
- ✅ **Auth Service**: Running on port 5001
- ✅ **Card Service**: Running on port 5002  
- ✅ **Game Service**: Running on port 5003
- ✅ **Leaderboard Service**: Running on port 5004
- ✅ **Database**: PostgreSQL initialized with 39 cards

### **Database Schema**
The system uses the following main tables:
- **users**: User accounts and authentication
- **cards**: Card collection (39 total: Rock, Paper, Scissors × 13 power levels each)
- **games**: Game state and player information
- **game_history**: Completed games for leaderboard calculations

### **Deployment Instructions**
```bash
# Start all services
docker compose up -d --build

# Stop all services  
docker compose down

# View logs
docker compose logs [service-name]

# Check status
docker compose ps
```

---

## **🛠️ Development Notes**

### **Authentication Flow**
1. User registers/logs in via Auth Service
2. Receives JWT token with 24-hour expiration
3. Token must be included in `Authorization: Bearer <token>` header for all protected endpoints
4. Other services validate tokens via Auth Service `/api/auth/validate` endpoint

### **Game Rules**
- Each player starts with 22 randomly selected cards
- Players draw 3 cards to hand each turn
- Players select 1 card to play, other 2 are discarded
- Battle resolution follows rock-paper-scissors rules:
  - Rock > Scissors
  - Scissors > Paper  
  - Paper > Rock
  - Same type: Higher power wins (special: 1 beats 13)
- Game continues until a player cannot draw 3 cards
- Winner is determined by most rounds won

### **Error Handling**
All services return consistent error responses:
```json
{
  "error": "Descriptive error message"
}
```
HTTP status codes follow REST conventions (200, 400, 401, 403, 404, 500).

---

## **📞 Support & Contact**

For technical issues or questions about this API documentation, please contact the development team.

**Project**: Advanced Software Engineering - Battle Card Game  
**Version**: 1.0  
**Last Updated**: November 15, 2025

---

*This documentation covers all available endpoints and functionality of the Battle Card Game microservices architecture. The system is fully operational and ready for team testing and demonstration.*