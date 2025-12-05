# Strict Game Logic Implementation

## Summary of Changes

This update implements **strict game rules** where each player can only draw cards **once** per turn and play **one card** per turn. The 2 unplayed cards are permanently discarded from the game.

---

## Backend Changes

### 1. Database Schema (`microservices/database/03-add-turn-state-tracking.sql`)

Added 4 new columns to the `games` table:
- `player1_has_drawn` (BOOLEAN) - Tracks if player 1 has drawn cards this turn
- `player2_has_drawn` (BOOLEAN) - Tracks if player 2 has drawn cards this turn
- `player1_has_played` (BOOLEAN) - Tracks if player 1 has played a card this turn
- `player2_has_played` (BOOLEAN) - Tracks if player 2 has played a card this turn

### 2. Game Service (`microservices/game-service/app.py`)

#### **Modified `draw_hand` endpoint:**
- ✅ Checks if player has already drawn cards this turn
- ✅ Returns error: "You have already drawn cards this turn" if attempting to draw twice
- ✅ Sets `player_has_drawn = TRUE` after drawing
- ✅ Still draws 3 cards normally (or remaining cards for tie-breaker)

#### **Modified `play_card` endpoint:**
- ✅ Checks if player has drawn cards first
- ✅ Returns error: "You must draw cards before playing" if not drawn
- ✅ Checks if player has already played this turn
- ✅ Returns error: "You have already played a card this turn" if already played
- ✅ **Discards the 2 remaining cards** - they are permanently removed
- ✅ Sets `player_has_played = TRUE` after playing
- ✅ Clears hand to empty array `[]`

#### **Modified `auto_resolve_round` function:**
- ✅ Resets all 4 flags to `FALSE` after round resolves
- ✅ Clears played cards and hands
- ✅ Increments turn counter
- ✅ Both players can now draw and play again

#### **Modified `get_game` endpoint:**
- ✅ Returns `has_drawn` and `has_played` flags for both players
- ✅ Frontend can check these flags to show correct UI state

---

## Frontend Changes

### 3. Game Interface (`frontend/js/game.js`)

#### **Modified `updateGameDisplay` function:**
Complete rewrite to enforce strict logic:

```javascript
// STRICT GAME LOGIC:
// 1. If I haven't drawn -> show draw button
// 2. If I've drawn but not played -> show hand and play button
// 3. If I've played -> show "waiting for opponent" message
// 4. When both have played -> round auto-resolves and flags reset
```

**State-based UI rendering:**
- **Not drawn yet**: Shows "Draw Cards" button, hides hand
- **Drawn, not played**: Shows hand with 3 cards, enables "Play Card" button
- **Played, waiting**: Hides everything, shows "Waiting for opponent to play..."
- **Both played**: Shows "Round resolving...", then refreshes to next turn

#### **Modified `playSelectedCard` function:**
- ✅ Only sends `card_index` (not full card object)
- ✅ Clears hand immediately after playing (2 cards discarded)
- ✅ Shows "Card played! Waiting for opponent..." message
- ✅ Displays round result notification when both players have played

#### **Added `showRoundResult` function:**
- ✅ Shows temporary notification with round winner
- ✅ Displays "Round tied!" for perfect ties
- ✅ Auto-refreshes game state after 3 seconds

#### **Removed old functions:**
- ❌ Deleted `updateTurnIndicator()` - replaced with state-based logic in `updateGameDisplay()`

---

## Game Flow

### Complete Turn Sequence:

1. **Player 1 draws cards** → Gets 3 cards, `player1_has_drawn = TRUE`
2. **Player 2 can draw immediately** (doesn't have to wait) → Gets 3 cards, `player2_has_drawn = TRUE`
3. **Player 1 selects and plays 1 card** → 2 other cards discarded, `player1_has_played = TRUE`
4. **Player 2 selects and plays 1 card** → 2 other cards discarded, `player2_has_played = TRUE`
5. **Round auto-resolves:**
   - Winner determined (Rock > Scissors > Paper > Rock)
   - Same type: higher power wins
   - Same type + power: tie (no points)
   - Scores updated
   - All flags reset to `FALSE`
   - Turn incremented
6. **Repeat from step 1** until a player cannot draw 3 cards

### Key Rules Enforced:

✅ **One draw per turn** - Cannot draw twice in same turn  
✅ **One play per turn** - Cannot play twice in same turn  
✅ **Must draw before playing** - Cannot play without drawing first  
✅ **2 cards always discarded** - The unplayed cards are removed permanently  
✅ **Both players can act independently** - Player 2 doesn't wait for Player 1 to draw  
✅ **Round resolves when both have played** - Automatic resolution, no manual trigger  

---

## Testing the Changes

### Start the services:
```bash
cd microservices
docker compose down -v
docker compose up -d --build
```

### Test scenario:
1. Open game in two browsers (Bob and Alex)
2. **Bob clicks "Draw Cards"** → Should see 3 cards
3. **Alex clicks "Draw Cards"** → Should see 3 cards
4. **Bob tries to click "Draw Cards" again** → Should see error
5. **Bob selects and plays a card** → Hand disappears, "Waiting for opponent..."
6. **Alex selects and plays a card** → Round resolves, scores update
7. **Both players see "Draw Cards" button again** → Next turn begins

---

## Error Messages

| Scenario | Error Message |
|----------|--------------|
| Drawing twice in one turn | "You have already drawn cards this turn. Wait for both players to play." |
| Playing without drawing | "You must draw cards before playing" |
| Playing twice in one turn | "You have already played a card this turn. Wait for the round to resolve." |
| Invalid card index | "Invalid card index" |
| No cards in deck | "No cards left in deck" |

---

## Files Modified

### Backend:
- ✅ `microservices/database/03-add-turn-state-tracking.sql` (NEW)
- ✅ `microservices/game-service/app.py` (MODIFIED)

### Frontend:
- ✅ `frontend/js/game.js` (MODIFIED)

---

## Deployment Notes

⚠️ **Important**: This update requires a database schema change. You must:
1. Stop all services: `docker compose down -v`
2. Rebuild with clean volumes: `docker compose up -d --build`

The `-v` flag removes old database volumes, ensuring the new schema is applied.

---

## Backward Compatibility

❌ **This is a breaking change**. Old game sessions will not work with the new logic. All existing games should be completed before deploying this update.

---

**Implementation Date**: December 2, 2025  
**Status**: ✅ Complete and deployed
