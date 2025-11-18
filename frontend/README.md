# Battlecards Frontend

A modern, responsive web application for the Battlecards game - a strategic Rock, Paper, Scissors card game with power values.

## Features

### 🔐 Authentication
- **Login/Register Page** - Secure user authentication
- Users must be authenticated to access the game

### 🏠 Homepage
- **Two large game buttons:**
  - 🚀 **LAUNCH A GAME!** - Creates a game with a shareable code
  - 🎮 **JOIN A GAME!** - Join an existing game using a code
- **Header with dropdown menu** showing:
  - Current user
  - Profile
  - Leaderboard
  - Game Statistics
  - Game Rules
  - Logout option

### 🎴 Deck Selection
- **Manual Selection** - Choose the number of Rock, Paper, and Scissors cards (total: 10 cards)
- **Random Deck** - Automatically generate a random deck
- Powers are randomly distributed among cards

### 🎮 Game Page
- **Real-time gameplay** with card selection
- **Visual card display** with emojis (🪨 📄 ✂️) and power values
- **Score tracking** for both players
- **Turn indicator** showing whose turn it is
- **Hand management** - Select and play cards from your hand
- **Opponent card reveal** - See what your opponent played

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
│   └── leaderboard.js      # Game history with pagination
├── index.html              # Homepage
├── login.html              # Login/Register page
├── deck-selection.html     # Deck selection page
├── game.html               # Game page
├── profile.html            # Profile page
├── leaderboard.html        # Leaderboard page
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

The frontend connects to microservices through the Nginx gateway on port 8080:

- **Auth Service**: `/api/auth/` - User authentication and profiles
- **Game Service**: `/api/game/` - Game creation, joining, and gameplay
- **Leaderboard Service**: `/api/leaderboard/` - Match history

## Running the Application

1. Make sure Docker services are running:
   ```bash
   cd microservices
   docker compose up -d
   ```

2. Access the application:
   - **Frontend**: http://localhost:8080
   - **Default page**: Login page (`login.html`)

3. First-time users:
   - Click "Register here" on the login page
   - Create an account
   - Login with your credentials

## Game Flow

1. **Login** → Authenticate to access the game
2. **Homepage** → Choose to launch or join a game
3. **Deck Selection** → Build your deck (manual or random)
4. **Wait for Opponent** → Both players must select decks
5. **Game Starts** → Take turns playing cards
6. **Game Over** → View results and return to homepage

## Technical Details

- **Pure JavaScript** - No frameworks, just vanilla JS
- **RESTful API** - Communication with backend microservices
- **JWT Authentication** - Secure token-based auth
- **LocalStorage** - Client-side token and user data storage
- **Polling** - Regular checks for game updates
- **CORS Enabled** - Cross-origin requests supported

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
