# Deck Selection Feature

## Overview

The deck selection feature allows players to customize their decks before starting a game. Instead of being assigned random decks automatically, players can now choose which types of cards they want in their deck.

## How It Works

### 1. Game Creation
When a player creates a game, it now starts in the `deck_selection` status with empty decks for both players.

```bash
POST /api/games
{
  "player2_name": "opponent_username"
}
```

Response:
```json
{
  "game_id": "uuid",
  "player1_name": "creator",
  "player2_name": "opponent",
  "status": "deck_selection",
  "turn": 1
}
```

### 2. Deck Selection Phase

Both players must select their decks before the game can begin. Each player has two options:

#### Option A: Manual Selection
- Choose exactly **22 cards**
- Specify how many of each type (Rock, Paper, Scissors)
- Powers are randomly assigned from the card database

Example:
```json
{
  "deck": [
    {"type": "Rock"},
    {"type": "Rock"},
    {"type": "Rock"},
    {"type": "Rock"},
    {"type": "Paper"},
    {"type": "Paper"},
    {"type": "Paper"},
    {"type": "Scissors"},
    {"type": "Scissors"},
    {"type": "Scissors"}
  ]
}
```

#### Option B: Random Deck
- Frontend generates a random mix of card types
- Still 22 cards total
- Powers are randomly assigned

### 3. Selecting a Deck

```bash
POST /api/games/{game_id}/select-deck
Authorization: Bearer {token}
{
  "deck": [
    {"type": "Rock"},
    {"type": "Paper"},
    ...
  ]
}
```

Response:
```json
{
  "message": "Deck selected successfully",
  "deck": [
    {"id": 1, "type": "Rock", "power": 5},
    {"id": 14, "type": "Paper", "power": 3},
    ...
  ],
  "both_selected": false,
  "status": "deck_selection"
}
```

### 4. Checking Status

Players can check if both have selected their decks:

```bash
GET /api/games/{game_id}/status
Authorization: Bearer {token}
```

Response:
```json
{
  "status": "deck_selection",  // or "in_progress" when both selected
  "player1_deck_selected": true,
  "player2_deck_selected": false,
  "game_id": "uuid"
}
```

### 5. Game Start

Once **both players** have selected their decks, the game automatically transitions to `active` status and gameplay can begin as normal.

## Frontend Implementation

The frontend (`deck-selection.html` and `deck-selection.js`) provides:
- Manual selection interface with +/- buttons for each card type
- Random deck generation option
- Real-time deck count display
- Polling to detect when opponent has selected their deck
- Automatic redirect to game page when both players are ready

## API Endpoints

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/games/{game_id}/select-deck` | Select deck for the game |
| GET | `/api/games/{game_id}/status` | Check game status and deck selection progress |

### Modified Endpoints

| Method | Path | Change |
|--------|------|--------|
| POST | `/api/games` | Now creates games in `deck_selection` status with empty decks |

## Database Schema

New columns added to `games` table:
- `player1_deck_selected` (BOOLEAN): Whether player 1 has selected their deck
- `player2_deck_selected` (BOOLEAN): Whether player 2 has selected their deck

New game status value:
- `deck_selection`: Game is waiting for players to select their decks

## Validation Rules

1. **Deck size**: Must be exactly 22 cards
2. **Card types**: Only "Rock", "Paper", or "Scissors" allowed
3. **One-time selection**: Players cannot change their deck once selected
4. **Game status**: Can only select deck when game is in `deck_selection` status
5. **Authorization**: Only players in the game can select decks

## Testing

Run the deck selection tests:

```bash
python tests/test_deck_selection.py
```

This test suite covers:
- Complete deck selection flow
- Manual deck selection
- Random deck selection
- Status polling
- Input validation
- Duplicate selection prevention
- Game state transitions

## Migration

To apply the database migration:

```bash
docker compose down -v
docker compose up -d --build
```

The migration script (`04-add-deck-selection-tracking.sql`) will:
1. Add deck selection tracking columns
2. Update the game_status CHECK constraint
3. Create indexes for performance

## Backward Compatibility

This is a **breaking change** for the game creation flow. All new games now require deck selection. Existing games in the database will have `player1_deck_selected` and `player2_deck_selected` set to `false` by default.

If you need to support old-style automatic deck assignment, you could:
1. Keep the old behavior for games created via a different endpoint
2. Add a query parameter to `/api/games` to opt into automatic deck assignment
3. Create a migration script to mark existing games as having decks selected

## Frontend Usage Flow

1. User clicks "New Game" and enters opponent name
2. Game is created with `deck_selection` status
3. User is redirected to `deck-selection.html?game_id={uuid}`
4. User chooses manual or random deck selection
5. User confirms deck (22 cards)
6. Frontend polls `/api/games/{game_id}/status` every 2 seconds
7. When both players have selected decks, status becomes `in_progress`
8. User is automatically redirected to `game.html?game_id={uuid}`
9. Game proceeds normally from there

## Example Deck Compositions

**Aggressive (Heavy Rock)**
- 12 Rock, 5 Paper, 5 Scissors
- Good against Scissors-heavy opponents

**Defensive (Balanced)**
- 8 Rock, 7 Paper, 7 Scissors
- Well-rounded for any opponent

**Paper Specialist**
- 5 Rock, 12 Paper, 5 Scissors
- Good against Rock-heavy opponents

**Random**
- Random distribution
- Unpredictable strategy
