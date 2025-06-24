# src/etl/etl_03_matches_and_related.py
import psycopg2
import json
from datetime import datetime
from src import config
from src import db_utils
import logging

logger = logging.getLogger(__name__)


def get_player_identifier(player_name, cursor, player_name_to_identifier_cache):
    """Looks up player identifier by name, first in cache, then DB if not found."""
    if not player_name:
        return None
    if player_name in player_name_to_identifier_cache:
        return player_name_to_identifier_cache[player_name]

    cursor.execute("SELECT identifier FROM Players WHERE name = %s OR unique_name = %s LIMIT 1;",
                   (player_name, player_name))
    result = cursor.fetchone()
    if result:
        player_name_to_identifier_cache[player_name] = result[0]
        return result[0]
    else:
        cursor.execute("SELECT identifier FROM Players WHERE identifier = %s LIMIT 1;", (player_name,))
        result_id_check = cursor.fetchone()
        if result_id_check:
            player_name_to_identifier_cache[player_name] = result_id_check[0]
            return result_id_check[0]

        logger.warning(f"Player identifier not found for name: '{player_name}'")
        return None


def load_matches_and_related(team_id_cache, venue_id_cache, player_name_to_identifier_cache):
    """
    Processes stg_match_data to populate Matches, MatchPlayers,
    PlayerOfMatchAwards, and MatchOfficialsAssignment tables.
    """
    conn = None
    logger.info("Starting population of Matches and related tables...")
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, match_details FROM stg_match_data;")
        staged_matches = cursor.fetchall()

        for match_file_id, match_json_detail in staged_matches:
            logger.debug(f"Processing match_id: {match_file_id} for Matches table and related...")
            try:
                info = match_json_detail.get('info', {})

                # --- 1. Robustly parse teams and season ---

                # Robustly handle teams list which can be null
                teams_in_match = info.get('teams')
                if teams_in_match is None:
                    teams_in_match = []

                team1_name = teams_in_match[0] if len(teams_in_match) > 0 else None
                team2_name = teams_in_match[1] if len(teams_in_match) > 1 else None

                # *** FIX for season year format ***
                season_raw = info.get('season')
                season_year_to_insert = None
                if len(info.get('dates', [None])) > 1 and season_raw:
                    season_str = str(season_raw)
                    try:
                        # Take the first four characters, which represent the starting year
                        season_year_to_insert = int(season_str[:4])
                    except (ValueError, TypeError):
                        logger.error(f"Could not parse season '{season_str}' for match {match_file_id}.")
                        # This will cause the INSERT to fail if season_year column is NOT NULL, which is intended.
                else:
                    match_date_str = info.get('dates', [None])[0]
                    try:
                        season_year_to_insert = int(match_date_str[:4])
                    except (ValueError, TypeError):
                        logger.error(f"Could not parse season '{season_str}' for match {match_file_id}.")
                # *** End of fix ***

                team1_id = team_id_cache.get(team1_name)
                team2_id = team_id_cache.get(team2_name)

                venue_name_raw = info.get('venue', '').strip()
                city_raw = info.get('city', '').strip() if info.get('city') else None
                venue_key = (venue_name_raw, city_raw)
                venue_id = venue_id_cache.get(venue_key)

                if not venue_id and venue_name_raw:
                    for (vn, vc), vid in venue_id_cache.items():
                        if vn == venue_name_raw:
                            venue_id = vid
                            break
                if not venue_id and venue_name_raw:
                    logger.warning(
                        f"Venue ID not found for '{venue_name_raw}', City '{city_raw}' in match {match_file_id}")

                toss_winner_name = info.get('toss', {}).get('winner')
                toss_winner_team_id = team_id_cache.get(toss_winner_name) if toss_winner_name else None

                outcome_winner_name = info.get('outcome', {}).get('winner')
                outcome_winner_team_id = team_id_cache.get(outcome_winner_name) if outcome_winner_name else None

                outcome_details = info.get('outcome', {})
                outcome_type = None
                outcome_margin = None
                if 'by' in outcome_details:
                    if 'wickets' in outcome_details['by']:
                        outcome_type = 'wickets'
                        outcome_margin = outcome_details['by']['wickets']
                    elif 'runs' in outcome_details['by']:
                        outcome_type = 'runs'
                        outcome_margin = outcome_details['by']['runs']
                elif 'result' in outcome_details:
                    outcome_type = outcome_details['result']

                match_date_str = info.get('dates', [None])[0]
                match_date_obj = datetime.strptime(match_date_str, '%Y-%m-%d').date() if match_date_str else None

                cursor.execute("""
                    INSERT INTO Matches (
                        match_id, season_year, match_date, event_name, match_number, venue_id,
                        team1_id, team2_id, toss_winner_team_id, toss_decision,
                        outcome_winner_team_id, outcome_type, outcome_margin,
                        match_type, overs_limit, balls_per_over
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (match_id) DO UPDATE SET 
                        season_year = EXCLUDED.season_year, match_date = EXCLUDED.match_date, 
                        event_name = EXCLUDED.event_name, match_number = EXCLUDED.match_number, venue_id = EXCLUDED.venue_id,
                        team1_id = EXCLUDED.team1_id, team2_id = EXCLUDED.team2_id, 
                        toss_winner_team_id = EXCLUDED.toss_winner_team_id, toss_decision = EXCLUDED.toss_decision,
                        outcome_winner_team_id = EXCLUDED.outcome_winner_team_id, outcome_type = EXCLUDED.outcome_type, 
                        outcome_margin = EXCLUDED.outcome_margin, match_type = EXCLUDED.match_type, 
                        overs_limit = EXCLUDED.overs_limit, balls_per_over = EXCLUDED.balls_per_over;
                """, (
                    match_file_id,
                    season_year_to_insert,  # Using the corrected variable here
                    match_date_obj, info.get('event', {}).get('name'),
                    info.get('event', {}).get('match_number'), venue_id, team1_id, team2_id,
                    toss_winner_team_id, info.get('toss', {}).get('decision'), outcome_winner_team_id,
                    outcome_type, outcome_margin, info.get('match_type'), info.get('overs'),
                    info.get('balls_per_over')
                ))

                json_players_info = info.get('players', {})
                people_registry = info.get('registry', {}).get('people', {})
                for team_name_in_json, player_name_list in json_players_info.items():
                    current_team_id = team_id_cache.get(team_name_in_json)
                    if not current_team_id:
                        logger.warning(
                            f"Team ID not found for team '{team_name_in_json}' in match {match_file_id} for MatchPlayers.")
                        continue
                    for player_name in player_name_list:
                        #player_identifier = get_player_identifier(player_name, cursor, player_name_to_identifier_cache)
                        player_identifier = people_registry[player_name]
                        if player_identifier:
                            cursor.execute("""
                                INSERT INTO MatchPlayers (match_id, player_identifier, team_id)
                                VALUES (%s, %s, %s) ON CONFLICT (match_id, player_identifier) DO NOTHING;
                            """, (match_file_id, player_identifier, current_team_id))

                for pom_player_name in info.get('player_of_match', []):
                    #player_identifier = get_player_identifier(pom_player_name, cursor, player_name_to_identifier_cache)
                    player_identifier = people_registry[pom_player_name]
                    if player_identifier:
                        cursor.execute("""
                            INSERT INTO PlayerOfMatchAwards (match_id, player_identifier) VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                        """, (match_file_id, player_identifier))

                json_officials_info = info.get('officials', {})
                for role, official_name_or_list in json_officials_info.items():
                    official_names_to_process = []
                    if isinstance(official_name_or_list, list):
                        official_names_to_process.extend(official_name_or_list)
                    elif isinstance(official_name_or_list, str):
                        official_names_to_process.append(official_name_or_list)

                    for official_name in official_names_to_process:
                        #official_identifier = get_player_identifier(official_name, cursor,player_name_to_identifier_cache)
                        official_identifier = people_registry[official_name]
                        if official_identifier:
                            cursor.execute("""
                                INSERT INTO MatchOfficialsAssignment (match_id, official_identifier, match_role)
                                VALUES (%s, %s, %s) ON CONFLICT (match_id, official_identifier, match_role) DO NOTHING;
                            """, (match_file_id, official_identifier, role))

                conn.commit()
            except Exception as e_match:
                logger.error(f"Error processing details for match_id {match_file_id}: {e_match}", exc_info=True)
                conn.rollback()

        logger.info("Matches and related tables population attempt finished.")

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error in load_matches_and_related: {error}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
            logger.info("PostgreSQL connection for Matches load is closed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("Simulating dimension cache loading for standalone run...")

    temp_conn = db_utils.get_db_connection()
    temp_cursor = temp_conn.cursor()

    player_cache_for_run = {}
    temp_cursor.execute("SELECT identifier, name, full_name, known_as FROM Players;")
    for p_row in temp_cursor.fetchall():
        if p_row[1]: player_cache_for_run[p_row[1]] = p_row[0]
        if p_row[2]: player_cache_for_run[p_row[2]] = p_row[0]
        if p_row[3]: player_cache_for_run[p_row[3]] = p_row[0]

    team_cache_for_run = {}
    temp_cursor.execute("SELECT team_id, team_name FROM Teams;")
    for t_row in temp_cursor.fetchall():
        team_cache_for_run[t_row[1]] = t_row[0]

    venue_cache_for_run = {}
    temp_cursor.execute("SELECT venue_id, venue_name, city FROM Venues;")
    for v_row in temp_cursor.fetchall():
        venue_cache_for_run[(v_row[1], v_row[2])] = v_row[0]

    temp_cursor.close()
    temp_conn.close()
    logger.info("Dimension caches simulated for standalone run.")

    load_matches_and_related(team_cache_for_run, venue_cache_for_run, player_cache_for_run)