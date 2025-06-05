WITH AllDeliveries AS (
    -- Unnest all deliveries from all matches to have a base to work from
    SELECT
        md.id AS match_id,
        (i.data ->> 'team') AS current_batting_team,
        i.idx AS innings_idx_in_match, -- 1-based index from ORDINALITY
        o.idx AS over_in_innings,      -- 1-based index from ORDINALITY
        d.idx AS ball_in_over,         -- 1-based index from ORDINALITY
        d.delivery_obj ->> 'batter' AS batter,
        d.delivery_obj ->> 'bowler' AS bowler,
        d.delivery_obj -> 'runs' AS runs_obj,
        d.delivery_obj -> 'extras' AS extras_obj, -- Object like {"wides": 1} or {"noballs": 1}
        d.delivery_obj -> 'wickets' AS wickets_array -- Array of wicket objects
    FROM
        match_data md,
        LATERAL jsonb_array_elements(md.match_details -> 'innings') WITH ORDINALITY AS i(data, idx),
        LATERAL jsonb_array_elements(i.data -> 'overs') WITH ORDINALITY AS o(data, idx),
        LATERAL jsonb_array_elements(o.data -> 'deliveries') WITH ORDINALITY AS d(delivery_obj, idx)
),
BowlerDeliveryStats AS (
    -- Calculate per-delivery stats relevant for bowlers
    SELECT
        bowler,
        batter,
        (runs_obj ->> 'batter')::integer AS runs_off_bat,
        COALESCE((extras_obj ->> 'wides')::integer, 0) AS wides,
        COALESCE((extras_obj ->> 'noballs')::integer, 0) AS noballs,
        COALESCE((extras_obj ->> 'byes')::integer, 0) AS byes,
        COALESCE((extras_obj ->> 'legbyes')::integer, 0) AS legbyes,
        (runs_obj ->> 'total')::integer AS total_runs_on_ball,
        CASE
            WHEN wickets_array IS NOT NULL AND jsonb_array_length(wickets_array) > 0 THEN
                CASE
                    WHEN wickets_array -> 0 ->> 'kind' NOT IN ('run out', 'retired hurt', 'obstructing the field', 'handled the ball', 'timed out')
                    THEN 1
                    ELSE 0
                END
            ELSE 0
        END AS is_bowler_wicket,
        CASE -- Ball bowled (not a wide)
            WHEN COALESCE((extras_obj ->> 'wides')::integer, 0) = 0 THEN 1
            ELSE 0
        END AS is_legal_delivery_for_over, -- Counts towards 6 balls of over (excludes wides)
        CASE -- Dot ball bowled (strict: no runs off bat, no byes/legbyes on a legal delivery)
            WHEN (runs_obj ->> 'batter')::integer = 0 AND
                 COALESCE((extras_obj ->> 'wides')::integer, 0) = 0 AND
                 COALESCE((extras_obj ->> 'noballs')::integer, 0) = 0 AND
                 COALESCE((extras_obj ->> 'byes')::integer, 0) = 0 AND
                 COALESCE((extras_obj ->> 'legbyes')::integer, 0) = 0
            THEN 1 ELSE 0
        END AS is_dot_ball_bowled
    FROM AllDeliveries
),
BowlerAggregatedStats AS (
    -- Aggregate stats for each bowler
    SELECT
        bowler,
        SUM(is_bowler_wicket) AS total_wickets,
        SUM(runs_off_bat + wides + noballs) AS total_runs_conceded, -- Runs bowler is responsible for
        SUM(is_legal_delivery_for_over) AS total_balls_bowled, -- Legal balls for overs (used for economy)
        SUM(CASE WHEN is_bowler_wicket > 0 THEN 1 ELSE 0 END * is_legal_delivery_for_over) AS balls_bowled_for_wickets, -- Balls bowled when wicket taken by bowler
        SUM(is_dot_ball_bowled) AS dot_balls_bowled
    FROM BowlerDeliveryStats
    GROUP BY bowler
    HAVING SUM(is_legal_delivery_for_over) > 0 -- Bowler must have bowled at least one legal ball
),
TopBowlers AS (
    -- Determine top 25 bowlers based on criteria
    SELECT
        bowler,
        total_wickets,
        total_runs_conceded,
        total_balls_bowled,
        dot_balls_bowled,
        (total_runs_conceded * 6.0 / NULLIF(total_balls_bowled, 0)) AS economy_rate,
        (total_balls_bowled * 1.0 / NULLIF(total_wickets, 0)) AS bowling_strike_rate, -- Balls per wicket
        (total_runs_conceded * 1.0 / NULLIF(total_wickets, 0)) AS bowling_average
    FROM BowlerAggregatedStats
    ORDER BY
        total_wickets DESC,
        bowling_strike_rate ASC NULLS LAST, -- Lower is better
        bowling_average ASC NULLS LAST,   -- Lower is better
        economy_rate ASC NULLS LAST,      -- Lower is better
        dot_balls_bowled DESC
    LIMIT 25
),
-- You can query the TopBowlers CTE directly if you want to see the list:
-- SELECT * FROM TopBowlers;

