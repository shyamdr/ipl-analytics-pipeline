-- 15. Players Table (Sourced primarily from people.csv)
CREATE TABLE Players (
    identifier TEXT PRIMARY KEY,
    name TEXT,
    unique_name TEXT,
    key_cricinfo TEXT,
    batting_hand TEXT,
    bowling_hand TEXT,
    player_role TEXT,
    date_of_birth DATE,
    country TEXT,
    bowling_style TEXT,
    full_name TEXT,
    CONSTRAINT players_pkey PRIMARY KEY (identifier)
);