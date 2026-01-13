# config.py
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_NAME: str = os.getenv("DB_NAME", "postgres")
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")

# Path Configuration
JSON_FILES_DIRECTORY: str = os.getenv("JSON_FILES_DIRECTORY", "data/raw_json_cricsheet/")
PEOPLE_CSV_PATH: str = os.getenv("PEOPLE_CSV_PATH", "data/master_data/people.csv")