BatsmanDeliveryDetailsAgainstTop AS (
    -- Get delivery details for batsmen ONLY against the Top 25 Bowlers
    SELECT
        ad.match_id,
        ad.innings_idx_in_match,
        ad.batter,
        ad.bowler,
        (ad.runs_obj ->> 'batter')::integer AS runs_scored,
        CASE WHEN COALESCE((ad.extras_obj ->> 'wides')::integer, 0) = 0 THEN 1 ELSE 0 END AS ball_faced, -- Not a wide
        CASE WHEN (ad.runs_obj ->> 'batter')::integer = 0 AND COALESCE((ad.extras_obj ->> 'wides')::integer, 0) = 0 THEN 1 ELSE 0 END AS is_dot_faced,
        CASE WHEN (ad.runs_obj ->> 'batter')::integer = 4 THEN 1 ELSE 0 END AS is_four,
        CASE WHEN (ad.runs_obj ->> 'batter')::integer = 6 THEN 1 ELSE 0 END AS is_six,
        CASE
            WHEN ad.wickets_array IS NOT NULL AND jsonb_array_length(ad.wickets_array) > 0 AND
                 (ad.wickets_array -> 0 ->> 'player_out') = ad.batter
            THEN 1 ELSE 0
        END AS is_dismissed
    FROM AllDeliveries ad
    WHERE ad.bowler IN (SELECT bowler FROM TopBowlers) -- Filter deliveries bowled by top bowlers
),
BatsmanAggregatedAgainstTop AS (
    -- Aggregate stats for batsmen against these top bowlers
    SELECT
        batter,
        SUM(runs_scored) AS total_runs,
        SUM(ball_faced) AS total_balls_faced,
        COUNT(DISTINCT bowler) AS distinct_top_bowlers_faced,
        SUM(is_dot_faced) AS dot_balls_faced,
        SUM(is_four) AS fours_scored,
        SUM(is_six) AS sixes_scored,
        SUM(is_four) + SUM(is_six) AS total_boundaries,
        SUM(is_dismissed) AS times_dismissed
    FROM BatsmanDeliveryDetailsAgainstTop
    GROUP BY batter
    HAVING
        COUNT(DISTINCT bowler) >= 10 AND  -- Faced at least 10 of the top 25 bowlers
        SUM(ball_faced) >= 200            -- Faced at least 200 balls cumulatively
),
PlayerAwards AS (
    -- Calculate Player of the Match awards for each player
    SELECT
        player_name,
        COUNT(*) AS awards_count
    FROM
        match_data,
        LATERAL jsonb_array_elements_text(match_details -> 'info' -> 'player_of_match') AS p(player_name)
    GROUP BY player_name
)
-- Final result: Top 25 batsmen
SELECT
    b.batter AS batsman_name,
    b.total_runs,
    b.total_balls_faced,
    ROUND((b.total_runs * 100.0 / NULLIF(b.total_balls_faced, 0)), 2) AS strike_rate,
    ROUND((b.total_runs * 1.0 / NULLIF(b.times_dismissed, 0)), 2) AS batting_average,
    b.total_boundaries,
    b.fours_scored,
    b.sixes_scored,
    b.times_dismissed,
    b.distinct_top_bowlers_faced,
    COALESCE(pa.awards_count, 0) AS potm_awards
FROM
    BatsmanAggregatedAgainstTop b
LEFT JOIN
    PlayerAwards pa ON b.batter = pa.player_name
ORDER BY
    b.total_runs DESC,
    strike_rate DESC NULLS LAST,
    batting_average DESC NULLS LAST,
    b.total_boundaries DESC,
    potm_awards DESC NULLS LAST
LIMIT 25;