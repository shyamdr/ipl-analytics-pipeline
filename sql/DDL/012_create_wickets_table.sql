-- 12. Wickets Table - FKs to Players.identifier
CREATE TABLE Wickets (
    wicket_id BIGSERIAL PRIMARY KEY,
    delivery_id BIGINT REFERENCES Deliveries(delivery_id) NOT NULL,
    player_out_identifier TEXT REFERENCES Players(identifier) NOT NULL, -- Changed FK
    kind TEXT NOT NULL,
    bowler_credited_identifier TEXT REFERENCES Players(identifier) -- Changed FK
);