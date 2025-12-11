-- Add tiebreaker fields to games table for handling 7th round tie scenarios
-- When turn 7 ends in a tie, players are prompted to play their 22nd card

-- Add column to track if game is awaiting tiebreaker decision
ALTER TABLE games ADD COLUMN IF NOT EXISTS awaiting_tiebreaker_response BOOLEAN DEFAULT FALSE;

-- Add columns to track each player's tiebreaker decision
ALTER TABLE games ADD COLUMN IF NOT EXISTS player1_tiebreaker_decision VARCHAR(10); -- 'yes' or 'no'
ALTER TABLE games ADD COLUMN IF NOT EXISTS player2_tiebreaker_decision VARCHAR(10); -- 'yes' or 'no'

-- Add comment for the new columns
COMMENT ON COLUMN games.awaiting_tiebreaker_response IS 'True when game ended in 7th round tie and waiting for players to decide if they want to play the 22nd card';
COMMENT ON COLUMN games.player1_tiebreaker_decision IS 'Player 1 decision on tiebreaker: yes (play 22nd card) or no (end game as tie)';
COMMENT ON COLUMN games.player2_tiebreaker_decision IS 'Player 2 decision on tiebreaker: yes (play 22nd card) or no (end game as tie)';

-- Print confirmation
SELECT 'Tiebreaker fields added to games table successfully!' as message;
