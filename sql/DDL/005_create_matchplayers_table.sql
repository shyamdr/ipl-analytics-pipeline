-- Table: public.matchplayers

-- DROP TABLE IF EXISTS public.matchplayers;

CREATE TABLE IF NOT EXISTS public.matchplayers
(
    match_player_id integer NOT NULL DEFAULT nextval('matchplayers_match_player_id_seq'::regclass),
    match_id text COLLATE pg_catalog."default" NOT NULL,
    player_identifier text COLLATE pg_catalog."default" NOT NULL,
    team_id integer NOT NULL,
    is_captain boolean DEFAULT false,
    is_wicket_keeper boolean DEFAULT false,
    CONSTRAINT matchplayers_pkey PRIMARY KEY (match_player_id),
    CONSTRAINT matchplayers_match_id_player_identifier_key UNIQUE (match_id, player_identifier),
    CONSTRAINT matchplayers_match_id_fkey FOREIGN KEY (match_id)
        REFERENCES public.matches (match_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT matchplayers_player_identifier_fkey FOREIGN KEY (player_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT matchplayers_team_id_fkey FOREIGN KEY (team_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.matchplayers
    OWNER to postgres;

COMMENT ON TABLE public.matchplayers
    IS 'This junction table lists every player who participated in a specific match (i.e., the playing XI for each team).';

COMMENT ON COLUMN public.matchplayers.is_captain
    IS 'A flag indicating if this player was the captain for this match. Currently there is no data present for this field, hence do not use in analysis.';

COMMENT ON COLUMN public.matchplayers.is_wicket_keeper
    IS 'A flag indicating if this player was the wicket-keeper for this match. Currently there is no data present for this field, hence do not use in analysis.';