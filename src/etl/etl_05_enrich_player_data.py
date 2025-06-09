# src/etl/etl_05_enrich_player_data.py
import os
import time
import json
import psycopg2
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from psycopg2 import extras

from src import config
from src import db_utils

logger = logging.getLogger(__name__)

# List of valid bowling style abbreviations as discussed
VALID_BOWLING_STYLES = [
    "RF/RAF", "RFM/RAFM", "RMF/RAMF", "RM/RAM", "RMS/RAMS", "RSM/RASM", "RS/RAS", #Right arm fast bowling
    "LF/LAF", "LFM/LAFM", "LMF/LAMF", "LM/LAM", "LMS/LAMS", "LSM/LASM", "LS/LAS", #Left arm fast bowling
    "OB", "LB", "LBG", #Right arm spin bowling
    "SLA", "SLW", "LAG" #Left arm spin bowling
]


def build_enrichment_prompt(player_data: dict) -> str:
    """Constructs a detailed prompt to get player attributes from the AI."""

    # Provide all known context to help the AI find the correct player
    context = f"""
    - name: "{player_data.get('name')}"
    
    Details of the last IPL match played by the cricketer:
    - ipl season year: "{player_data.get('season_year')}"
    - last match date: "{player_data.get('last_match_date')}"
    - match: "{player_data.get('match')}"
    - venue: "{player_data.get('venue_name')}"
    - venue city: "{player_data.get('city')}"
    """

    # Define the rules and desired output format
    rules = f"""
    Based on the cricketer with the following details:
    {context}
    Provide the following missing information in a strict JSON format.
    1.  "batting_hand": Must be one of ["Right-hand bat", "Left-hand bat"].
    2.  "bowling_hand": Must be one of ["Right-arm", "Left-arm"].
    3.  "bowling_style": Must be one of the following exact abbreviations: {", ".join(VALID_BOWLING_STYLES)}.
    4.  "date_of_birth": Must be in "YYYY-MM-DD" format. If not found return '1900-01-01'.
    5.  "country": Country of origin of the cricketer. Must be a single country.
    6.  "player_role": Must be one of the ["Batsman", "Bowler", "All-rounder", "Wicket Keeper"]

    If a value is unknown or the player is not a bowler, return N/A for that key, but please provide the other keys.
    Only return the JSON object and nothing else.
    """
    return rules


