-- Add session tracking columns to refresh_tokens table
-- This enables concurrent session detection and prevention

ALTER TABLE refresh_tokens
ADD COLUMN IF NOT EXISTS device_info VARCHAR(255),
ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45),
ADD COLUMN IF NOT EXISTS user_agent TEXT,
ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add index for faster active session queries
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_active 
ON refresh_tokens(user_id, revoked, expires_at) 
WHERE revoked = FALSE;

-- Add comment to document the table structure
COMMENT ON COLUMN refresh_tokens.device_info IS 'Device identifier or name (e.g., "Chrome on Windows", "Mobile Safari")';
COMMENT ON COLUMN refresh_tokens.ip_address IS 'IP address from which the session was created';
COMMENT ON COLUMN refresh_tokens.user_agent IS 'Full user agent string for detailed device tracking';
COMMENT ON COLUMN refresh_tokens.last_used_at IS 'Timestamp of last token usage for activity tracking';
