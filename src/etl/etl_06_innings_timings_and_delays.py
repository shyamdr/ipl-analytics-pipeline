# src/etl/etl_06_innings_timings_and_delays.py

import os
import time
import json
import psycopg2
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from psycopg2 import extras
from datetime import datetime, timezone, date

from src import config
from src import db_utils

logger = logging.getLogger(__name__)


# --- Helper Functions for AI Interaction ---

def build_prompt_for_matches(matches_details: list[dict]) -> str:
    """
    Constructs a detailed prompt for the AI to find match timings and delays for a batch of matches.
    """
    matches_details_serializable = []
    for match in matches_details:
        match_copy = match.copy()  # Avoid modifying the original dict
        if isinstance(match_copy.get('match_date_played'), (date, datetime)):
            match_copy['match_date_played'] = match_copy['match_date_played'].isoformat()
        matches_details_serializable.append(match_copy)

    match_list_str = json.dumps(matches_details_serializable, indent=2)

    # Define the output JSON array structure that the AI MUST conform to
    json_structure_template = f"""
    [
      {{
        "match_id": "string",
        "season_year": "integer",
        "match_date_played": "string",
        "venue_name": "string",
        "team1": "string",
        "team2": "string",
        "innings_1": {{
          "inning_id": "integer",
          "total_duration_minutes": "integer",
          "playing_duration_minutes": "integer",
          "actual_starttime_utc": "string", // 'HH:MM:SS'
          "actual_endtime_utc": "string",
          "scheduled_starttime_utc": "string",
          "delays": [ // An array of delay objects.
            {{
              "reason": "string",
              "start_time_utc": "string",
              "resume_time_utc": "string",
              "duration_minutes": "integer",
              "overs_completed": "number"
            }}
          ]
        }},
        "innings_2": {{
          "inning_id": "integer",
          "total_duration_minutes": "integer",
          "playing_duration_minutes": "integer",
          "actual_starttime_utc": "string",
          "actual_endtime_utc": "string",
          "scheduled_starttime_utc": "string",
          "delays": [
            {{
              "reason": "string",
              "start_time_utc": "string",
              "resume_time_utc": "string",
              "duration_minutes": "integer",
              "overs_completed": "number"
            }}
          ]
        }}
      }},
      {{ ... (for other matches) ... }}
    ]
    """

    # Construct the full prompt
    prompt = f"""
    Role and Goal:
    You are an expert cricket data analyst AI. Your task is to analyze a batch of cricket matches and provide a detailed, \
    innings-level timeline for each. You must consult detailed, ball-by-ball cricket archives and commentaries to find the actual \
    event times, including any mid-innings delays.

    Input Match Details:
    I will provide you with a JSON array of matches to process. You must process each of them.

    Match Details JSON Array:
    {match_list_str}

    Output Requirements:
    The output MUST be a single JSON array object that strictly conforms to the following structure and its field \
    definitions. The array should contain a JSON object for each match provided in the input. Ensure all timestamps \
    in the output are in 'HH:MM:SS' format.
    Note : Rain, fog, bad weather or something catastropic should be counted as delays, known breaks in the match such \
    as timeout or player replacement due to a injury doesnt  count as delay unless it really doesnt take a lot of time like more than 15-20 minutes

    JSON Structure Template:
    {json_structure_template}

    Task:
    Now, generate the JSON output as defined above for the input matches.
    """

    prompt2 = f"""
    Role and Goal:
    You are a meticulous data extraction AI. Your task is to find a specific, authoritative public source for a cricket \
    match and then, based only on the information in that source, populate a detailed JSON timeline.
    
    Process:
    You must follow this two-step process for each match:
    Step 1 (Find Source): First, find the most authoritative public scorecard and commentary for the match (preferably from ESPNcricinfo).
    Step 2 (Extract Data): Second, using only the information from that specific source, generate the JSON output. If the source does not contain information for a field, use null
    
    Match Details JSON Array:
    {match_list_str}
    
    Output Requirements:
    The output MUST be a single JSON array object that strictly conforms to the following structure and its field \
    definitions. The array should contain a JSON object for each match provided in the input. Ensure all timestamps \
    in the output are in 'HH:MM:SS' format.

    JSON Structure Template:
    {json_structure_template}

    Task:
    Now, generate the JSON output as defined above for the input matches. In cases where the data is not available, try \
    to guess atleast the scheduled start time of the match unless if you can guess it with atleast 90% confidence
    """

    return prompt2


