-- Create cards table for Rock Paper Scissors
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Rock', 'Paper', 'Scissors')),
    power INTEGER NOT NULL CHECK (power >= 1 AND power <= 13),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(type);
CREATE INDEX IF NOT EXISTS idx_cards_power ON cards(power);
- Insert all possible RPS cards (type + power combinations)
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