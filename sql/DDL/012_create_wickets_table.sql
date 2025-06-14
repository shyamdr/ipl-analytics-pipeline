-- Table: public.wickets

-- DROP TABLE IF EXISTS public.wickets;

CREATE TABLE IF NOT EXISTS public.wickets
(
    wicket_id bigint NOT NULL DEFAULT nextval('wickets_wicket_id_seq'::regclass),
    delivery_id bigint NOT NULL,
    player_out_identifier text COLLATE pg_catalog."default" NOT NULL,
    kind text COLLATE pg_catalog."default" NOT NULL,
    bowler_credited_identifier text COLLATE pg_catalog."default",
    CONSTRAINT wickets_pkey PRIMARY KEY (wicket_id),
    CONSTRAINT wickets_bowler_credited_identifier_fkey FOREIGN KEY (bowler_credited_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT wickets_delivery_id_fkey FOREIGN KEY (delivery_id)
        REFERENCES public.deliveries (delivery_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT wickets_player_out_identifier_fkey FOREIGN KEY (player_out_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.wickets
    OWNER to postgres;

COMMENT ON TABLE public.wickets
    IS 'This is a central fact table containing metadata containing ball-by-ball event data for each inning of each match. This is the most granular and detailed table for analysis.';

COMMENT ON COLUMN public.wickets.kind
    IS 'The method of dismissal, e.g., "retired out", "retired hurt", "caught", "bowled", "caught and bowled", "run out", "stumped", "lbw", "obstructing the field", "hit wicket"';

COMMENT ON COLUMN public.wickets.bowler_credited_identifier
    IS 'The bowler credited with the wicket (NULL for run outs, etc.)';