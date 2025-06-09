-- 9. Innings Table (No change in its own columns, but context of related tables changes)
CREATE TABLE Innings (
    inning_id SERIAL PRIMARY KEY,
    match_id TEXT REFERENCES Matches(match_id) NOT NULL,
    inning_number INTEGER NOT NULL,
    batting_team_id INTEGER REFERENCES Teams(team_id) NOT NULL,
    bowling_team_id INTEGER REFERENCES Teams(team_id) NOT NULL,
    target_runs INTEGER,
    target_overs TEXT,
    is_super_over BOOLEAN
    UNIQUE (match_id, inning_number)
);