def get_player_details_from_ai(player_data: dict) -> dict | None:
    """Queries the Gemini API with a prompt and returns a validated JSON object."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        prompt = build_enrichment_prompt(player_data)

        response = model.generate_content(prompt)

        # Clean the response to extract the JSON part
        json_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()

        enriched_data = json.loads(json_text)
        return enriched_data
    except json.JSONDecodeError:
        logger.error(f"AI returned malformed JSON for player {player_data.get('name')}: {response.text}")
        return None
    except Exception as e:
        logger.error(f"API call failed for player {player_data.get('name')}: {e}")
        return None


def run_ai_enrichment():
    """Finds players missing data and uses AI to enrich their records."""
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("ERROR: GOOGLE_API_KEY not found in .env file.")
        return
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    logger.info("Gemini API configured for enrichment.")

    conn = None
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor(cursor_factory=extras.DictCursor)

        # Find players from your query who need enrichment
        query = """
            WITH RankedMatches AS (
                -- First, join all the tables together and rank each player's matches by date
                SELECT
                    mp.player_identifier,
                    m.match_date,
                    m.season_year,
                    m.match_number,
                    v.venue_name,
                    v.city,
                    v.country,
                    concat(t1.team_name, ' v/s ', t2.team_name) as match_description,
                    ROW_NUMBER() OVER(PARTITION BY mp.player_identifier ORDER BY m.match_date DESC, m.match_id DESC) as rn
                FROM MatchPlayers mp
                JOIN Matches m ON mp.match_id = m.match_id
                JOIN venues v on m.venue_id = v.venue_id
                JOIN teams t1 on m.team1_id = t1.team_id
                JOIN teams t2 on m.team2_id = t2.team_id
                )
                -- Now, select from your players table and join to the ranked matches
            SELECT
                p.identifier,
                p.name,
                p.unique_name,
                rm.country, -- Added country from your original query's intent
                rm.match_date as last_match_date,
                rm.season_year as last_season_year,
                rm.match_number as last_match_number,
                rm.venue_name as last_venue_name,
                rm.city as last_city,
                rm.match_description as last_match_played
            FROM
                players p
            JOIN RankedMatches rm ON p.identifier = rm.player_identifier
            WHERE
                -- This is the key: only select the #1 ranked match for each player
                rm.rn = 1
                -- This condition still finds players who are missing the data we want to enrich
                AND (p.batting_hand IS NULL OR p.bowling_hand IS NULL OR p.player_role IS NULL OR p.bowling_style IS NULL OR p.date_of_birth IS NULL OR p.country IS NULL)
            LIMIT 50;
        """
        cursor.execute(query)
        players_to_enrich = cursor.fetchall()

        total_players = len(players_to_enrich)
        if total_players == 0:
            logger.info("No players found requiring AI enrichment.")
            return

        logger.info(f"Found {total_players} players to enrich with AI...")

        for i, player_row in enumerate(players_to_enrich):
            player_dict = dict(player_row)
            logger.info(
                f"Processing player {i + 1}/{total_players}: {player_dict.get('name')} ({player_dict.get('identifier')})")

            enriched_data = get_player_details_from_ai(player_dict)

            if enriched_data:
                # Update the player record in the database
                update_query = """
                    UPDATE Players SET
                        batting_hand = COALESCE(%(batting_hand)s, batting_hand),
                        bowling_hand = COALESCE(%(bowling_hand)s, bowling_hand),
                        bowling_style = COALESCE(%(bowling_style)s, bowling_style),
                        date_of_birth = COALESCE(%(date_of_birth)s, date_of_birth),
                        country = COALESCE(%(country)s, country),
                        player_role = COALESCE(%(player_role)s, player_role)
                    WHERE identifier = %(id)s;
                """
                cursor.execute(update_query, {
                    'batting_hand': enriched_data.get('batting_hand'),
                    'bowling_hand': enriched_data.get('bowling_hand'),
                    'bowling_style': enriched_data.get('bowling_style'),
                    'date_of_birth': enriched_data.get('date_of_birth'),
                    'country': enriched_data.get('country'),
                    'player_role': enriched_data.get('player_role'),
                    'id': player_dict['identifier']
                })
                logger.info(f"Successfully updated player: {player_dict.get('name')}")
            else:
                logger.warning(f"Failed to get or parse AI data for player: {player_dict.get('name')}")

            # Must add a delay to respect API rate limits
            time.sleep(5)  # 1 request every 2 seconds = 30 requests/minute

        # AI is not reliable sometimes
        cursor.execute("""
        UPDATE Players
            SET bowling_style = CASE
                WHEN bowling_style in ('RF', 'RAF') THEN 'RF/RAF'
                WHEN bowling_style in ('RFM', 'RAFM') THEN 'RFM/RAMF'
                WHEN bowling_style in ('RMF', 'RAMF') THEN 'RMF/RAMF'
                WHEN bowling_style in ('RM', 'RAM') THEN 'RM/RAM'
                WHEN bowling_style in ('RMS', 'RAMS') THEN 'RMS/RAMS'
                WHEN bowling_style in ('RSM', 'RASM') THEN 'RSM/RASM'
                WHEN bowling_style in ('RS', 'RAS') THEN 'RS/RAS'
                WHEN bowling_style in ('LF', 'LAF') THEN 'LF/LAF'
                WHEN bowling_style in ('LFM', 'LAFM') THEN 'LFM/LAMF'
                WHEN bowling_style in ('LMF', 'LAMF') THEN 'LMF/LAMF'
                WHEN bowling_style in ('LM', 'LAM') THEN 'LM/LAM'
                WHEN bowling_style in ('LMS', 'LAMS') THEN 'LMS/LAMS'
                WHEN bowling_style in ('LSM', 'LASM') THEN 'LSM/LASM'
                WHEN bowling_style in ('LS', 'LAS') THEN 'LS/LAS'
                ELSE bowling_style
            END
        """)
        conn.commit()
        logger.info("AI enrichment process finished successfully.")

    except (Exception, psycopg2.Error) as error:
        logger.error("A critical error occurred during the AI enrichment process.", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
            logger.info("PostgreSQL connection for AI enrichment is closed.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    run_ai_enrichment()