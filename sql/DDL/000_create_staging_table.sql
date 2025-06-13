    -- This is a staging table to hold the raw JSON data from the source files.
    -- DO NOT use this table for analytical queries.
    -- Use the final relational tables (Matches, Innings, etc.) instead.

CREATE TABLE stg_match_data (
    id TEXT PRIMARY KEY,
    match_details JSONB
);