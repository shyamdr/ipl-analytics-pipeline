-- 11. Deliveries Table - FKs to Players.identifier
CREATE TABLE Deliveries (
    delivery_id BIGSERIAL PRIMARY KEY,
    inning_id INTEGER REFERENCES Innings(inning_id) NOT NULL,
    over_number INTEGER NOT NULL,
    ball_number_in_over INTEGER NOT NULL,
    batter_identifier TEXT REFERENCES Players(identifier) NOT NULL,      -- Changed FK
    bowler_identifier TEXT REFERENCES Players(identifier) NOT NULL,      -- Changed FK
    non_striker_identifier TEXT REFERENCES Players(identifier) NOT NULL, -- Changed FK
    runs_batter INTEGER NOT NULL,
    runs_extras INTEGER NOT NULL,
    runs_non_boundary BOOLEAN,
    runs_total INTEGER NOT NULL,
    extras_wides INTEGER DEFAULT 0,
    extras_noballs INTEGER DEFAULT 0,
    extras_byes INTEGER DEFAULT 0,
    extras_legbyes INTEGER DEFAULT 0,
    extras_penalty INTEGER DEFAULT 0,
    raw_extras_json JSONB,
    raw_review_json JSONB
);
