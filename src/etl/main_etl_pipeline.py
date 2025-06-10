# src/etl/main_etl_pipeline.py
import logging
import os
from datetime import datetime
from src.etl import load_stg_match_data
from src.etl import etl_01_people_master
from src.etl import etl_02_dimensions_from_json
from src.etl import etl_03_matches_and_related
from src.etl import etl_04_innings_deliveries_etc
from src import db_utils
from src import config

# --- Setup Logging ---
def setup_logging():
    """Configures logging to write to a file."""
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_directory, f"etl_pipeline_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,  # Log INFO level and above (INFO, WARNING, ERROR, CRITICAL)
        # Change to logging.DEBUG for more verbose output during development
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),  # Log to this file
            logging.StreamHandler()  # Also log to console (optional, remove if you only want file)
        ]
    )
    # Get the root logger
    logger = logging.getLogger()
    logger.info("Logging setup complete. ETL process starting.")
    return logger

# Call setup_logging at the very beginning
setup_logging()
# --- End Logging Setup ---

def run_full_etl_pipeline():
    logger = logging.getLogger(__name__)
    logger.info("Starting Full ETL Pipeline...")

    # Step 0: Load raw JSON data into stg_match_data table
    logger.info("\n--- Step 0: Staging Raw JSON Data ---")
    try:
        load_stg_match_data.stage_all_json_files()
        logger.info("Step 0 completed successfully.")
    except Exception as e:
        logger.error(f"Error in Step 0 (Staging Raw JSON Data): {e}", exc_info=True)
        # Decide if you want to stop the pipeline or continue
        # return # Example: stop if staging fails

    # Step 1: Populate Players table from people.csv
    logger.info("\n--- Step 1: Populating Players Master Table ---")
    try:
        etl_01_people_master.load_people_master()
        logger.info("Step 1 completed successfully.")
    except Exception as e:
        logger.error(f"Error in Step 1 (Populating Players): {e}", exc_info=True)
        # return

    # Step 2: Populate Teams and Venues from stg_match_data
    logger.info("\n--- Step 2: Populating Teams and Venues Dimensions ---")
    team_id_cache, venue_id_cache = {}, {}  # Initialize
    try:
        team_id_cache, venue_id_cache = etl_02_dimensions_from_json.populate_teams_and_venues()
        if not team_id_cache or not venue_id_cache:  # Check if caches were populated
            logger.critical("Critical Error: Team or Venue caches not populated by Step 2. Aborting further ETL steps.")
            return
        logger.info("Step 2 completed successfully.")
    except Exception as e:
        logger.error(f"Error in Step 2 (Populating Teams/Venues): {e}", exc_info=True)
        logger.critical("Aborting pipeline due to critical error in Step 2.")
        return

    # Step 2.5: Populate a comprehensive player name -> identifier cache
    logger.info("\n--- Step 2.5: Populating Player Name to Identifier Cache ---")
    player_name_to_identifier_cache = {}
    conn_cache = None
    try:
        conn_cache = db_utils.get_db_connection()
        cursor_cache = conn_cache.cursor()
        cursor_cache.execute("SELECT identifier, name, unique_name FROM Players;")
        # for row in cursor_cache.fetchall():
        #     identifier, name, unique_name = row
        #     # Build the cache using the available name columns
        #     if name == unique_name:
        #         player_name_to_identifier_cache[name.strip()] = identifier
        #     if unique_name and unique_name.strip() not in player_name_to_identifier_cache:
        #         player_name_to_identifier_cache[unique_name.strip()] = identifier

        for row in cursor_cache.fetchall():
            identifier, name, unique_name = row
            # Build the cache using the available name columns
            if name == unique_name:
                player_name_to_identifier_cache[name.strip()] = identifier

        for row in cursor_cache.fetchall():
            identifier, name, unique_name = row
            if unique_name and unique_name.strip() not in player_name_to_identifier_cache:
                player_name_to_identifier_cache[unique_name.strip()] = identifier
            if name and name.strip() not in player_name_to_identifier_cache:
                player_name_to_identifier_cache[name.strip()] = identifier

        logger.info(f"Player name to identifier cache populated with {len(player_name_to_identifier_cache)} entries.")
        print(player_name_to_identifier_cache)
        cursor_cache.close()
    except Exception as e:
        logger.error(f"Error populating player name cache: {e}", exc_info=True)
        logger.critical("Aborting pipeline due to critical error in Player Cache population.")
        return
    finally:
        if conn_cache:
            conn_cache.close()

    # Step 3: Populate Matches and related tables
    logger.info("\n--- Step 3: Populating Matches and Related Tables ---")
    try:
        etl_03_matches_and_related.load_matches_and_related(team_id_cache, venue_id_cache,
                                                            player_name_to_identifier_cache)
        logger.info("Step 3 completed successfully.")
    except Exception as e:
        logger.error(f"Error in Step 3 (Populating Matches): {e}", exc_info=True)
        # return

    # Step 4: Populate Innings, Deliveries, Wickets, etc.
    logger.info("\n--- Step 4: Populating Innings, Deliveries and Related Transactional Tables ---")
    try:
        etl_04_innings_deliveries_etc.load_innings_deliveries_and_related(team_id_cache,
                                                                          player_name_to_identifier_cache)
        logger.info("Step 4 completed successfully.")
    except Exception as e:
        logger.error(f"Error in Step 4 (Populating Innings/Deliveries): {e}", exc_info=True)
        # return

    logger.info("\nFull ETL Pipeline Completed Successfully!")


if __name__ == "__main__":
    run_full_etl_pipeline()