-- Table: public.replacements

-- DROP TABLE IF EXISTS public.replacements;

CREATE TABLE IF NOT EXISTS public.replacements
(
    replacement_id integer NOT NULL DEFAULT nextval('replacements_replacement_id_seq'::regclass),
    match_id text COLLATE pg_catalog."default" NOT NULL,
    delivery_id bigint,
    inning_id integer,
    team_id integer,
    replacement_type text COLLATE pg_catalog."default" NOT NULL,
    replaced_role text COLLATE pg_catalog."default",
    player_in_identifier text COLLATE pg_catalog."default" NOT NULL,
    player_out_identifier text COLLATE pg_catalog."default",
    reason text COLLATE pg_catalog."default",
    CONSTRAINT replacements_pkey PRIMARY KEY (replacement_id),
    CONSTRAINT replacements_delivery_id_fkey FOREIGN KEY (delivery_id)
        REFERENCES public.deliveries (delivery_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT replacements_inning_id_fkey FOREIGN KEY (inning_id)
        REFERENCES public.innings (inning_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT replacements_match_id_fkey FOREIGN KEY (match_id)
        REFERENCES public.matches (match_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT replacements_player_in_identifier_fkey FOREIGN KEY (player_in_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT replacements_player_out_identifier_fkey FOREIGN KEY (player_out_identifier)
        REFERENCES public.players (identifier) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT replacements_team_id_fkey FOREIGN KEY (team_id)
        REFERENCES public.teams (team_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.replacements
    OWNER to postgres;

COMMENT ON TABLE public.replacements
    IS 'Tracks player substitutions during a match (e.g., Impact Players, concussion subs). It provides the details of any replacements that happened before this delivery took place. It shows who was substituted in and out, why, and which team it was for, as well as what type of replacement it is, match or role. These different types are grouped together within the replacements section, and it’s possible that a delivery could have both types.';

COMMENT ON COLUMN public.replacements.delivery_id
    IS 'The specific delivery when the substitution occurred.';

COMMENT ON COLUMN public.replacements.team_id
    IS 'The team making the replacement (NULL for role changes).';

COMMENT ON COLUMN public.replacements.replacement_type
    IS 'The type of replacement, either ''match'' or ''role''.';

COMMENT ON COLUMN public.replacements.replaced_role
    IS 'The specific role being replaced, e.g., ''bowler''.';

COMMENT ON COLUMN public.replacements.player_out_identifier
    IS 'The player being replaced (can be NULL).';

COMMENT ON COLUMN public.replacements.reason
    IS 'The reason for the substitution.';