# Game Invitation Management Update

## Overview
This update implements proper tracking of game invitations vs. actual games played, ensuring that ignored invitations don't appear in the leaderboard statistics.

## Problem
Previously, when a user ignored a game invitation, the system would call the `/end` endpoint which:
1. Set `is_active = false`
2. Archived the game in `game_history`
3. Counted the game in leaderboard statistics

This meant ignored invitations appeared as games that were played, which was incorrect and inflated statistics.

## Solution
Added a `game_status` column to track the complete lifecycle of games with five distinct states:

### Game Status Values
- **`pending`**: Invitation sent but not yet accepted by player2
- **`active`**: Game has been joined and is currently in progress
- **`completed`**: Game finished normally with a winner
- **`abandoned`**: Game was quit before completion
- **`ignored`**: Invitation was declined/ignored by player2

## Changes Made

### 1. Database Schema (`04-add-game-status.sql`)
- Added `game_status` column with CHECK constraint
- Created index for better query performance
- Migrated existing games to appropriate status values

### 2. Game Service (`microservices/game-service/app.py`)

#### Game Creation
- New games now start with `game_status = 'pending'`
- Games are invitations until player2 joins

#### Game Joining
- Added `mark_game_as_active()` function
- When player2 first draws cards or plays, status changes from `pending` to `active`
- This clearly marks when a game was actually joined

#### New Endpoint: `/api/games/<game_id>/ignore`
- POST endpoint for player2 to decline invitations
- Only works on `pending` games
- Sets `game_status = 'ignored'` and `is_active = false`
- Does NOT archive the game to history

#### Updated `/api/games/<game_id>/end`
- Determines appropriate status based on game state:
  - Games with winners → `completed`
  - Pending games being ended → `ignored`
  - Early abandonment (turn ≤ 1) → `abandoned`
  - Other endings without winner → `abandoned`
- Only archives games with status `completed` or `abandoned`
- Ignored and pending games are NOT archived

### 3. Leaderboard Service (`microservices/leaderboard-service/app.py`)
Updated all queries to filter by `game_status IN ('completed', 'abandoned')`:

- **`/api/leaderboard`**: Global leaderboard rankings
- **`/api/leaderboard/my-matches`**: User's match history
- **`/api/leaderboard/player/<player_name>`**: Individual player stats
- **`/api/leaderboard/recent-games`**: Recent completed games
- **`/api/leaderboard/top-players`**: Top players by various metrics
- **`/api/leaderboard/statistics`**: Global game statistics

All queries now exclude `pending` and `ignored` games from statistics.

### 4. Frontend (`frontend/js/home.js`)
- Updated `ignoreInvitation()` function
- Now calls `/api/games/<game_id>/ignore` endpoint
- Better error handling with user feedback

## Benefits

### 1. Accurate Statistics
- Leaderboard only counts games that were actually played
- Win/loss records are now accurate
- No inflation from ignored invitations

### 2. Clear Game Lifecycle
The status column provides complete visibility:
```
pending → active → completed/abandoned
pending → ignored (alternative path)
```

### 3. Better Data Management
- Ignored invitations don't clutter `game_history`
- Only actual games are archived
- Easy to query for different game states

### 4. User Experience
- Clear distinction between invitations and games
- Users can ignore invitations without penalty
- Statistics accurately reflect actual gameplay

## Testing Recommendations

### Test Scenarios
1. **Create and Ignore Invitation**
   - Create game invitation
   - Player2 ignores it
   - Verify game has `game_status = 'ignored'`
   - Verify it doesn't appear in leaderboard stats

2. **Create and Join Game**
   - Create game invitation
   - Player2 draws cards (first action)
   - Verify `game_status` changes from `pending` to `active`
   - Complete the game
   - Verify `game_status = 'completed'`
   - Verify it appears in leaderboard stats

3. **Abandon Active Game**
   - Start and join a game
   - End it before completion
   - Verify `game_status = 'abandoned'`
   - Verify it appears in leaderboard stats (as a played game)

4. **Leaderboard Accuracy**
   - Create multiple invitations and ignore them
   - Play actual games
   - Verify leaderboard only counts played games
   - Check all statistics endpoints

### SQL Queries for Verification
```sql
-- Check game status distribution
SELECT game_status, COUNT(*) 
FROM games 
GROUP BY game_status;

-- Verify ignored games aren't in history
SELECT COUNT(*) 
FROM games g
LEFT JOIN game_history gh ON g.game_id = gh.game_id
WHERE g.game_status = 'ignored' AND gh.game_id IS NOT NULL;
-- Should return 0

-- Verify completed/abandoned games are in history
SELECT COUNT(*) 
FROM games g
LEFT JOIN game_history gh ON g.game_id = gh.game_id
WHERE g.game_status IN ('completed', 'abandoned') AND gh.game_id IS NULL;
-- Should return 0 or very small number
```

## Migration Notes

### Deployment Steps
1. Stop all services
2. Run the migration script: `04-add-game-status.sql`
3. Rebuild and restart services with updated code
4. Verify migration success with status distribution query

### Backward Compatibility
- Existing queries using `is_active = false` will still work
- The migration script properly categorizes existing games
- No data loss or corruption

## API Changes

### New Endpoint
```
POST /api/games/<game_id>/ignore
Authorization: Bearer <token>

Response 200:
{
  "message": "Invitation ignored successfully"
}

Response 403:
{
  "error": "Only the invited player can ignore this invitation"
}

Response 400:
{
  "error": "Can only ignore pending invitations"
}
```

### Modified Endpoint Behavior
`POST /api/games/<game_id>/end` now:
- Sets appropriate `game_status` based on game state
- Only archives games that were actually played
- Returns same response format as before

## Future Enhancements

### Potential Improvements
1. **Invitation Expiration**: Add timeout for pending invitations
2. **Status Transitions**: Track status change timestamps
3. **Analytics**: Separate dashboards for invitations vs. games
4. **Notifications**: Alert users about pending invitations
5. **Bulk Operations**: Clear all ignored/old pending games

### Monitoring
Consider adding metrics for:
- Invitation acceptance rate
- Average time from pending to active
- Abandoned game rate
- Game completion rate

## Conclusion
This update provides a robust solution for managing game invitations separately from actual gameplay, ensuring accurate statistics and better user experience.
