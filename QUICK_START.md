# 🎮 Battlecards - Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- PowerShell (Windows) or Bash (Linux/Mac)

## Starting the Application

### 1. Navigate to the microservices directory
```powershell
cd "C:\Users\estel\OneDrive\Advanced software engineering\project\ASE\microservices"
```

### 2. Start all services
```powershell
docker compose up -d --build
```

This will start:
- PostgreSQL database
- Auth Service (port 5001)
- Card Service (port 5002)
- Game Service (port 5003)
- Leaderboard Service (port 5004)
- Nginx Gateway (port 8080) + Frontend

### 3. Wait for services to be ready
```powershell
docker compose ps
```

All services should show "healthy" status.

### 4. Access the application
Open your browser and go to:
```
http://localhost:8080
```

You'll see the login page as the default entry point.

## First Time Setup

### Create an Account
1. Click "Register here" on the login page
2. Enter:
   - Username
   - Email
   - Password (confirm it)
3. Click "Register"
4. After successful registration, login with your credentials

## Playing the Game

### Launch a Game
1. From the homepage, click **"🚀 LAUNCH A GAME!"**
2. A game code will be displayed (e.g., "ABC123")
3. Share this code with a friend
4. Wait for them to join

### Join a Game
1. From the homepage, click **"🎮 JOIN A GAME!"**
2. Enter the game code you received
3. Click "Join Game"

### Build Your Deck
1. Choose **Manual Selection** or **Random Deck**
2. For manual:
   - Click +/- to add/remove Rock 🪨, Paper 📄, or Scissors ✂️
   - Total must equal 10 cards
3. Click "Confirm Deck & Start Game"
4. Wait for your opponent to also select their deck

### Play the Game
1. Select a card from your hand by clicking it
2. Click "Play Card" button
3. Wait for your opponent to play
4. Both cards are revealed with the winner determined by:
   - Rock beats Scissors
   - Scissors beats Paper
   - Paper beats Rock
   - Same type: Higher power wins!
5. Continue until all cards are played
6. View the Victory/Defeat popup with final scores

## Navigation

### Homepage Menu (☰)
Click the menu button in the top-right to access:
- **Profile** - View/edit your account
- **Leaderboard** - View your game history
- **Game Statistics** - Coming soon!
- **Game Rules** - Learn how to play
- **Logout** - Sign out

### Back Button (←)
Every page except the homepage has a back button in the top-left corner.

## Troubleshooting

### Can't access the application?
```powershell
# Check if services are running
docker compose ps

# View logs
docker compose logs api-gateway
docker compose logs auth-service
```

### Services not healthy?
```powershell
# Restart services
docker compose restart

# Or rebuild
docker compose down
docker compose up -d --build
```

### Database issues?
```powershell
# Reset everything (WARNING: Deletes all data!)
docker compose down -v
docker compose up -d --build
```

### CORS errors in browser?
- Clear browser cache
- Try incognito/private mode
- Check browser console for specific errors

## Stopping the Application

```powershell
# Stop all services
docker compose down

# Stop and remove volumes (deletes all data)
docker compose down -v
```

## Development Tips

### View Service Logs
```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f auth-service
docker compose logs -f game-service
docker compose logs -f api-gateway
```

### Restart a Single Service
```powershell
docker compose restart auth-service
```

### Rebuild Frontend Changes
```powershell
# Frontend files are mounted as volume, so changes appear immediately
# Just refresh your browser!

# If CSS/JS changes don't appear, force refresh:
# - Windows: Ctrl + F5
# - Mac: Cmd + Shift + R
```

## API Endpoints

Access backend APIs directly (for testing):

### Auth Service
- POST `http://localhost:8080/api/auth/register`
- POST `http://localhost:8080/api/auth/login`
- GET `http://localhost:8080/api/auth/profile`
- PUT `http://localhost:8080/api/auth/profile`

### Game Service
- POST `http://localhost:8080/api/game/create`
- POST `http://localhost:8080/api/game/{game_id}/join`
- POST `http://localhost:8080/api/game/{game_id}/select-deck`
- GET `http://localhost:8080/api/game/{game_id}/state`
- POST `http://localhost:8080/api/game/{game_id}/play-card`

### Leaderboard Service
- GET `http://localhost:8080/api/leaderboard/my-matches`

## Architecture

```
Browser (localhost:8080)
    ↓
Nginx Gateway (Container)
    ↓
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Auth        │ Card        │ Game        │ Leaderboard │
│ Service     │ Service     │ Service     │ Service     │
│ :5001       │ :5002       │ :5003       │ :5004       │
└─────────────┴─────────────┴─────────────┴─────────────┘
                        ↓
                  PostgreSQL
                   (Container)
```

## Tech Stack

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- No frameworks/libraries
- Responsive design

### Backend
- Python Flask microservices
- PostgreSQL database
- JWT authentication
- Nginx reverse proxy

### Deployment
- Docker & Docker Compose
- Microservices architecture

## Support

For issues or questions:
1. Check the logs: `docker compose logs -f`
2. Verify services are healthy: `docker compose ps`
3. Review the README files in `/frontend` and `/microservices`

## Game Rules Summary

- Each player builds a 10-card deck
- Cards: Rock 🪨, Paper 📄, Scissors ✂️
- Each card has a random power value
- Rock beats Scissors, Scissors beats Paper, Paper beats Rock
- Same type: Higher power wins
- Winner of each round earns points
- Most points after 10 rounds wins!

Enjoy playing Battlecards! 🎮👑
