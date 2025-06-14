-- Table: public.matchofficialsassignment

-- DROP TABLE IF EXISTS public.matchofficialsassignment;

CREATE TABLE IF NOT EXISTS public.matchofficialsassignment
(
    match_official_assignment_id integer NOT NULL DEFAULT nextval('matchofficialsassignment_match_official_assignment_id_seq'::regclass),
    match_id text COLLATE pg_catalog."default" NOT NULL,
    official_identifier text COLLATE pg_catalog."default" NOT NULL,
    match_role text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT matchofficialsassignment_pkey PRIMARY KEY (match_official_assignment_id),
    CONSTRAINT matchofficialsassignment_match_id_official_identifier_match_key UNIQUE (match_id, official_identifier, match_role),
    CONSTRAINT matchofficialassignment_official_identifier_fkey FOREIGN KEY (official_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT matchofficialsassignment_match_id_fkey FOREIGN KEY (match_id)
        REFERENCES public.matches (match_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.matchofficialsassignment
    OWNER to postgres;

COMMENT ON TABLE public.matchofficialsassignment
    IS 'This junction table links officials (who are stored in the Players table) to the specific role they performed in a match.';

COMMENT ON COLUMN public.matchofficialsassignment.match_role
    IS 'The specific role in the match, e.g., umpire, tv_umpire, match_referee, reserve_umpire';