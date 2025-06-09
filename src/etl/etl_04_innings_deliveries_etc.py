# src/etl/etl_04_innings_deliveries_etc.py
import psycopg2
import json
from src import config
from src import db_utils
import logging

logger = logging.getLogger(__name__)


def get_player_id_from_name_robust(player_name, cursor, cache):
    """Helper to get player ID, robust to names vs existing IDs in registry"""
    if not player_name: return None
    if player_name in cache: return cache[player_name]

    cursor.execute("SELECT identifier FROM Players WHERE identifier = %s;", (player_name,))
    res_id = cursor.fetchone()
    if res_id:
        cache[player_name] = res_id[0]
        return res_id[0]

    query = """
        SELECT identifier FROM Players 
        WHERE name = %(name)s OR known_as = %(name)s OR full_name = %(name)s 
        LIMIT 1;
    """
    cursor.execute(query, {'name': player_name})
    res_name = cursor.fetchone()
    if res_name:
        cache[player_name] = res_name[0]
        return res_name[0]

    logger.warning(f"Player identifier still not found for: '{player_name}' during delivery processing.")
    return None


def load_innings_deliveries_and_related(team_id_cache, player_name_to_identifier_cache):
    """
    Processes stg_match_data to populate Innings, Deliveries, Wickets,
    Powerplays, and Replacements tables.
    """
    conn = None
    logger.info("Starting population of Innings, Deliveries, and related tables...")
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, match_details FROM stg_match_data;")
        staged_matches = cursor.fetchall()

        for match_file_id, match_json_detail in staged_matches:
            logger.debug(f"Processing innings & deliveries for match_id: {match_file_id}...")
            try:
                info = match_json_detail.get('info', {})
                teams_in_match_names = info.get('teams', [])

                json_innings_data = match_json_detail.get('innings', [])
                for inning_idx, inning_json in enumerate(json_innings_data):
                    inning_number = inning_idx + 1

                    batting_team_name = inning_json.get('team')
                    batting_team_id = team_id_cache.get(batting_team_name)

                    if not batting_team_id:
                        logger.error(
                            f"Batting team ID not found for '{batting_team_name}' in match {match_file_id}, inning {inning_number}. Skipping inning.")
                        continue

                    # Determine bowling team ID
                    bowling_team_id = None
                    if len(teams_in_match_names) == 2 and team_id_cache.get(
                            teams_in_match_names[0]) and team_id_cache.get(teams_in_match_names[1]):
                        team1_id_local = team_id_cache[teams_in_match_names[0]]
                        team2_id_local = team_id_cache[teams_in_match_names[1]]
                        bowling_team_id = team2_id_local if batting_team_id == team1_id_local else team1_id_local

                    if not bowling_team_id:
                        logger.error(
                            f"Could not determine bowling team for match {match_file_id}, inning {inning_number}. Skipping inning.")
                        continue

                    target_info = inning_json.get('target', {}) if inning_number == 2 else {}

                    is_super_over = inning_json.get('super_over', False)

                    cursor.execute("""
                        INSERT INTO Innings (match_id, inning_number, batting_team_id, bowling_team_id, target_runs, target_overs, is_super_over)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (match_id, inning_number) 
                        DO UPDATE SET batting_team_id = EXCLUDED.batting_team_id, bowling_team_id = EXCLUDED.bowling_team_id, 
                                     target_runs = EXCLUDED.target_runs, target_overs = EXCLUDED.target_overs, is_super_over = EXCLUDED.is_super_over
                        RETURNING inning_id;
                    """, (
                        match_file_id, inning_number, batting_team_id, bowling_team_id,
                        target_info.get('runs'),
                        str(target_info.get('overs')) if target_info.get('overs') is not None else None, is_super_over
                    # Ensure overs is string or null
                    ))
                    inning_id_db = cursor.fetchone()[0]

                    # --- Powerplays ---
                    for pp_json in inning_json.get('powerplays', []):
                        cursor.execute("""
                            INSERT INTO Powerplays (inning_id, type, from_over, to_over)
                            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
                        """, (inning_id_db, pp_json.get('type'), pp_json.get('from'), pp_json.get('to')))

                    # --- Deliveries ---
                    current_ball_in_over_count = 0  # Logical ball number as per JSON array order
                    for over_json in inning_json.get('overs', []):
                        over_number_val = over_json.get('over')

                        for delivery_json in over_json.get('deliveries', []):
                            current_ball_in_over_count += 1  # This is the sequence in the deliveries array for the over

                            batter_name = delivery_json.get('batter')
                            bowler_name = delivery_json.get('bowler')
                            non_striker_name = delivery_json.get('non_striker')

                            batter_identifier = get_player_id_from_name_robust(batter_name, cursor,
                                                                               player_name_to_identifier_cache)
                            bowler_identifier = get_player_id_from_name_robust(bowler_name, cursor,
                                                                               player_name_to_identifier_cache)
                            non_striker_identifier = get_player_id_from_name_robust(non_striker_name, cursor,
                                                                                    player_name_to_identifier_cache)

                            if not (batter_identifier and bowler_identifier and non_striker_identifier):
                                logger.warning(
                                    f"Skipping delivery in match {match_file_id}, inning {inning_number}, over {over_number_val} due to missing player identifier(s). Batter:'{batter_name}', Bowler:'{bowler_name}', NonStriker:'{non_striker_name}'")
                                continue

                            runs_data = delivery_json.get('runs', {})
                            extras_data = delivery_json.get('extras', {})

                            cursor.execute("""
                                INSERT INTO Deliveries (
                                    inning_id, over_number, ball_number_in_over,
                                    batter_identifier, bowler_identifier, non_striker_identifier,
                                    runs_batter, runs_extras, runs_total,
                                    extras_wides, extras_noballs, extras_byes, extras_legbyes, extras_penalty,
                                    raw_extras_json, raw_review_json
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING delivery_id;
                            """, (
                                inning_id_db, over_number_val, current_ball_in_over_count,
                                batter_identifier, bowler_identifier, non_striker_identifier,
                                runs_data.get('batter', 0), runs_data.get('extras', 0), runs_data.get('total', 0),
                                extras_data.get('wides', 0), extras_data.get('noballs', 0),
                                extras_data.get('byes', 0), extras_data.get('legbyes', 0),
                                extras_data.get('penalty', 0),
                                json.dumps(extras_data) if extras_data else None,
                                json.dumps(delivery_json.get('review')) if delivery_json.get('review') else None
                            ))
                            delivery_id_db = cursor.fetchone()[0]

                            # --- Wickets ---
                            for wicket_json in delivery_json.get('wickets', []):
                                player_out_name = wicket_json.get('player_out')
                                player_out_identifier = get_player_id_from_name_robust(player_out_name, cursor,
                                                                                       player_name_to_identifier_cache)

                                if not player_out_identifier:
                                    logger.warning(
                                        f"Skipping wicket for '{player_out_name}' due to missing player ID. Match {match_file_id}, Delivery {delivery_id_db}")
                                    continue

                                wicket_kind = wicket_json.get('kind')
                                bowler_credited_id = bowler_identifier if wicket_kind not in (
                                    'run out', 'obstructing the field', 'retired hurt', 'handled the ball',
                                    'timed out') else None

                                cursor.execute("""
                                    INSERT INTO Wickets (delivery_id, player_out_identifier, kind, bowler_credited_identifier)
                                    VALUES (%s, %s, %s, %s) RETURNING wicket_id;
                                """, (delivery_id_db, player_out_identifier, wicket_kind, bowler_credited_id))
                                wicket_id_db = cursor.fetchone()[0]

                                for fielder_json in wicket_json.get('fielders', []):
                                    fielder_name = fielder_json.get('name')
                                    fielder_identifier = get_player_id_from_name_robust(fielder_name, cursor,
                                                                                        player_name_to_identifier_cache)
                                    if fielder_identifier:
                                        cursor.execute("""
                                            INSERT INTO WicketFielders (wicket_id, fielder_player_identifier)
                                            VALUES (%s, %s) ON CONFLICT (wicket_id, fielder_player_identifier) DO NOTHING;
                                        """, (wicket_id_db, fielder_identifier))

                            # --- Replacements (Impact Players) ---
                            # JSON structure: delivery_obj -> 'replacements' -> 'match' (this is an array)
                            replacements_list_at_delivery = delivery_json.get('replacements', {}).get('match', [])
                            for rep_event in replacements_list_at_delivery:
                                team_replaced_name = rep_event.get('team')
                                player_in_name = rep_event.get('in')
                                player_out_name = rep_event.get('out')
                                reason = rep_event.get('reason')

                                team_replaced_id = team_id_cache.get(team_replaced_name)
                                player_in_identifier = get_player_id_from_name_robust(player_in_name, cursor,
                                                                                      player_name_to_identifier_cache)
                                player_out_identifier = get_player_id_from_name_robust(player_out_name, cursor,
                                                                                       player_name_to_identifier_cache)

                                if team_replaced_id and player_in_identifier and player_out_identifier:
                                    cursor.execute("""
                                        INSERT INTO Replacements (
                                            match_id, delivery_id, inning_id, team_id, 
                                            player_in_identifier, player_out_identifier, reason
                                        ) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
                                    """, (
                                        match_file_id, delivery_id_db, inning_id_db, team_replaced_id,
                                        player_in_identifier, player_out_identifier, reason
                                    ))
                        current_ball_in_over_count = 0  # Reset for next over's deliveries array

                conn.commit()
            except Exception as e_match_detail:
                logger.error(f"Error processing innings/deliveries for match_id {match_file_id}: {e_match_detail}",
                             exc_info=True)
                conn.rollback()

        logger.info("Innings, Deliveries, and related tables population attempt finished.")

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error in load_innings_deliveries_and_related: {error}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
            logger.info("PostgreSQL connection for Innings/Deliveries load is closed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("Simulating dimension cache loading for standalone run of Innings/Deliveries ETL...")

    temp_conn_main = db_utils.get_db_connection()
    temp_cursor_main = temp_conn_main.cursor()

    player_cache_for_run_main = {}
    temp_cursor_main.execute("SELECT identifier, name, full_name, known_as FROM Players;")
    for p_row_main in temp_cursor_main.fetchall():
        if p_row_main[1]: player_cache_for_run_main[p_row_main[1]] = p_row_main[0]
        if p_row_main[3] and p_row_main[3] not in player_cache_for_run_main: player_cache_for_run_main[p_row_main[3]] = \
            p_row_main[0]
        if p_row_main[2] and p_row_main[2] not in player_cache_for_run_main: player_cache_for_run_main[p_row_main[2]] = \
            p_row_main[0]

    team_cache_for_run_main = {}
    temp_cursor_main.execute("SELECT team_id, team_name FROM Teams;")
    for t_row_main in temp_cursor_main.fetchall():
        team_cache_for_run_main[t_row_main[1]] = t_row_main[0]

    temp_cursor_main.close()
    temp_conn_main.close()
    logger.info("Dimension caches simulated for standalone run.")

    load_innings_deliveries_and_related(team_cache_for_run_main, player_cache_for_run_main)