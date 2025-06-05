-- 3. Venues Table
CREATE TABLE Venues (
    venue_id SERIAL PRIMARY KEY,
    venue_name TEXT NOT NULL UNIQUE, -- Added UNIQUE constraint here
    city TEXT,
    country TEXT
);