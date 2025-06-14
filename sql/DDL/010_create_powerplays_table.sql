-- Table: public.powerplays

-- DROP TABLE IF EXISTS public.powerplays;

CREATE TABLE IF NOT EXISTS public.powerplays
(
    powerplay_id integer NOT NULL DEFAULT nextval('powerplays_powerplay_id_seq'::regclass),
    inning_id integer NOT NULL,
    type text COLLATE pg_catalog."default" NOT NULL,
    from_over numeric(3,1) NOT NULL,
    to_over numeric(3,1) NOT NULL,
    CONSTRAINT powerplays_pkey PRIMARY KEY (powerplay_id),
    CONSTRAINT powerplays_inning_id_fkey FOREIGN KEY (inning_id)
        REFERENCES public.innings (inning_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.powerplays
    OWNER to postgres;

COMMENT ON TABLE public.powerplays
    IS 'This table defines the powerplay phases (e.g., mandatory) for an inning.';

COMMENT ON COLUMN public.powerplays.type
    IS 'The type of powerplay, e.g., mandatory, batting, bowling etc';

COMMENT ON COLUMN public.powerplays.from_over
    IS 'The start of the powerplay, e.g., 0.1 for the first ball';

COMMENT ON COLUMN public.powerplays.to_over
    IS 'The end of the powerplay, e.g., 5.6 for the end of the sixth over';