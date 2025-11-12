-- PostgreSQL initialization script for Battle Card Game
-- This script will create the tables and populate them with initial card data

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create cards table
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    power INTEGER NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(type);
CREATE INDEX IF NOT EXISTS idx_cards_power ON cards(power);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Insert sample battle cards
INSERT INTO cards (type, power) VALUES
('Rock', 1),
('Paper', 1),
('Scissors', 1),
('Rock', 2),
('Paper', 2),
('Scissors', 2),
('Rock', 3),
('Paper', 3),
('Scissors', 3),
('Rock', 4),
('Paper', 4),
('Scissors', 4),
('Rock', 5),
('Paper', 5),
('Scissors', 5),
('Rock', 6),
('Paper', 6),
('Scissors', 6),
('Rock', 7),
('Paper', 7),
('Scissors', 7),
('Rock', 8),
('Paper', 8),
('Scissors', 8),
('Rock', 9),
('Paper', 9),
('Scissors', 9),
('Rock', 10),
('Paper', 10),
('Scissors', 10),
('Rock', 11),
('Paper', 11),
('Scissors', 11),
('Rock', 12),
('Paper', 12),
('Scissors', 12),
('Rock', 13),
('Paper', 13),
('Scissors', 13);

-- Print confirmation
SELECT 'Battle Cards database initialized successfully!' as message;
SELECT CONCAT('Inserted ', COUNT(*), ' cards into the database.') as card_count FROM cards;