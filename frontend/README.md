# Battlecards Frontend

A modern, responsive web application for the Battlecards game - a strategic Rock, Paper, Scissors card game with power values.

## Features

### 🔐 Authentication & Security
- **Login/Register Page** - Secure user authentication with JWT tokens
- **Automatic Token Refresh** - Seamless session management with refresh tokens
- **Account Lockout Protection** - 3 failed login attempts = 15-minute lockout
- **Concurrent Session Control** - One active session per user (strict mode)
- **Session Management** - View and revoke active sessions from any device
- Users must be authenticated to access the game

### 🏠 Homepage
- **Two large game buttons:**
  - 🚀 **LAUNCH A GAME!** - Creates a game and sends invitation to another player
  - 🎮 **JOIN A GAME!** - Join an existing game using a game code
- **Game Invitations** - Accept, decline, or cancel game invitations
- **Header with dropdown menu** showing:
  - Current user
  - Profile
  - Leaderboard
  - Game Statistics
  - Game Rules
  - Admin Panel (admin users only)
  - Logout option

### 🎴 Deck Selection
- **Manual Selection** - Choose the number of Rock, Paper, and Scissors cards (total: 22 cards)
- **Random Deck** - Automatically generate a random deck
- Powers are randomly distributed among cards (1-10)
- Both players must confirm decks before game starts

### 🎮 Game Page
- **Real-time gameplay** with card selection
- **Visual card display** with emojis (🪨 📄 ✂️) and power values
- **Score tracking** for both players
- **Turn indicator** showing whose turn it is
- **⏱️ Live Countdown Timer** - Real-time timer displayed on game page
- **Hand management** - Select and play cards from your hand
- **Opponent card reveal** - See what your opponent played
- **Battle resolution** - Automatic round resolution with visual feedback

### 🏆 Game Over
- **Victory/Defeat popup** with:
  - 👑 Golden crown for victory
  - 💀 Grey skull for defeat
  - Final score display
  - Return to homepage button

### 👤 Profile Page
- **View mode** - Display username, email
- **Edit mode** - Modify username, email, and password
- Toggle between view and edit modes
- Save changes with validation

### 📊 Leaderboard
- **Paginated game history** (10 games per page)
- Displays:
  - Date of match
  - Opponent name
  - Your score
  - Opponent's score
  - Result (Victory/Defeat)

### 📖 Additional Pages
- **Game Statistics** - Placeholder for future statistics features
- **Game Rules** - Complete game instructions and tips
- **Admin Panel** (admin users only):
  - View all user action logs
  - Search and filter logs by user, action type, or date
  - Monitor security events (failed logins, unauthorized access)
  - Track game events (created, started, completed, abandoned)

## File Structure

```
frontend/
├── css/
│   └── styles.css           # All styles with beautiful gradients
├── js/
│   ├── auth.js             # Login/Register logic
│   ├── home.js             # Homepage and game creation/joining
│   ├── deck-selection.js   # Deck building logic
│   ├── game.js             # Main game logic and card playing
│   ├── profile.js          # Profile viewing and editing
│   └── game-history.js      # Game history with pagination
├── index.html              # Homepage
├── login.html              # Login/Register page
├── deck-selection.html     # Deck selection page
├── game.html               # Game page
├── profile.html            # Profile page
├── game-history.html        # Leaderboard page
├── statistics.html         # Statistics placeholder
└── rules.html              # Game rules page
```

## Design Features

- **Modern gradient backgrounds** - Purple to blue gradient theme
- **Smooth animations** - Hover effects and transitions
- **Responsive design** - Works on desktop and mobile
- **Card emojis** - Visual representation (🪨 Rock, 📄 Paper, ✂️ Scissors)
- **Real-time updates** - Polling for game state changes
- **Clean UI** - Professional and intuitive interface

## API Integration

The frontend connects to microservices through the Nginx gateway with HTTPS on port 8443:

- **Auth Service**: `/api/auth/` - User authentication, profiles, sessions, and token refresh
- **Card Service**: `/api/cards/` - Card database and deck generation
- **Game Service**: `/api/games/` - Game creation, invitations, joining, deck selection, and gameplay
- **Leaderboard Service**: `/api/leaderboard/` - Match history and player statistics
- **Logs Service**: `/api/logs/` - User action logging and audit trails (admin only)

**Base URL**: `https://localhost:8443`

## Running the Application

1. Make sure Docker services are running:
   ```bash
   cd microservices
   ./build-and-start.sh
   # Or manually: docker compose up -d --build
   ```

2. Access the application:
   - **Frontend (HTTPS)**: https://localhost:8443
   - **Frontend (HTTP)**: http://localhost:8080 (redirects to HTTPS)
   - **Default page**: Login page (`login.html`)
   - **Note**: Browser will show security warning for self-signed certificate - click "Advanced" and "Proceed to localhost"

3. First-time users:
   - Click "Register here" on the login page
   - Create an account with strong password
   - Login with your credentials
   - Note: Account locks after 3 failed login attempts for 15 minutes

## Game Flow

1. **Login** → Authenticate to access the game (automatic token refresh)
2. **Homepage** → Choose to launch or join a game
3. **Game Invitation** → Accept/decline invitation or wait for opponent to join
4. **Deck Selection** → Build your deck of 22 cards (manual or random)
5. **Wait for Opponent** → Both players must confirm their decks
6. **Game Starts** → Take turns playing cards with countdown timer
7. **Game Over** → View results, see final scores, and return to homepage
8. **View History** → Check game history in leaderboard

## Technical Details

- **Pure JavaScript** - No frameworks, just vanilla JS
- **RESTful API** - Communication with backend microservices via HTTPS
- **JWT Authentication** - Secure token-based auth with automatic refresh
- **LocalStorage** - Client-side token and user data storage
- **TokenManagement Module** - Automatic token refresh and authenticated fetch wrapper
- **Polling** - Regular checks for game updates and timer synchronization
- **CORS Enabled** - Cross-origin requests supported
- **HTTPS/TLS** - Encrypted communication with self-signed certificates for development

## Navigation

- **Back Button** - Upper left on all pages (except homepage)
- **Menu Button** - Upper right on homepage
- **Automatic Redirects** - Login required for protected pages
- **Session Management** - Token-based authentication

## Responsive Features

- Mobile-friendly layout
- Touch-friendly buttons
- Adaptive card sizing
- Flexible grid layouts

## Future Enhancements (Placeholders)

- Game statistics with charts
- Win/loss ratios
- Card usage analytics
- Playing streaks
- Advanced filtering on leaderboard