def get_match_timings_from_ai(matches_details: list[dict]) -> list[dict] | None:
    """
    Queries the Gemini API with a prompt to get match timings and delays for a batch of matches.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        prompt = build_prompt_for_matches(matches_details)

        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0))

        log_file_path = os.path.join("logs", "ai_responses.log")
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, "a") as log_file:
            log_file.write("--- NEW RESPONSE ---\n")
            log_file.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
            log_file.write(f"Prompt: {prompt}\n")
            log_file.write(f"Response: {response.text}\n\n")

        # Clean the response to extract the JSON part
        json_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()

        enriched_data = json.loads(json_text)
        if not isinstance(enriched_data, list):
            raise TypeError("AI did not return a JSON array as expected.")

        return enriched_data
    except json.JSONDecodeError:
        logger.error(f"AI returned malformed JSON for batch of matches: {response.text}")
        return None
    except Exception as e:
        logger.error(f"API call failed for batch of matches: {e}")
        return None


# --- Main ETL Function ---

def run_ai_enrichment_match_timings():
    """
    Finds matches missing timing data and uses AI to enrich their records in a batch.
    """
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

        # Find matches that are missing timing data
        query_matches_to_enrich = """
        SELECT
            m.match_id,
            m.season_year,
            m.match_date AS match_date_played,
            v.venue_name,
            t1.team_name AS team1,
            t2.team_name AS team2,
            i1.inning_id AS inning_1_id,
            i2.inning_id AS inning_2_id
        FROM Matches m
        JOIN Venues v ON m.venue_id = v.venue_id
        JOIN Teams t1 ON m.team1_id = t1.team_id
        JOIN Teams t2 ON m.team2_id = t2.team_id
        JOIN Innings i1 ON m.match_id = i1.match_id AND i1.inning_number = 1
        JOIN Innings i2 ON m.match_id = i2.match_id AND i2.inning_number = 2
        -- Only select matches that are missing timing data for inning 1
        LEFT JOIN InningsTimings it1 ON i2.inning_id = it1.inning_id
        WHERE it1.inning_id IS NULL OR scheduled_starttime_utc IS NULL
        ORDER BY m.season_year DESC, m.match_date DESC
        LIMIT 100; -- Process in batches of 30
        """
        cursor.execute(query_matches_to_enrich)
        matches_to_enrich = cursor.fetchall()

        total_matches = len(matches_to_enrich)
        if total_matches == 0:
            logger.info("No matches found requiring AI enrichment.")
            return

        logger.info(f"Found {total_matches} matches to enrich with AI...")
        logger.info(f"Making a single API call for the batch...")

        enriched_data_list = get_match_timings_from_ai(matches_to_enrich)

        if enriched_data_list:
            for enriched_match in enriched_data_list:
                match_id = enriched_match.get('match_id')
                match_date_str = enriched_match.get('match_date_played')

                # --- Parse and Insert Timings and Delays for EACH match ---
                for innings_key in ['innings_1', 'innings_2']:
                    innings_data = enriched_match.get(innings_key)
                    if not innings_data:
                        continue

                    inning_id = innings_data.get('inning_id')

                    # 1. Insert/Update InningsTimings table
                    actual_start_str = innings_data.get('actual_starttime_utc')
                    actual_end_str = innings_data.get('actual_endtime_utc')
                    scheduled_start_str = innings_data.get('scheduled_starttime_utc')

                    actual_start_dt = datetime.strptime(f"{match_date_str} {actual_start_str}",
                                                        '%Y-%m-%d %H:%M:%S').replace(
                        tzinfo=timezone.utc) if actual_start_str else None
                    actual_end_dt = datetime.strptime(f"{match_date_str} {actual_end_str}",
                                                      '%Y-%m-%d %H:%M:%S').replace(
                        tzinfo=timezone.utc) if actual_end_str else None
                    scheduled_start_dt = datetime.strptime(f"{match_date_str} {scheduled_start_str}",
                                                           '%Y-%m-%d %H:%M:%S').replace(
                        tzinfo=timezone.utc) if scheduled_start_str else None

                    timings_query = """
                        INSERT INTO InningsTimings (
                            inning_id, total_duration_minutes, playing_duration_minutes,
                            actual_starttime_utc, actual_endtime_utc, scheduled_starttime_utc
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (inning_id) DO UPDATE SET
                            total_duration_minutes = COALESCE(EXCLUDED.total_duration_minutes, InningsTimings.total_duration_minutes),
                            playing_duration_minutes = COALESCE(EXCLUDED.playing_duration_minutes, InningsTimings.playing_duration_minutes),
                            actual_starttime_utc = COALESCE(EXCLUDED.actual_starttime_utc, InningsTimings.actual_starttime_utc),
                            actual_endtime_utc = COALESCE(EXCLUDED.actual_endtime_utc, InningsTimings.actual_endtime_utc),
                            scheduled_starttime_utc = COALESCE(EXCLUDED.scheduled_starttime_utc, InningsTimings.scheduled_starttime_utc);
                    """
                    cursor.execute(timings_query, (
                        inning_id,
                        innings_data.get('total_duration_minutes'),
                        innings_data.get('playing_duration_minutes'),
                        actual_start_dt,
                        actual_end_dt,
                        scheduled_start_dt
                    ))

                    # 2. Loop through and insert into InningsDelays table
                    for delay in innings_data.get('delays', []):
                        delay_start_str = delay.get('start_time_utc')
                        delay_resume_str = delay.get('resume_time_utc')

                        delay_start_dt = datetime.strptime(f"{match_date_str} {delay_start_str}",
                                                           '%Y-%m-%d %H:%M:%S').replace(
                            tzinfo=timezone.utc) if delay_start_str else None
                        delay_resume_dt = datetime.strptime(f"{match_date_str} {delay_resume_str}",
                                                            '%Y-%m-%d %H:%M:%S').replace(
                            tzinfo=timezone.utc) if delay_resume_str else None

                        delays_query = """
                            INSERT INTO InningsDelays (
                                inning_id, reason, start_time_utc, resume_time_utc, duration_minutes, overs_completed
                            ) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
                        """
                        cursor.execute(delays_query, (
                            inning_id,
                            delay.get('reason'),
                            delay_start_dt,
                            delay_resume_dt,
                            delay.get('duration_minutes'),
                            delay.get('overs_completed')
                        ))

                conn.commit()
                logger.info(f"Successfully enriched match: {match_id}")

        else:
            logger.warning("Failed to get or parse AI data for the batch of matches.")

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
    run_ai_enrichment_match_timings()