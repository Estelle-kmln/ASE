-- Create cards table for Rock Paper Scissors
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Rock', 'Paper', 'Scissors')),
    power INTEGER NOT NULL CHECK (power BETWEEN 1 AND 13),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(type);
CREATE INDEX IF NOT EXISTS idx_cards_power ON cards(power);