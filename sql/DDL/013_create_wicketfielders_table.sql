-- 13. WicketFielders Table - FK to Players.identifier
CREATE TABLE WicketFielders (
    wicket_fielder_id SERIAL PRIMARY KEY,
    wicket_id BIGINT REFERENCES Wickets(wicket_id) NOT NULL,
    fielder_player_identifier TEXT REFERENCES Players(identifier) NOT NULL, -- Changed FK
    UNIQUE (wicket_id, fielder_player_identifier)
);