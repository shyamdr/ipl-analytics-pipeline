-- 6. PlayerOfMatchAwards Table - FK to Players.identifier
CREATE TABLE PlayerOfMatchAwards (
    award_id SERIAL PRIMARY KEY,
    match_id TEXT REFERENCES Matches(match_id) NOT NULL,
    player_identifier TEXT REFERENCES Players(identifier) NOT NULL -- Changed FK
);