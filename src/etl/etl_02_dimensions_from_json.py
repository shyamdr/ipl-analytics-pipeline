# src/etl/etl_02_dimensions_from_json.py
import psycopg2
import json
from src import config
from src import db_utils
import logging

logger = logging.getLogger(__name__)

# Caches to hold IDs of already inserted dimension data (name -> id)
team_id_cache = {}
venue_id_cache = {}  # Key will be (venue_name, city_name) tuple


def populate_teams_and_venues() -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    """
    Scans stg_match_data to find unique teams and venues,
    populates Teams and Venues tables, and fills local caches.
    
    Returns:
        tuple: (team_id_cache, venue_id_cache) or ({}, {}) on error
    """
    conn = None
    logger.info("Starting population of Teams and Venues tables...")
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT match_details FROM stg_match_data;")
        all_match_json_data = [row[0] for row in cursor.fetchall()]

        unique_teams_names = set()
        unique_venues_info = {}  # (venue_name, city) -> (venue_name, city)

        for match_json in all_match_json_data:
            info = match_json.get('info', {})

            # Collect Team Names
            for team_name in info.get('teams', []):
                if team_name: unique_teams_names.add(team_name.strip())
            if info.get('toss', {}).get('winner'):
                unique_teams_names.add(info['toss']['winner'].strip())
            if info.get('outcome', {}).get('winner'):
                unique_teams_names.add(info['outcome']['winner'].strip())
            # From innings
            for inning_data in match_json.get('innings', []):
                if inning_data.get('team'):
                    unique_teams_names.add(inning_data['team'].strip())

            # Collect Venue Info
            venue_name = info.get('venue')
            city_name = info.get('city')
            if venue_name:
                v_name_stripped = venue_name.strip()
                c_name_stripped = city_name.strip() if city_name else None
                unique_venues_info[(v_name_stripped, c_name_stripped)] = (v_name_stripped, c_name_stripped)

        # Insert Teams
        for name in unique_teams_names:
            try:
                cursor.execute(
                    "INSERT INTO Teams (team_name) VALUES (%s) ON CONFLICT (team_name) DO NOTHING;", (name,)
                )
            except Exception as e:
                logger.error(f"Error inserting team '{name}': {e}", exc_info=True)
                conn.rollback()
                raise

        # Insert Venues
        for key_tuple, val_tuple in unique_venues_info.items():
            venue_name, city = val_tuple
            try:
                cursor.execute(
                    "INSERT INTO Venues (venue_name, city) VALUES (%s, %s) ON CONFLICT (venue_name) DO NOTHING;",
                    (venue_name, city)
                )
            except Exception as e:
                logger.error(f"Error inserting venue '{venue_name}', City '{city}': {e}", exc_info=True)
                conn.rollback()
                raise

        conn.commit()
        logger.info("Teams and Venues tables populated.")

        cursor.execute("SELECT team_id, team_name FROM Teams;")
        for row in cursor.fetchall():
            team_id_cache[row[1]] = row[0]
        logger.info(f"Team ID cache populated with {len(team_id_cache)} teams.")

        cursor.execute("SELECT venue_id, venue_name, city FROM Venues;")
        for row in cursor.fetchall():
            venue_id_cache[(row[1], row[2])] = row[0]
        logger.info(f"Venue ID cache populated with {len(venue_id_cache)} venues.")

        return team_id_cache, venue_id_cache

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error populating dimension tables (Teams, Venues): {error}", exc_info=True)
        if conn:
            conn.rollback()
        raise  # Re-raise to let caller handle
    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
            logger.info("PostgreSQL connection for Teams/Venues load is closed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    global_team_id_cache, global_venue_id_cache = populate_teams_and_venues()
    logger.info(f"Standalone run finished. Fetched {len(global_team_id_cache)} teams.")
    logger.info(f"Standalone run finished. Fetched {len(global_venue_id_cache)} venues.")