-- Add leaderboard visibility preference
-- Migration script for adding user privacy control for leaderboard display

-- Add show_on_leaderboard column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS show_on_leaderboard BOOLEAN DEFAULT TRUE;

-- Create index for better performance on leaderboard queries
CREATE INDEX IF NOT EXISTS idx_users_show_on_leaderboard ON users(show_on_leaderboard);

-- Add comment to show_on_leaderboard column
COMMENT ON COLUMN users.show_on_leaderboard IS 'Indicates whether the user wants to appear on the global leaderboard. Default is TRUE (visible).';

-- Log the migration
INSERT INTO logs (action, username, details)
VALUES ('SYSTEM_MIGRATION', 'system', 'Added leaderboard visibility preference column to users table');

SELECT 'Leaderboard visibility preference added successfully!' as message;
