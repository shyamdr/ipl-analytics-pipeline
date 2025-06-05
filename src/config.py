# config.py
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "1234" # Ideally, use environment variables for passwords in a real GitGub project
DB_HOST = "localhost"
DB_PORT = "5432"

# Path to the source JSON files (used by your original stg_match_data loading script)
JSON_FILES_DIRECTORY = "/Users/SHRANGAP2401/Personal Space/Projects/ipl_analytics_project/data/raw_json_cricsheet/"

# Path to the people.csv file
PEOPLE_CSV_PATH = "/Users/SHRANGAP2401/Personal Space/Projects/ipl_analytics_project/data/master_data/people.csv"