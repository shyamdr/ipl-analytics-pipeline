-- 1. Players Table (Sourced primarily from people.csv)
CREATE TABLE Players (
    identifier TEXT PRIMARY KEY,         -- From people.csv 'identifier' column
    name TEXT,                           -- From people.csv 'name' column (Consider making this NOT NULL if appropriate)
    full_name TEXT,                      -- From people.csv 'full_name' column
    date_of_birth DATE,                  -- From people.csv 'date_of_birth', allows NULL
    country TEXT,                        -- From people.csv 'country', allows NULL
    batting_hand TEXT,                   -- From people.csv 'batting_hand', allows NULL
    bowling_hand TEXT,                   -- From people.csv 'bowling_hand', allows NULL
    bowling_style TEXT,                  -- From people.csv 'bowling_style', allows NULL
    known_as TEXT,                       -- From people.csv 'known_as', allows NULL
    roles TEXT[]                         -- From people.csv 'roles', stored as an array of text, allows NULL
);