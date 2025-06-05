-- 5. MatchPlayers (Playing XI) - FK to Players.identifier
CREATE TABLE MatchPlayers (
    match_player_id SERIAL PRIMARY KEY,
    match_id TEXT REFERENCES Matches(match_id) NOT NULL,
    player_identifier TEXT REFERENCES Players(identifier) NOT NULL, -- Changed FK
    team_id INTEGER REFERENCES Teams(team_id) NOT NULL,
    is_captain BOOLEAN DEFAULT FALSE,
    is_wicket_keeper BOOLEAN DEFAULT FALSE,
    UNIQUE (match_id, player_identifier)
);