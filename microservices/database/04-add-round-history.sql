-- Add round history tracking to games table
-- This will store the history of each round as JSON

ALTER TABLE games 
ADD COLUMN IF NOT EXISTS round_history TEXT DEFAULT '[]';

-- Add round history to game_history table for archived games
ALTER TABLE game_history
ADD COLUMN IF NOT EXISTS round_history TEXT DEFAULT '[]';

-- Update existing records to have empty array
UPDATE games SET round_history = '[]' WHERE round_history IS NULL;
UPDATE game_history SET round_history = '[]' WHERE round_history IS NULL;
