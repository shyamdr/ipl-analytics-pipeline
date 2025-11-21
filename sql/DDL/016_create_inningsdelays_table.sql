-- Table: public.inningsdelays

-- DROP TABLE IF EXISTS public.inningsdelays;

CREATE TABLE IF NOT EXISTS public.inningsdelays
(
    delay_id SERIAL NOT NULL,
    inning_id integer NOT NULL,
    reason text COLLATE pg_catalog."default",
    start_time_utc timestamp with time zone,
    resume_time_utc timestamp with time zone,
    duration_minutes integer,
    overs_completed integer,
    CONSTRAINT inningsdelays_pkey PRIMARY KEY (delay_id),
    CONSTRAINT inningsdelays_inning_id_fkey FOREIGN KEY (inning_id)
        REFERENCES public.innings (inning_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.inningsdelays
    OWNER to postgres;

COMMENT ON TABLE public.inningsdelays
    IS 'This table stores every individual delay event that occurred during an innings.';

COMMENT ON COLUMN public.inningsdelays.delay_id
    IS 'The unique ID for each specific delay event.';

COMMENT ON COLUMN public.inningsdelays.inning_id
    IS 'Foreign Key to the Innings table, indicating which innings the delay occurred in.';

COMMENT ON COLUMN public.inningsdelays.reason
    IS 'The cause of the delay, e.g., ''Rain'', ''Bad Light'', ''Injury''.';

COMMENT ON COLUMN public.inningsdelays.start_time_utc
    IS 'The time in UTC when the delay started.';

COMMENT ON COLUMN public.inningsdelays.resume_time_utc
    IS 'The time in UTC when the play resumed after the delay.';

COMMENT ON COLUMN public.inningsdelays.duration_minutes
    IS 'The total duration of this specific delay in minutes.';

COMMENT ON COLUMN public.inningsdelays.overs_completed
    IS 'The number of overs completed in the innings when the delay occurred.';