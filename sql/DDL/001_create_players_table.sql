-- Table: public.players

-- DROP TABLE IF EXISTS public.players;

CREATE TABLE IF NOT EXISTS public.players
(
    identifier text COLLATE pg_catalog."default" NOT NULL,
    name text COLLATE pg_catalog."default",
    unique_name text COLLATE pg_catalog."default",
    key_cricinfo text COLLATE pg_catalog."default",
    batting_hand text COLLATE pg_catalog."default",
    bowling_hand text COLLATE pg_catalog."default",
    player_role text COLLATE pg_catalog."default",
    date_of_birth date,
    country text COLLATE pg_catalog."default",
    bowling_style text COLLATE pg_catalog."default",
    full_name text COLLATE pg_catalog."default",
    CONSTRAINT players_pkey PRIMARY KEY (identifier)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.players
    OWNER to postgres;

COMMENT ON TABLE public.players
    IS 'This table is a master list of all players and officials(umpires/referees)';

COMMENT ON COLUMN public.players.identifier
    IS 'The globally unique ID for the person from people.csv';

COMMENT ON COLUMN public.players.name
    IS 'The player''s common name, e.g., V Kohli';

COMMENT ON COLUMN public.players.unique_name
    IS 'A unique name variant, often for disambiguation, e.g in case multiple players have same name field';

COMMENT ON COLUMN public.players.key_cricinfo
    IS 'The player''s ID from ESPNCricinfo, used for scraping URLs';

COMMENT ON COLUMN public.players.batting_hand
    IS 'The player''s batting hand, e.g ''Right'' if Right handed batsman, ''Left'' if Left handed batsman, could be null or N/A in case information is not available';

COMMENT ON COLUMN public.players.bowling_hand
    IS 'The player''s bowling arm eg. Left or Right';

COMMENT ON COLUMN public.players.player_role
    IS 'The player''s primary role, e.g., Batsman, All-rounder, Bowler, Wicket keeper etc';

COMMENT ON COLUMN public.players.date_of_birth
    IS 'The player''s date of birth in YYYY-MM-DD format';

COMMENT ON COLUMN public.players.country
    IS 'The player''s country of origin';

COMMENT ON COLUMN public.players.bowling_style
    IS 'Abbreviation for the specific bowling style, These are the possible values:
	RF/RAF means Right arm fast (fast/pace);
	RFM/RAFM means Right arm fast medium (fast/pace);
	RMF/RAMF means Right arm medium fast (fast/pace);
	RM/RAM means Right arm medium (fast/pace);
	RMS/RAMS means Right arm medium slow (fast/pace);
	RS/RAS means Right arm slow (fast/pace);
	LF/LAF means Left arm fast (fast/pace);
	LFM/LAFM means Left arm fast medium (fast/pace);
	LMF/LAMF means Left arm medium fast (fast/pace);
	LM/LAM means Left arm medium (fast/pace);
	LMS/LAMS means Left arm medium slow (fast/pace);
	LS/LAS means Left arm slow (fast/pace);
	OB means Right arm Off break (slow/spin);
	LB means Right arm Leg break(slow/spin);
	LBG means Right arm Leg break Googly (slow/spin);
	SLA means Slow left arm orthodox (slow/spin);
	SLW means Slow left arm wrist spin (slow/spin);
	LAG means Left arm googly (slow/spin);
	Otherwise it could be null or N/A if data is not available';

COMMENT ON COLUMN public.players.full_name
    IS 'The player''s full name';