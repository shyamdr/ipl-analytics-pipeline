# src/etl/main_etl_pipeline.py
from src.etl import load_stg_match_data  # Assuming your original script is adapted or named this
from src.etl import etl_01_people_master
from src.etl import etl_02_dimensions_from_json
from src.etl import etl_03_matches_and_related
from src.etl import etl_04_innings_deliveries_etc
from src import db_utils  # For fetching initial caches for later steps


def run_full_etl_pipeline():
    print("Starting Full ETL Pipeline...")

    # Step 0: Load raw JSON data into stg_match_data table
    print("\n--- Step 0: Staging Raw JSON Data ---")
    load_stg_match_data.stage_all_json_files()  # Ensure this function exists and works

    # Step 1: Populate Players table from people.csv
    print("\n--- Step 1: Populating Players Master Table ---")
    etl_01_people_master.load_people_master()

    # Step 2: Populate Teams and Venues from stg_match_data
    # This function now returns the caches it populates.
    print("\n--- Step 2: Populating Teams and Venues Dimensions ---")
    team_id_cache, venue_id_cache = etl_02_dimensions_from_json.populate_teams_and_venues()

    if not team_id_cache or not venue_id_cache:
        print("Critical Error: Team or Venue caches not populated. Aborting further ETL steps.")
        return

    # Step 2.5: Populate a comprehensive player name -> identifier cache
    # This is crucial for etl_03 and etl_04
    player_name_to_identifier_cache = {}
    conn_cache = None
    try:
        conn_cache = db_utils.get_db_connection()
        cursor_cache = conn_cache.cursor()
        # Fetch all known names for players to build a lookup
        cursor_cache.execute("SELECT identifier, name, full_name, known_as FROM Players;")
        for row in cursor_cache.fetchall():
            identifier, name, full_name, known_as = row
            if name: player_name_to_identifier_cache[name.strip()] = identifier
            if full_name: player_name_to_identifier_cache[
                full_name.strip()] = identifier  # Overwrites if name was same, usually fine
            if known_as: player_name_to_identifier_cache[known_as.strip()] = identifier
        print(f"Player name to identifier cache populated with {len(player_name_to_identifier_cache)} entries.")
        cursor_cache.close()
    except Exception as e:
        print(f"Error populating player name cache: {e}")
        return  # Cannot proceed without player cache
    finally:
        if conn_cache:
            conn_cache.close()

    # Step 3: Populate Matches and related tables (MatchPlayers, PlayerOfMatchAwards, MatchOfficialsAssignment)
    print("\n--- Step 3: Populating Matches and Related Tables ---")
    etl_03_matches_and_related.load_matches_and_related(team_id_cache, venue_id_cache, player_name_to_identifier_cache)

    # Step 4: Populate Innings, Deliveries, Wickets, Powerplays, Replacements
    print("\n--- Step 4: Populating Innings, Deliveries and Related Transactional Tables ---")
    etl_04_innings_deliveries_etc.load_innings_deliveries_and_related(team_id_cache,
                                                                      player_name_to_identifier_cache)  # Pass caches

    print("\nFull ETL Pipeline Completed Successfully!")


if __name__ == "__main__":
    # Ensure all DDLs are run before executing this pipeline.
    # Ensure config.py has correct paths.
    run_full_etl_pipeline()