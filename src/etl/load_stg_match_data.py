# src/etl/load_stg_match_data.py
import json
import os
import psycopg2 # Keep if not using db_utils, otherwise can remove
from src import config # Corrected import
from src import db_utils # Corrected import - use this for connection

def load_json_to_staging_db(match_id, filepath, conn):
    """Loads a single JSON file into the stg_match_data table."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: # Added encoding
            json_data_object = json.load(f)

        json_string_for_db = json.dumps(json_data_object)

        cur = conn.cursor()
        # Ensure your stg_match_data table has 'id' as TEXT PK and 'match_details' as JSONB
        sql = "INSERT INTO stg_match_data (id, match_details) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET match_details = EXCLUDED.match_details;"
        cur.execute(sql, (match_id, json_string_for_db,))
        # conn.commit() # Commit will be handled by the calling function or main_etl script
        cur.close()
        print(f"Successfully staged data from: {filepath} with ID: {match_id}")
        return True
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. Check file format.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while staging data from {filepath} (ID: {match_id}): {error}")
    return False


def stage_all_json_files():
    """Iterates over JSON files and loads them into the staging table."""
    conn = None
    success_count = 0
    fail_count = 0
    try:
        conn = db_utils.get_db_connection() # Use db_utils
        print("Successfully connected to PostgreSQL for staging!")

        for filename in os.listdir(config.JSON_FILES_DIRECTORY):
            if filename.endswith(".json"):
                match_file_id = os.path.splitext(filename)[0]
                full_filepath = os.path.join(config.JSON_FILES_DIRECTORY, filename)
                print(f"Staging file: {full_filepath}")
                if load_json_to_staging_db(match_file_id, full_filepath, conn):
                    success_count += 1
                else:
                    fail_count += 1
        conn.commit() # Commit all successful staging operations together
        print(f"Staging complete. Successful files: {success_count}, Failed files: {fail_count}")

    except (Exception, psycopg2.Error) as error:
        print(f"Error during staging process: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("PostgreSQL connection for staging is closed.")

if __name__ == "__main__":
    # This script populates stg_match_data.
    # Ensure stg_match_data (id TEXT PK, match_details JSONB) table exists.
    # Example DDL:
    # CREATE TABLE IF NOT EXISTS stg_match_data (
    #     id TEXT PRIMARY KEY,
    #     match_details JSONB NOT NULL
    # );
    print("Starting staging process for raw JSON files...")
    stage_all_json_files()
    print("Staging process finished.")