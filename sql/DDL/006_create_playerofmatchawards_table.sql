-- Table: public.playerofmatchawards

-- DROP TABLE IF EXISTS public.playerofmatchawards;

CREATE TABLE IF NOT EXISTS public.playerofmatchawards
(
    award_id integer NOT NULL DEFAULT nextval('playerofmatchawards_award_id_seq'::regclass),
    match_id text COLLATE pg_catalog."default" NOT NULL,
    player_identifier text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT playerofmatchawards_pkey PRIMARY KEY (award_id),
    CONSTRAINT playerofmatchawards_match_id_fkey FOREIGN KEY (match_id)
        REFERENCES public.matches (match_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT playerofmatchawards_player_identifier_fkey FOREIGN KEY (player_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.playerofmatchawards
    OWNER to postgres;

COMMENT ON TABLE public.playerofmatchawards
    IS 'This junction table lists every player who participated in a specific match (i.e., the playing XI for each team).';