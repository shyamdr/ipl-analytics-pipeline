# src/etl/load_stg_match_data.py
import json
import os
import psycopg2
from src import config
from src import db_utils
import logging

logger = logging.getLogger(__name__)

def load_json_to_staging_db(match_id, filepath, conn):
    """Loads a single JSON file into the stg_match_data table."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data_object = json.load(f)

        json_string_for_db = json.dumps(json_data_object)

        cur = conn.cursor()
        sql = "INSERT INTO stg_match_data (id, match_details) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET match_details = EXCLUDED.match_details;"
        cur.execute(sql, (match_id, json_string_for_db,))
        cur.close()
        logger.info(f"Successfully prepared staging data for ID: {match_id}")
        return True
    except FileNotFoundError:
        logger.error(f"File not found at {filepath}")
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {filepath}. Check file format.")
    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error while staging data from {filepath} (ID: {match_id}): {error}", exc_info=True)
    return False


def stage_all_json_files():
    """Iterates over JSON files and loads them into the staging table."""
    conn = None
    success_count = 0
    fail_count = 0
    try:
        conn = db_utils.get_db_connection()
        logger.info("Successfully connected to PostgreSQL for staging.")

        for filename in os.listdir(config.JSON_FILES_DIRECTORY):
            if filename.endswith(".json"):
                match_file_id = os.path.splitext(filename)[0]
                full_filepath = os.path.join(config.JSON_FILES_DIRECTORY, filename)
                logger.debug(f"Staging file: {full_filepath}")
                if load_json_to_staging_db(match_file_id, full_filepath, conn):
                    success_count += 1
                else:
                    fail_count += 1
        conn.commit()
        logger.info(f"Staging complete. Successful files: {success_count}, Failed files: {fail_count}")

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Error during staging process: {error}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info("PostgreSQL connection for staging is closed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("Starting staging process for raw JSON files...")
    stage_all_json_files()
    logger.info("Staging process finished.")