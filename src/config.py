# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Path Configuration
JSON_FILES_DIRECTORY = os.getenv("JSON_FILES_DIRECTORY", "data/raw_json_cricsheet/")
PEOPLE_CSV_PATH = os.getenv("PEOPLE_CSV_PATH", "data/master_data/people.csv")