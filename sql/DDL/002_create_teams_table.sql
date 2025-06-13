-- Table: public.teams

-- DROP TABLE IF EXISTS public.teams;

CREATE TABLE IF NOT EXISTS public.teams
(
    team_id integer NOT NULL DEFAULT nextval('teams_team_id_seq'::regclass),
    team_name text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT teams_pkey PRIMARY KEY (team_id),
    CONSTRAINT teams_team_name_key UNIQUE (team_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.teams
    OWNER to postgres;

COMMENT ON TABLE public.teams
    IS 'This table is a master list of all unique team names.';

COMMENT ON COLUMN public.teams.team_id
    IS 'The unique ID generated for a team';

COMMENT ON COLUMN public.teams.team_name
    IS 'The full official name of the team, e.g., Chennai Super Kings';