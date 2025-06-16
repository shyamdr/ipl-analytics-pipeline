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

	-- STEP 5: FUZZY MATCHING FALLBACK
    WITH MetaphoneTexts AS ( --FuzzyCandidates
        SELECT
            p.identifier,
			metaphone(p.full_name, 255) AS mcode_full_name,
			metaphone(p.first_last_name, 255) AS mcode_first_last_name,
			metaphone(search_name, 255) AS mcode_search_name
        FROM Players p
        WHERE p.first_last_name IS NOT NULL
    ),
	FuzzyCandidates AS (
		SELECT
			*,
			levenshtein(mcode_search_name, mcode_first_last_name) AS lv_score1,
			similarity(mcode_search_name, mcode_first_last_name) AS trigram_score1,
			levenshtein(mcode_search_name, mcode_full_name) AS lv_score2,
			similarity(mcode_search_name, mcode_full_name) AS trigram_score2
		FROM MetaphoneTexts
	)
	SELECT identifier INTO found_identifier
	FROM FuzzyCandidates
	WHERE
	    ((lv_score1 <= round(0.3 * GREATEST(LENGTH(mcode_search_name), LENGTH(mcode_first_last_name))) AND trigram_score1 >= 0.3)
	    OR (lv_score2 <= round(0.3 * GREATEST(LENGTH(mcode_search_name), LENGTH(mcode_full_name))) AND trigram_score1 >= 0.3))
	ORDER BY lv_score1 ASC, trigram_score1 DESC, lv_score2 ASC, trigram_score2 DESC
	LIMIT 1;

	RETURN found_identifier;

    -- If no unique match is found after all checks, return NULL
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;