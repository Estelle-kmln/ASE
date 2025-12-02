-- Add fields to track if players have drawn/played in current turn
-- This enforces the strict rule: each player draws once and plays once per turn

ALTER TABLE games 
ADD COLUMN IF NOT EXISTS player1_has_drawn BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS player2_has_drawn BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS player1_has_played BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS player2_has_played BOOLEAN DEFAULT FALSE;

-- Update existing games to set these flags to false
UPDATE games SET 
    player1_has_drawn = FALSE,
    player2_has_drawn = FALSE,
    player1_has_played = FALSE,
    player2_has_played = FALSE
WHERE player1_has_drawn IS NULL;
