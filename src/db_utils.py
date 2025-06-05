# db_utils.py
import psycopg2
from . import config # Import constants from config.py

def get_db_connection():
  """Establishes and returns a database connection."""
  conn = psycopg2.connect(
      dbname=config.DB_NAME,
      user=config.DB_USER,
      password=config.DB_PASSWORD,
      host=config.DB_HOST,
      port=config.DB_PORT
  )
  return conn