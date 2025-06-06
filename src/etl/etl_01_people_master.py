# src/etl/etl_01_people_master.py
import csv
import psycopg2
from datetime import datetime
from src import config
from src import db_utils
import logging

logger = logging.getLogger(__name__)

def parse_date_of_birth(dob_str):
    """Parses date string, handling potential errors."""
    if not dob_str or dob_str.lower() == 'nan' or dob_str.lower() == 'none':
        return None
    try:
        return datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(dob_str, '%d/%m/%Y').date()
        except ValueError:
            logger.warning(f"Could not parse date_of_birth: {dob_str}")
            return None


def parse_roles_list(roles_str):
    """Parses the roles string (e.g., "Player,Umpire") into a list of strings."""
    if not roles_str or roles_str.lower() == 'nan' or roles_str.lower() == 'none':
        return None
    return [role.strip() for role in roles_str.split(',')]


def load_people_master():
    """Reads people.csv and populates the Players table."""
    conn = None
    processed_count = 0
    updated_count = 0
    inserted_count = 0
    skipped_count = 0

    logger.info(f"Starting to load people master data from: {config.PEOPLE_CSV_PATH}")
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        with open(config.PEOPLE_CSV_PATH, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row_num, row in enumerate(csv_reader):
                processed_count += 1
                try:
                    identifier = row.get('identifier')
                    if not identifier:
                        logger.warning(f"Skipping row {row_num + 2} due to missing identifier: {row}")
                        skipped_count += 1
                        continue

                    dob = parse_date_of_birth(row.get('date_of_birth'))
                    roles = parse_roles_list(row.get('roles'))

                    name = row.get('name') or None
                    full_name = row.get('full_name') or None
                    country = row.get('country') or None
                    batting_hand = row.get('batting_hand') or None
                    bowling_hand = row.get('bowling_hand') or None
                    bowling_style = row.get('bowling_style') or None
                    known_as = row.get('known_as') or None

                    cursor.execute("""
                        INSERT INTO Players (
                            identifier, name, full_name, date_of_birth, country,
                            batting_hand, bowling_hand, bowling_style, known_as, roles
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (identifier) DO UPDATE SET
                            name = EXCLUDED.name,
                            full_name = EXCLUDED.full_name,
                            date_of_birth = EXCLUDED.date_of_birth,
                            country = EXCLUDED.country,
                            batting_hand = EXCLUDED.batting_hand,
                            bowling_hand = EXCLUDED.bowling_hand,
                            bowling_style = EXCLUDED.bowling_style,
                            known_as = EXCLUDED.known_as,
                            roles = EXCLUDED.roles
                        RETURNING identifier;
                    """, (
                        identifier, name, full_name, dob, country,
                        batting_hand, bowling_hand, bowling_style, known_as,
                        roles
                    ))
                    if cursor.rowcount > 0:
                        pass

                except Exception as e_row:
                    logger.error(f"Error processing CSV row {row_num + 2}: {row}. Error: {e_row}", exc_info=True)
                    skipped_count += 1

            conn.commit()
            logger.info(
                f"Players table populated/updated. Total rows from CSV: {processed_count}. Processed successfully: {processed_count - skipped_count}, Skipped due to errors: {skipped_count}")

    except FileNotFoundError:
        logger.error(f"FATAL: People CSV file not found at {config.PEOPLE_CSV_PATH}")
    except (Exception, psycopg2.Error) as error:
        logger.error("Error connecting to PostgreSQL or during CSV processing.", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()
            logger.info("PostgreSQL connection for people master load is closed.")


if __name__ == "__main__":
    # Note: For standalone running, logging needs to be configured.
    # The main_etl_pipeline.py script already does this.
    # If running this file directly, you might need a temporary logging config here.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    load_people_master()