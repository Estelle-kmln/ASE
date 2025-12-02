-- PostgreSQL initialization script for Rock Paper Scissors Battle Card Game
-- This script will create the tables and populate them with initial card data

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create cards table for Rock Paper Scissors
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Rock', 'Paper', 'Scissors')),
    power INTEGER NOT NULL CHECK (power >= 1 AND power <= 13),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create games table for storing game state and results
CREATE TABLE IF NOT EXISTS games (
    game_id VARCHAR(255) PRIMARY KEY,
    turn INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    player1_name VARCHAR(255) NOT NULL,
    player1_deck_cards TEXT,
    player1_hand_cards TEXT,
    player1_played_card TEXT,
    player2_name VARCHAR(255) NOT NULL,
    player2_deck_cards TEXT,
    player2_hand_cards TEXT,
    player2_played_card TEXT,
    winner VARCHAR(255),
    player1_score INTEGER DEFAULT 0,
    player2_score INTEGER DEFAULT 0,
    round_history TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(type);
CREATE INDEX IF NOT EXISTS idx_cards_power ON cards(power);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_games_is_active ON games(is_active);
CREATE INDEX IF NOT EXISTS idx_games_player1_name ON games(player1_name);
CREATE INDEX IF NOT EXISTS idx_games_player2_name ON games(player2_name);
CREATE INDEX IF NOT EXISTS idx_games_winner ON games(winner);

-- Insert all possible RPS cards (type + power combinations)
-- Rock cards (power 1-13)
INSERT INTO cards (type, power) VALUES
('Rock', 1), ('Rock', 2), ('Rock', 3), ('Rock', 4), ('Rock', 5), ('Rock', 6), ('Rock', 7),
('Rock', 8), ('Rock', 9), ('Rock', 10), ('Rock', 11), ('Rock', 12), ('Rock', 13);

-- Paper cards (power 1-13)  
INSERT INTO cards (type, power) VALUES
('Paper', 1), ('Paper', 2), ('Paper', 3), ('Paper', 4), ('Paper', 5), ('Paper', 6), ('Paper', 7),
('Paper', 8), ('Paper', 9), ('Paper', 10), ('Paper', 11), ('Paper', 12), ('Paper', 13);

-- Scissors cards (power 1-13)
INSERT INTO cards (type, power) VALUES
('Scissors', 1), ('Scissors', 2), ('Scissors', 3), ('Scissors', 4), ('Scissors', 5), ('Scissors', 6), ('Scissors', 7),
('Scissors', 8), ('Scissors', 9), ('Scissors', 10), ('Scissors', 11), ('Scissors', 12), ('Scissors', 13);

-- Print confirmation
SELECT 'Rock Paper Scissors Battle Card Game database initialized successfully!' as message;
SELECT CONCAT('Created ', COUNT(*), ' RPS cards in the database.') as card_count FROM cards;