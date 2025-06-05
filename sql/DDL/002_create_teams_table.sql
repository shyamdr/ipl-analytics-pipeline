-- 2. Teams Table
CREATE TABLE Teams (
    team_id SERIAL PRIMARY KEY,
    team_name TEXT NOT NULL UNIQUE
);