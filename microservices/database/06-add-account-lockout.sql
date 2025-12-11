-- Add account lockout mechanism
-- Migration script for adding account security features

-- Add account lockout columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP NULL;

-- Create index for better performance on lockout queries
CREATE INDEX IF NOT EXISTS idx_users_account_locked ON users(account_locked_until);

-- Add comments to new columns
COMMENT ON COLUMN users.failed_login_attempts IS 'Number of consecutive failed login attempts';
COMMENT ON COLUMN users.account_locked_until IS 'Timestamp until which the account is locked (NULL if not locked)';
COMMENT ON COLUMN users.last_failed_login IS 'Timestamp of the last failed login attempt';

-- Log the migration
INSERT INTO logs (action, username, details)
VALUES ('SYSTEM_MIGRATION', 'system', 'Account lockout mechanism added to users table');
