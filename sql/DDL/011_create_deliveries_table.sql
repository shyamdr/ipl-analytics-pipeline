-- Table: public.deliveries

-- DROP TABLE IF EXISTS public.deliveries;

CREATE TABLE IF NOT EXISTS public.deliveries
(
    delivery_id bigint NOT NULL DEFAULT nextval('deliveries_delivery_id_seq'::regclass),
    inning_id integer NOT NULL,
    over_number integer NOT NULL,
    ball_number_in_over integer NOT NULL,
    batter_identifier text COLLATE pg_catalog."default" NOT NULL,
    bowler_identifier text COLLATE pg_catalog."default" NOT NULL,
    non_striker_identifier text COLLATE pg_catalog."default" NOT NULL,
    runs_batter integer NOT NULL,
    runs_extras integer NOT NULL,
    runs_non_boundary boolean,
    runs_total integer NOT NULL,
    extras_wides integer DEFAULT 0,
    extras_noballs integer DEFAULT 0,
    extras_byes integer DEFAULT 0,
    extras_legbyes integer DEFAULT 0,
    extras_penalty integer DEFAULT 0,
    raw_extras_json jsonb,
    raw_review_json jsonb,
    CONSTRAINT deliveries_pkey PRIMARY KEY (delivery_id),
    CONSTRAINT deliveries_batter_identifier_fkey FOREIGN KEY (batter_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT deliveries_bowler_identifier_fkey FOREIGN KEY (bowler_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT deliveries_inning_id_fkey FOREIGN KEY (inning_id)
        REFERENCES public.innings (inning_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT deliveries_non_striker_identifier_fkey FOREIGN KEY (non_striker_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.deliveries
    OWNER to postgres;

COMMENT ON TABLE public.deliveries
    IS 'This is a central fact table containing metadata containing ball-by-ball event data for each inning of each match. This is the most granular and detailed table for analysis.';

COMMENT ON COLUMN public.deliveries.over_number
    IS 'The over number in the inning, usually 0-19 for T20 matches. Accordingly for ODI or other matches';

COMMENT ON COLUMN public.deliveries.ball_number_in_over
    IS 'The sequence of the ball within that over (e.g., 1, 2, 3...). Every ball, legal and illegal is counted towards it for example an over with 6 legal deliveries and 1 illegal delivery such as a wide delivery will consist of values from 0-7.';

COMMENT ON COLUMN public.deliveries.runs_batter
    IS 'Runs scored by the batter directly off the bat. (Counted towards batsman''s tally of runs)';

COMMENT ON COLUMN public.deliveries.runs_extras
    IS 'Runs scored as extras (from wides, no-balls, leg-byes, byes etc.). (Not counted towards batsman''s tally of runs)';

COMMENT ON COLUMN public.deliveries.runs_non_boundary
    IS 'If this value is True, This indicates that the 4 or 6 scored was not via an actual boundary(4 or a 6), for example it was all run by running between the wickets, or overthrows.';

COMMENT ON COLUMN public.deliveries.runs_total
    IS 'Total runs on this delivery (equal to runs_batter + runs_extras).';

COMMENT ON COLUMN public.deliveries.extras_wides
    IS 'The number of runs from wides on this delivery.';

COMMENT ON COLUMN public.deliveries.extras_noballs
    IS 'The number of runs from no-balls on this delivery.';

COMMENT ON COLUMN public.deliveries.extras_byes
    IS 'The number of byes on this delivery.';

COMMENT ON COLUMN public.deliveries.extras_legbyes
    IS 'The number of leg-byes on this delivery.';

COMMENT ON COLUMN public.deliveries.extras_penalty
    IS 'Any penalty runs awarded on this delivery.';

COMMENT ON COLUMN public.deliveries.raw_extras_json
    IS 'Note : This column should not be used for analytical purposes, as ths field is the priginal raw object from upstream data source, the same data is distributed in the individual fields such as ''extras_byes'' for information on ''byes'' for the particular delivery. Use, those fields instead. This column is the original JSON object for extras, for detailed analysis. If extras were conceded on a delivery then this field will indicate how the extras came about. The value of the field will be an object with byes, legbyes, noballs, penalty, and wides as the possible keys, and the associated value for each will be the number of runs from each.';

COMMENT ON COLUMN public.deliveries.raw_review_json
    IS 'The original JSON object for a player review (DRS), if one occurred. Details on any review that took place as part of the delivery, contains fields : ''batter'' - The name of the batter for whom the decision was reviewed; ''by'' - The name of the team that called for the review; ''decision'' - The decision made following the review. This will be one of ''struck down'', or ''upheld''; ''umpire'' - The name of the umpire who''s decision was reviewed; ''umpires_call'' - If a review was struck down due to it being down to the umpires call this field will be true.';