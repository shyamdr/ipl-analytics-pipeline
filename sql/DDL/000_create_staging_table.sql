-- Create the new table with id as TEXT
CREATE TABLE stg_match_data (
    id TEXT PRIMARY KEY,
    match_details JSONB
);