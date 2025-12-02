CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Rock', 'Paper', 'Scissors')),
    power INTEGER NOT NULL CHECK (power >= 1 AND power <= 13),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO cards (type, power)
SELECT 'Rock', generate_series(1, 13)
UNION ALL
SELECT 'Paper', generate_series(1, 13)
UNION ALL
SELECT 'Scissors', generate_series(1, 13);
