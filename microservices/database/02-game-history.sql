-- PostgreSQL schema additions for immutable game history storage

CREATE TABLE IF NOT EXISTS game_history (
    game_id VARCHAR(255) PRIMARY KEY,
    player1_name VARCHAR(255) NOT NULL,
    player2_name VARCHAR(255) NOT NULL,
    player1_score INTEGER NOT NULL,
    player2_score INTEGER NOT NULL,
    winner VARCHAR(255),
    round_history TEXT DEFAULT '[]',
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    encrypted_payload BYTEA NOT NULL,
    integrity_hash VARCHAR(128) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_game_history_archived_at
    ON game_history(archived_at);

