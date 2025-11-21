-- Table: public.inningstimings

-- DROP TABLE IF EXISTS public.inningstimings;

CREATE TABLE IF NOT EXISTS public.inningstimings
(
    inning_id integer NOT NULL,
    total_duration_minutes integer,
    playing_duration_minutes integer,
    scheduled_starttime_utc timestamp with time zone,
    actual_starttime_utc timestamp with time zone,
    actual_endtime_utc timestamp with time zone,
    CONSTRAINT inningstimings_pkey PRIMARY KEY (inning_id),
    CONSTRAINT inningstimings_inning_id_fkey FOREIGN KEY (inning_id)
        REFERENCES public.innings (inning_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.inningstimings
    OWNER to postgres;

COMMENT ON TABLE public.inningstimings
    IS 'This table stores the high-level timing and duration for each innings of a match.';

COMMENT ON COLUMN public.inningstimings.inning_id
    IS 'Foreign Key to the Innings table, representing one innings.';

COMMENT ON COLUMN public.inningstimings.total_duration_minutes
    IS 'The total duration of the innings in minutes, including any delays.';

COMMENT ON COLUMN public.inningstimings.playing_duration_minutes
    IS 'The actual duration of the innings in minutes, excluding all delays.';

COMMENT ON COLUMN public.inningstimings.scheduled_starttime_utc
    IS 'The originally scheduled start time of the innings in UTC.';

COMMENT ON COLUMN public.inningstimings.actual_starttime_utc
    IS 'The actual time the first ball was bowled in UTC.';

COMMENT ON COLUMN public.inningstimings.actual_endtime_utc
    IS 'The actual time the final ball was bowled in UTC.';