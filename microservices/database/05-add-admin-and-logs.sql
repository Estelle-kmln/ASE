-- Add admin role and logging system
-- Migration script for adding admin functionality and system logs

-- Add is_admin column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- Create logs table for system monitoring
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    username VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

-- Create index for better performance on logs queries
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_username ON logs(username);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);

-- Create default admin user (password: Admin123!)
-- Password hash for 'Admin123!' using bcrypt
INSERT INTO users (username, password, is_admin, created_at)
VALUES (
    'admin',
    '$2b$12$jEunw.mQny9lmZ7.kQiAqO0XhAE1MWf662lOtXBhZd/2n8N.93R4K',
    TRUE,
    CURRENT_TIMESTAMP
)
ON CONFLICT (username) DO UPDATE
SET is_admin = TRUE;

-- Log the admin user creation
INSERT INTO logs (action, username, details)
VALUES ('SYSTEM_INIT', 'system', 'Default admin user created or updated');

-- Add comment to is_admin column
COMMENT ON COLUMN users.is_admin IS 'Indicates whether the user has administrator privileges';
COMMENT ON TABLE logs IS 'System logs for monitoring user actions and system events';
