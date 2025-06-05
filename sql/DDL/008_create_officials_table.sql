CREATE TABLE Officials (
    official_id TEXT PRIMARY KEY, -- Using the ID from registry.people
    official_name TEXT NOT NULL -- Could be redundant if name is in Players table
    -- default_role TEXT -- General role if any
);