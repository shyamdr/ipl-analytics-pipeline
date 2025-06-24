-- FUNCTION: public.get_player_id_by_name(text)

-- DROP FUNCTION IF EXISTS public.get_player_id_by_name(text);

CREATE OR REPLACE FUNCTION public.get_player_id_by_name(
	search_name text)
    RETURNS text
    LANGUAGE 'plpgsql'
    COST 100
    STABLE PARALLEL UNSAFE
AS $BODY$
DECLARE
    found_identifier TEXT;
    match_count INTEGER;
    name_array TEXT[];
    current_name TEXT;
BEGIN
    -- Generate name variants based on nickname mappings
    WITH NameMapping AS (
        SELECT 'chris' AS nickname, 'christopher' AS longform UNION
        SELECT 'ben' AS nickname, 'benjamin' AS longform UNION
		SELECT 'mike' AS nickname, 'michael' AS longform UNION
		SELECT 'joe' AS nickname, 'joseph' AS longform UNION
		SELECT 'md' AS nickname, 'mohammed' AS longform UNION
		SELECT 'mohd' AS nickname, 'mohammed' AS longform UNION
		SELECT 'dan' AS nickname, 'daniel' AS longform UNION
		SELECT 'matt' AS nickname, 'matthew' AS longform UNION
		SELECT 'steve' AS nickname, 'steven' AS longform UNION
		SELECT 'tim' AS nickname, 'timothy' AS longform UNION
		SELECT 'sam' AS nickname, 'samuel' AS longform UNION
		SELECT 'nick' AS nickname, 'nicholas' AS longform UNION
		SELECT 'greg' AS nickname, 'gregory' AS longform UNION
		SELECT 'mark' AS nickname, 'marcus' AS longform UNION
		SELECT 'john' AS nickname, 'johnny' AS longform
    ),
    SplitName AS (
        SELECT 
            TRIM(SPLIT_PART(search_name, ' ', 1)) AS first_name,
            TRIM(SPLIT_PART(search_name, ' ', 2)) AS last_name
    ),
    NameVariants AS (
        SELECT 
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM NameMapping nm 
                    WHERE nm.nickname = SplitName.first_name
                )
                THEN ARRAY[
                    search_name,
                    (SELECT nm.longform FROM NameMapping nm WHERE nm.nickname = SplitName.first_name) || ' ' || SplitName.last_name
                ]
                ELSE ARRAY[search_name]
            END AS name_array
        FROM SplitName
    )
    SELECT NameVariants.name_array INTO name_array FROM NameVariants;

    -- Loop through each name in the array
    FOREACH current_name IN ARRAY name_array
    LOOP
        -- Step 1: Check first_last_name
        SELECT identifier, COUNT(1)
        INTO found_identifier, match_count
        FROM Players
        WHERE LOWER(first_last_name) = LOWER(current_name)
            AND identifier IS NOT NULL
        GROUP BY identifier
        HAVING COUNT(1) = 1;

        IF match_count = 1 THEN
            RETURN found_identifier;
        END IF;

        -- Step 2: Check full_name
        SELECT identifier, COUNT(1)
        INTO found_identifier, match_count
        FROM Players
        WHERE LOWER(full_name) = LOWER(current_name)
            AND identifier IS NOT NULL
        GROUP BY identifier
        HAVING COUNT(1) = 1;

        IF match_count = 1 THEN
            RETURN found_identifier;
        END IF;

        -- Step 3: Check unique_name
        SELECT identifier, COUNT(1)
        INTO found_identifier, match_count
        FROM Players
        WHERE LOWER(unique_name) = LOWER(current_name)
            AND identifier IS NOT NULL
        GROUP BY identifier
        HAVING COUNT(1) = 1;

        IF match_count = 1 THEN
            RETURN found_identifier;
        END IF;

        -- Step 4: Check name
        SELECT identifier, COUNT(1)
        INTO found_identifier, match_count
        FROM Players
        WHERE LOWER(name) = LOWER(current_name)
            AND identifier IS NOT NULL
        GROUP BY identifier
        HAVING COUNT(1) = 1;

        IF match_count = 1 THEN
            RETURN found_identifier;
        END IF;
    END LOOP;

    -- Step 5: Fuzzy matching fallback for all names in the array
    WITH UnnestedNames AS (
        SELECT UNNEST(name_array) AS search_name
    ),
    MetaphoneTexts AS (
        SELECT
            n.search_name,
            p.identifier,
            metaphone(p.full_name, 255) AS mcode_full_name,
            metaphone(p.first_last_name, 255) AS mcode_first_last_name,
            metaphone(n.search_name, 255) AS mcode_search_name
        FROM UnnestedNames n
        CROSS JOIN Players p
        WHERE p.first_last_name IS NOT NULL
    ),
    FuzzyCandidates AS (
        SELECT
            mt.search_name,
            mt.identifier,
            levenshtein(mt.mcode_search_name, mt.mcode_first_last_name) AS lv_score1,
            similarity(mt.mcode_search_name, mt.mcode_first_last_name) AS trigram_score1,
            levenshtein(mt.mcode_search_name, mt.mcode_full_name) AS lv_score2,
            similarity(mt.mcode_search_name, mt.mcode_full_name) AS trigram_score2
        FROM MetaphoneTexts mt
        WHERE 
            ((levenshtein(mt.mcode_search_name, mt.mcode_first_last_name) <= ROUND(0.3 * GREATEST(LENGTH(mt.mcode_search_name), LENGTH(mt.mcode_first_last_name)))
                AND similarity(mt.mcode_search_name, mt.mcode_first_last_name) >= 0.3)
            OR (levenshtein(mt.mcode_search_name, mt.mcode_full_name) <= ROUND(0.3 * GREATEST(LENGTH(mt.mcode_search_name), LENGTH(mt.mcode_full_name)))
                AND similarity(mt.mcode_search_name, mt.mcode_full_name) >= 0.3))
            AND mt.identifier IS NOT NULL
    )
    SELECT identifier INTO found_identifier
    FROM FuzzyCandidates
    ORDER BY lv_score1 ASC, trigram_score1 DESC, lv_score2 ASC, trigram_score2 DESC
    LIMIT 1;

    RETURN found_identifier;

    -- Return NULL if no match is found
    RETURN NULL;
END;
$BODY$;

ALTER FUNCTION public.get_player_id_by_name(text)
    OWNER TO postgres;
