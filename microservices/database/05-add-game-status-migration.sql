-- Migration script to add game_status column and migrate from is_active
-- This script should be run on existing databases that still have is_active

-- Step 1: Add game_status column if it doesn't exist
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS game_status VARCHAR(20);

-- Step 2: Migrate data from is_active to game_status
-- Set game_status based on is_active and winner status
UPDATE games 
SET game_status = CASE 
    WHEN is_active = true AND winner IS NULL THEN 'active'
    WHEN is_active = true AND winner IS NOT NULL THEN 'completed'
    WHEN is_active = false AND winner IS NOT NULL THEN 'completed'
    WHEN is_active = false AND winner IS NULL THEN 'abandoned'
    ELSE 'pending'
END
WHERE game_status IS NULL;

-- Step 3: Set default value and make it NOT NULL
ALTER TABLE games 
ALTER COLUMN game_status SET DEFAULT 'pending',
ALTER COLUMN game_status SET NOT NULL;

-- Step 4: Add CHECK constraint
ALTER TABLE games 
DROP CONSTRAINT IF EXISTS games_game_status_check;

ALTER TABLE games 
ADD CONSTRAINT games_game_status_check 
CHECK (game_status IN ('pending', 'deck_selection', 'active', 'completed', 'abandoned', 'ignored'));

-- Step 5: Add deck selection columns (from 04-add-deck-selection-tracking.sql)
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS player1_deck_selected BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS player2_deck_selected BOOLEAN DEFAULT false;

-- Step 6: Create indexes
CREATE INDEX IF NOT EXISTS idx_games_game_status ON games(game_status);
CREATE INDEX IF NOT EXISTS idx_games_deck_selection ON games(player1_deck_selected, player2_deck_selected);

-- Step 7: Add comment
COMMENT ON COLUMN games.game_status IS 'Status of the game: pending (invitation), deck_selection (waiting for deck selection), active (in progress), completed (finished), abandoned (quit), ignored (declined invitation)';

-- Step 8: Remove is_active column and its index (optional - can be done separately)
-- ALTER TABLE games DROP COLUMN IF EXISTS is_active;
-- DROP INDEX IF EXISTS idx_games_is_active;
