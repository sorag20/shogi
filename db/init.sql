-- Create database tables for Shogi App

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id VARCHAR(36) PRIMARY KEY,
    board_state JSON NOT NULL,
    turn ENUM('black', 'white') NOT NULL DEFAULT 'black',
    position_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kifus table (棋譜)
CREATE TABLE IF NOT EXISTS kifus (
    id VARCHAR(36) PRIMARY KEY,
    black_player VARCHAR(255),
    white_player VARCHAR(255),
    game_date DATE,
    result VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Moves table
CREATE TABLE IF NOT EXISTS moves (
    id VARCHAR(36) PRIMARY KEY,
    kifu_id VARCHAR(36) NOT NULL,
    move_number INT NOT NULL,
    notation VARCHAR(50) NOT NULL,
    from_square VARCHAR(10),
    to_square VARCHAR(10),
    piece_type VARCHAR(20),
    is_promotion BOOLEAN DEFAULT FALSE,
    is_drop BOOLEAN DEFAULT FALSE,
    comment TEXT,
    position_after JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kifu_id) REFERENCES kifus(id) ON DELETE CASCADE,
    INDEX idx_kifu_id (kifu_id),
    INDEX idx_move_number (move_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes
CREATE INDEX idx_positions_created_at ON positions(created_at);
CREATE INDEX idx_kifus_created_at ON kifus(created_at);
