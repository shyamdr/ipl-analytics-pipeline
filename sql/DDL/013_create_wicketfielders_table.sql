-- Table: public.wicketfielders

-- DROP TABLE IF EXISTS public.wicketfielders;

CREATE TABLE IF NOT EXISTS public.wicketfielders
(
    wicket_fielder_id integer NOT NULL DEFAULT nextval('wicketfielders_wicket_fielder_id_seq'::regclass),
    wicket_id bigint NOT NULL,
    fielder_player_identifier text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT wicketfielders_pkey PRIMARY KEY (wicket_fielder_id),
    CONSTRAINT wicketfielders_wicket_id_fielder_player_identifier_key UNIQUE (wicket_id, fielder_player_identifier),
    CONSTRAINT wicketfielders_wicket_id_fkey FOREIGN KEY (wicket_id)
        REFERENCES public.wickets (wicket_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT wicketsfields_fielder_player_identifier_fkey FOREIGN KEY (fielder_player_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.wicketfielders
    OWNER to postgres;

COMMENT ON TABLE public.wicketfielders
    IS 'This junction table links fielders to a specific wicket they were involved in (e.g., as a catcher or in a run out).';