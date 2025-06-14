-- Table: public.innings

-- DROP TABLE IF EXISTS public.innings;

CREATE TABLE IF NOT EXISTS public.innings
(
    inning_id integer NOT NULL DEFAULT nextval('innings_inning_id_seq'::regclass),
    match_id text COLLATE pg_catalog."default" NOT NULL,
    inning_number integer NOT NULL,
    batting_team_id integer NOT NULL,
    bowling_team_id integer NOT NULL,
    target_runs integer,
    target_overs text COLLATE pg_catalog."default",
    is_super_over boolean,
    CONSTRAINT innings_pkey PRIMARY KEY (inning_id),
    CONSTRAINT innings_match_id_inning_number_key UNIQUE (match_id, inning_number),
    CONSTRAINT innings_batting_team_id_fkey FOREIGN KEY (batting_team_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT innings_bowling_team_id_fkey FOREIGN KEY (bowling_team_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT innings_match_id_fkey FOREIGN KEY (match_id)
        REFERENCES public.matches (match_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.innings
    OWNER to postgres;

COMMENT ON TABLE public.innings
    IS 'The innings table represents an innings within the game of cricket. It contains the details of both the innings, such as the team batting, team bowling, target details if applicable';

COMMENT ON COLUMN public.innings.inning_number
    IS 'The sequence of the inning, eg. 1 or 2 etc';

COMMENT ON COLUMN public.innings.target_runs
    IS 'The target score set for the team batting';

COMMENT ON COLUMN public.innings.target_overs
    IS 'The target overs for the team batting';

COMMENT ON COLUMN public.innings.is_super_over
    IS 'A flag indicating if this inning was a super over. Note: Stats from the super overs are not considered generally for the player career stats or any other official purposes. Whenever joining innings table with any other table, by default, ALWAYS, ALWAYS filter out the super over innings in the final query, unless the query  specifically asks for considering super over stats.';