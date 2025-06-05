-- 14. Replacements Table - FKs to Players.identifier
CREATE TABLE Replacements (
    replacement_id SERIAL PRIMARY KEY,
    match_id TEXT REFERENCES Matches(match_id) NOT NULL,
    delivery_id BIGINT REFERENCES Deliveries(delivery_id),
    inning_id INTEGER REFERENCES Innings(inning_id),
    team_id INTEGER REFERENCES Teams(team_id) NOT NULL,
    player_in_identifier TEXT REFERENCES Players(identifier) NOT NULL,  -- Changed FK
    player_out_identifier TEXT REFERENCES Players(identifier) NOT NULL, -- Changed FK
    reason TEXT
);