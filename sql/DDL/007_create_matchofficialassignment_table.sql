-- 7. MatchOfficialsAssignment Table - FK to Players.identifier (assuming officials are in Players table)
CREATE TABLE MatchOfficialsAssignment (
    match_official_assignment_id SERIAL PRIMARY KEY,
    match_id TEXT REFERENCES Matches(match_id) NOT NULL,
    official_identifier TEXT REFERENCES Players(identifier) NOT NULL, -- Changed FK, assuming official is a Player
    match_role TEXT NOT NULL, -- e.g., "umpire", "tv_umpire" from JSON
    UNIQUE (match_id, official_identifier, match_role)
);