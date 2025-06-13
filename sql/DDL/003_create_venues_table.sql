-- Table: public.venues

-- DROP TABLE IF EXISTS public.venues;

CREATE TABLE IF NOT EXISTS public.venues
(
    venue_id integer NOT NULL DEFAULT nextval('venues_venue_id_seq'::regclass),
    venue_name text COLLATE pg_catalog."default" NOT NULL,
    city text COLLATE pg_catalog."default",
    country text COLLATE pg_catalog."default",
    longitude double precision,
    latitude double precision,
    CONSTRAINT venues_pkey PRIMARY KEY (venue_id),
    CONSTRAINT venues_venue_name_key UNIQUE (venue_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.venues
    OWNER to postgres;

COMMENT ON TABLE public.venues
    IS 'This table is a master list of all unique match venues (stadiums/grounds)';

COMMENT ON COLUMN public.venues.venue_id
    IS 'The unique ID generated for a venue';

COMMENT ON COLUMN public.venues.venue_name
    IS 'The name of the venue, e.g., M Chinnaswamy Stadium';

COMMENT ON COLUMN public.venues.city
    IS 'The city in which the venue is located';

COMMENT ON COLUMN public.venues.country
    IS 'The country in which the venue is located.';

COMMENT ON COLUMN public.venues.longitude
    IS 'The geographic longitude of the venue';

COMMENT ON COLUMN public.venues.latitude
    IS 'The geographic latitude of the venue';