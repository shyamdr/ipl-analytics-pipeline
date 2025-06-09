# src/etl/etl_01_people_master.py
import csv
import psycopg2
import logging
from src import config
from src import db_utils

logger = logging.getLogger(__name__)


def load_people_master():
    """Reads people.csv and populates the Players table based on its exact columns."""
    conn = None
    processed_count = 0
    skipped_count = 0

    logger.info(f"Starting to load people master data from: {config.PEOPLE_CSV_PATH}")
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        with open(config.PEOPLE_CSV_PATH, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            # Get the headers from the CSV file itself to make it robust
            headers = csv_reader.fieldnames

            # Prepare the SQL statement dynamically based on the headers
            # This makes the script adaptable if columns change slightly in the future
            sql_columns = ", ".join([f'"{h}"' for h in headers])  # Use quotes for safety
            sql_placeholders = ", ".join(["%s" for _ in headers])

            update_clause_parts = []
            for header in headers:
                if header != 'identifier':  # Don't update the primary key
                    update_clause_parts.append(f'"{header}" = EXCLUDED."{header}"')
            sql_update_clause = ", ".join(update_clause_parts)

            sql = f"""
                INSERT INTO People ({sql_columns})
                VALUES ({sql_placeholders})
                ON CONFLICT (identifier) DO UPDATE SET
                    {sql_update_clause};
            """

            for row_num, row in enumerate(csv_reader):
                processed_count += 1
                try:
                    # Check for mandatory identifier
                    if not row.get('identifier'):
                        logger.warning(f"Skipping row {row_num + 2} due to missing identifier.")
                        skipped_count += 1
                        continue

                    # Create a tuple of values in the same order as headers
                    values_tuple = tuple(row.get(h) or None for h in headers)

                    cursor.execute(sql, values_tuple)

                except Exception as e_row:
                    logger.error(f"Error processing CSV row {row_num + 2}: {row}. Error: {e_row}", exc_info=True)
                    skipped_count += 1

            sql = f"""
                INSERT INTO Players (identifier, name, unique_name, key_cricinfo)
                SELECT Identifier, name, unique_name, key_cricinfo 
                FROM People
                ON CONFLICT (identifier) DO NOTHING;
            """
            cursor.execute(sql)

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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    load_people_master()