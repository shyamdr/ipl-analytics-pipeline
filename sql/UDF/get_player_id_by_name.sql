CREATE OR REPLACE FUNCTION get_player_id_by_name(search_name TEXT)
RETURNS TEXT AS $$
DECLARE
    found_identifier TEXT;
    match_count INTEGER;
BEGIN
    -- Step 1: Check for an exact, unique match on first_last_name (case-insensitive)
    SELECT identifier, count(1) INTO found_identifier, match_count
    FROM Players WHERE lower(first_last_name) = lower(search_name)
    GROUP BY identifier;

    IF match_count = 1 THEN
        RETURN found_identifier;
    END IF;

    -- Step 2: If not found, check full_name
    SELECT identifier, count(1) INTO found_identifier, match_count
    FROM Players WHERE lower(full_name) = lower(search_name)
    GROUP BY identifier;

    IF match_count = 1 THEN
        RETURN found_identifier;
    END IF;

    -- Step 3: If not found, check unique_name
    SELECT identifier, count(1) INTO found_identifier, match_count
    FROM Players WHERE lower(unique_name) = lower(search_name)
    GROUP BY identifier;

    IF match_count = 1 THEN
        RETURN found_identifier;
    END IF;

    -- Step 4: If not found, check name
    SELECT identifier, count(1) INTO found_identifier, match_count
    FROM Players WHERE lower(name) = lower(search_name)
    GROUP BY identifier;

    IF match_count = 1 THEN
        RETURN found_identifier;
    END IF;

    -- If no unique match is found after all checks, return NULL
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;