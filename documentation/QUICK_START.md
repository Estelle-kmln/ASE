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
https://localhost:8443
```

**Important**: Your browser will show a security warning because the application uses a self-signed SSL certificate for development. This is normal.
- Click "Advanced" or "Show Details"
- Click "Proceed to localhost" or "Accept Risk and Continue"

You'll see the login page as the default entry point.

**Note**: HTTP requests to `http://localhost:8080` will automatically redirect to HTTPS on port 8443.

## First Time Setup

### Create an Account
1. Click "Register here" on the login page
2. Enter:
   - Username
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
   - Total must equal 22 cards
   - Powers (1-10) are randomly assigned
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
- **Profile** - View/edit your account details and manage sessions
- **Leaderboard** - View your game history and rankings
- **Game Statistics** - Coming soon!
- **Game Rules** - Learn how to play
- **Admin Panel** - View logs and monitor system (admin only)
- **Logout** - Sign out (invalidates current session)

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

Access backend APIs directly (for testing). Use `-k` flag with curl for self-signed certificates:

### Auth Service
- POST `https://localhost:8443/api/auth/register` - Create new account
- POST `https://localhost:8443/api/auth/login` - Login (returns access_token & refresh_token)
- POST `https://localhost:8443/api/auth/refresh` - Refresh access token
- GET `https://localhost:8443/api/auth/profile` - View profile
- PUT `https://localhost:8443/api/auth/profile` - Update profile
- GET `https://localhost:8443/api/auth/sessions` - View active sessions
- DELETE `https://localhost:8443/api/auth/sessions/{id}` - Logout specific device
- POST `https://localhost:8443/api/auth/sessions/revoke-all` - Logout all devices

### Game Service
- POST `https://localhost:8443/api/games/` - Create game with invitation
- POST `https://localhost:8443/api/games/{game_id}/accept-invitation` - Accept invitation
- POST `https://localhost:8443/api/games/{game_id}/decline-invitation` - Decline invitation
- POST `https://localhost:8443/api/games/{game_id}/select-deck` - Select deck
- GET `https://localhost:8443/api/games/{game_id}` - Get game state
- POST `https://localhost:8443/api/games/{game_id}/play-card` - Play a card
- GET `https://localhost:8443/api/games/pending-invitations` - View pending invitations

### Leaderboard Service
- GET `https://localhost:8443/api/leaderboard/` - Global leaderboard
- GET `https://localhost:8443/api/leaderboard/player/{name}` - Player stats

### Logs Service (Admin Only)
- GET `https://localhost:8443/api/logs/list` - View all logs
- GET `https://localhost:8443/api/logs/user/{username}` - User-specific logs

## Architecture

```
Browser (https://localhost:8443)
    ↓
Nginx Gateway (HTTPS/TLS - Container)
    ↓
┌──────────┬──────────┬──────────┬────────────┬──────────┐
│ Auth     │ Card     │ Game     │ Leaderboard│ Logs     │
│ Service  │ Service  │ Service  │ Service    │ Service  │
│ :5001    │ :5002    │ :5003    │ :5004      │ :5005    │
└──────────┴──────────┴──────────┴────────────┴──────────┘
                        ↓
                  PostgreSQL
                   (Container)
```

**Security Features:**
- HTTPS/TLS encryption
- JWT with automatic refresh tokens
- Concurrent session control (one per user)
- Account lockout (3 failed attempts)
- Comprehensive action logging

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

- Each player builds a 22-card deck (manual or random)
- Cards: Rock 🪨, Paper 📄, Scissors ✂️
- Each card has a power value (1-10)
- Rock beats Scissors, Scissors beats Paper, Paper beats Rock
- Same type: Higher power wins
- Winner of each round earns points equal to their card's power
- Most points after all cards are played wins!
- Game includes live countdown timer
- All actions are logged for security

Enjoy playing Battlecards! 🎮👑
