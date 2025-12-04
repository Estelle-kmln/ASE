-- Add deck selection tracking columns to games table
-- This allows tracking whether players have selected their decks before the game starts

-- First, add the deck selection tracking columns
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS player1_deck_selected BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS player2_deck_selected BOOLEAN DEFAULT false;

-- Update the game_status CHECK constraint to include 'deck_selection'
-- We need to drop and recreate the constraint
ALTER TABLE games 
DROP CONSTRAINT IF EXISTS games_game_status_check;

ALTER TABLE games 
ADD CONSTRAINT games_game_status_check 
CHECK (game_status IN ('pending', 'deck_selection', 'active', 'completed', 'abandoned', 'ignored'));

-- Create index for better performance when checking deck selection status
CREATE INDEX IF NOT EXISTS idx_games_deck_selection ON games(player1_deck_selected, player2_deck_selected);

-- Update the comment to reflect the new status
COMMENT ON COLUMN games.game_status IS 'Status of the game: pending (invitation), deck_selection (waiting for deck selection), active (in progress), completed (finished), abandoned (quit), ignored (declined invitation)';
