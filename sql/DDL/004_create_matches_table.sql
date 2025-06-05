-- 4. Matches Table
CREATE TABLE Matches (
    match_id TEXT PRIMARY KEY, -- Your filename-derived ID from stg_match_data
    season_year INTEGER NOT NULL,
    match_date DATE,
    event_name TEXT,
    match_number INTEGER,
    venue_id INTEGER REFERENCES Venues(venue_id),
    team1_id INTEGER REFERENCES Teams(team_id),
    team2_id INTEGER REFERENCES Teams(team_id),
    toss_winner_team_id INTEGER REFERENCES Teams(team_id),
    toss_decision TEXT,
    outcome_winner_team_id INTEGER REFERENCES Teams(team_id),
    outcome_type TEXT,
    outcome_margin INTEGER,
    match_type TEXT,
    overs_limit INTEGER,
    balls_per_over INTEGER,
    CONSTRAINT fk_team1_match CHECK (team1_id IS NULL OR team1_id != team2_id),
    CONSTRAINT fk_team2_match CHECK (team2_id IS NULL OR team1_id != team2_id)
);