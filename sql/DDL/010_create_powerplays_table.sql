-- 10. Powerplays Table (No change)
CREATE TABLE Powerplays (
    powerplay_id SERIAL PRIMARY KEY,
    inning_id INTEGER REFERENCES Innings(inning_id) NOT NULL,
    type TEXT NOT NULL,
    from_over DECIMAL(3,1) NOT NULL,
    to_over DECIMAL(3,1) NOT NULL
);