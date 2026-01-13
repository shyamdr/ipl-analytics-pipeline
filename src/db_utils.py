# db_utils.py
import psycopg2
import psycopg2.extensions
import logging
from . import config

logger = logging.getLogger(__name__)

def get_db_connection() -> psycopg2.extensions.connection:
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        logger.debug(f"Database connection established to {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to database. Check your credentials and ensure PostgreSQL is running.")
        logger.error(f"Connection details: host={config.DB_HOST}, port={config.DB_PORT}, dbname={config.DB_NAME}, user={config.DB_USER}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to database: {e}")
        raise