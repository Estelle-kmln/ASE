# Database Migration: Removing is_active Field

## Overview
This migration removes the `is_active` boolean field from the `games` table and replaces all its functionality with the more granular `game_status` field.

## Rationale
- The `is_active` boolean field was redundant with `game_status`
- `game_status` provides more specific states: `pending`, `active`, `deck_selection`, `completed`, `abandoned`, `ignored`
- Better handling of pending invitations and various game states
- Simpler database schema without duplicate state tracking

## Changes Made

### 1. Database Schema
**File**: `microservices/database/01-init-cards.sql`
- Removed `is_active BOOLEAN NOT NULL DEFAULT true` column from `games` table
- Removed `idx_games_is_active` index
- Updated `game_status` CHECK constraint to include `deck_selection` state
- Updated comments to reflect the change

**File**: `microservices/database/05-remove-is-active.sql` (NEW)
- Migration script to drop the `is_active` column from existing databases
- Drops the `idx_games_is_active` index
- Safe to run on existing installations

### 2. Backend API (game-service)
**File**: `microservices/game-service/app.py`
- Removed `is_active` from INSERT statements when creating games
- Removed `is_active` from UPDATE statements when ending/updating games
- Removed `is_active` from SELECT statements
- Replaced all `if not game["is_active"]` checks with `if game["game_status"] not in ['active', 'pending', 'deck_selection']`
- Replaced `if game["is_active"]` checks with `if game["game_status"] == 'completed'` (context-dependent)
- Updated response payloads to return `game_status` instead of `is_active`

### 3. Frontend
**File**: `frontend/js/home.js`
- Changed pending games filter from `game.is_active && ...` to `game.game_status === 'pending' && ...`
- Changed active games filter from `game.is_active && ...` to `game.game_status === 'active' && ...`

**File**: `frontend/js/game.js`
- Changed `if (!gameState.is_active)` to `if (gameState.game_status === 'completed' || gameState.game_status === 'abandoned' || gameState.game_status === 'ignored')`

### 4. Tests
**File**: `tests/test_game_service.py`
- Changed assertions from checking `is_active` to checking `game_status`
- Updated to verify `game_status` is in valid states

**File**: `tests/test_complete_game_flow.py`
- Changed `if not game_state['is_active']` to `if game_state['game_status'] in ['completed', 'abandoned', 'ignored']`
- Updated print statements to show `game_status` instead of `is_active`

**File**: `tests/microservices_postman_collection.json`
- Updated test assertions from `pm.expect(jsonData).to.have.property('is_active')` to `pm.expect(jsonData).to.have.property('game_status')`

### 5. API Documentation
**File**: `openapi.yaml`
- Updated `Game` schema to use `game_status` (enum type) instead of `is_active` (boolean)
- Updated required fields list

**File**: `documentation/API_Documentation.md`
- Updated example responses to show `game_status` instead of `is_active`

## Migration Steps

### For New Installations
1. Simply use the updated `01-init-cards.sql` - no migration needed

### For Existing Databases
1. Run the migration script:
   ```bash
   psql -U gameuser -d battlecards -f microservices/database/05-remove-is-active.sql
   ```

2. Rebuild and restart the services:
   ```bash
   cd microservices
   docker compose down
   docker compose up -d --build
   ```

## API Response Changes

### Before
```json
{
  "game_id": "uuid",
  "turn": 1,
  "is_active": true,
  "game_status": "active",
  ...
}
```

### After
```json
{
  "game_id": "uuid",
  "turn": 1,
  "game_status": "active",
  ...
}
```

## Game Status Values
- `pending`: Invitation sent but not yet accepted
- `active`: Game in progress
- `deck_selection`: Players are selecting their decks
- `completed`: Game finished normally with a winner
- `abandoned`: Game ended early without completion
- `ignored`: Invitation was declined

## Backward Compatibility
⚠️ **Breaking Change**: This is a breaking change for clients that rely on the `is_active` field.

Clients must update to check `game_status` instead:
- Instead of `is_active === true`, check `game_status in ['pending', 'active', 'deck_selection']`
- Instead of `is_active === false`, check `game_status in ['completed', 'abandoned', 'ignored']`

## Testing
After migration:
1. Test game creation
2. Test accepting invitations
3. Test active game flow
4. Test ignoring invitations
5. Test ending games
6. Run automated tests: `python tests/test_game_service.py`
