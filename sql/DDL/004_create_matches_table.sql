-- Table: public.matches

-- DROP TABLE IF EXISTS public.matches;

CREATE TABLE IF NOT EXISTS public.matches
(
    match_id text COLLATE pg_catalog."default" NOT NULL,
    season_year integer NOT NULL,
    match_date date,
    event_name text COLLATE pg_catalog."default",
    match_number integer,
    venue_id integer,
    team1_id integer,
    team2_id integer,
    toss_winner_team_id integer,
    toss_decision text COLLATE pg_catalog."default",
    outcome_winner_team_id integer,
    outcome_type text COLLATE pg_catalog."default",
    outcome_margin integer,
    match_type text COLLATE pg_catalog."default",
    overs_limit integer,
    balls_per_over integer,
    CONSTRAINT matches_pkey PRIMARY KEY (match_id),
    CONSTRAINT matches_outcome_winner_team_id_fkey FOREIGN KEY (outcome_winner_team_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT matches_team1_id_fkey FOREIGN KEY (team1_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT matches_team2_id_fkey FOREIGN KEY (team2_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT matches_toss_winner_team_id_fkey FOREIGN KEY (toss_winner_team_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT matches_venue_id_fkey FOREIGN KEY (venue_id)
        REFERENCES public.venues (venue_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT fk_team1_match CHECK (team1_id IS NULL OR team1_id <> team2_id),
    CONSTRAINT fk_team2_match CHECK (team2_id IS NULL OR team1_id <> team2_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.matches
    OWNER to postgres;

COMMENT ON TABLE public.matches
    IS 'This is a central fact table containing metadata for each match.';

COMMENT ON COLUMN public.matches.match_id
    IS ' The unique ID for the match, derived from the filename';

COMMENT ON COLUMN public.matches.season_year
    IS 'The starting year of the tournament season, e.g., 2023';

COMMENT ON COLUMN public.matches.match_date
    IS 'Date when the match was played in YYYY-MM-DD format';

COMMENT ON COLUMN public.matches.event_name
    IS 'The name of the event the match took place in.';

COMMENT ON COLUMN public.matches.match_number
    IS 'The match number of the match. This might indicate that it was the 3rd match of a series, or the 19th match of a competition. (e.g., 1, 2, ... 74)';

COMMENT ON COLUMN public.matches.toss_decision
    IS 'The decision made by the team winning the toss. This will be either bat or field.';

COMMENT ON COLUMN public.matches.outcome_type
    IS 'The method of victory, e.g., wickets, runs, tie';

COMMENT ON COLUMN public.matches.outcome_margin
    IS 'The margin of victory, e.g., 6 (for wickets) or 20 (for runs)';

COMMENT ON COLUMN public.matches.match_type
    IS 'The type of match this match refers to. Currently the possible values are Test, ODI, T20, IT20 (International T20), ODM (One-day match) or MDM (multi-day match).';

COMMENT ON COLUMN public.matches.balls_per_over
    IS 'The number of balls expected per over, generally 6.';