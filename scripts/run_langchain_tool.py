# scripts/run_langchain_tool.py

import os
import logging
from dotenv import load_dotenv

# LangChain Imports
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain

# Import your config for DB details
from src import config

# --- Setup Logging (Same as main_etl_pipeline) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def run_langchain_sql_tool():
    # --- 1. Load API Key ---
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return

    # --- 2. Set up the Database Connection for LangChain ---
    # LangChain uses SQLAlchemy to interact with databases.
    # We create a database URI string from your config file.
    db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"

    logger.info("Connecting to the database...")
    db = SQLDatabase.from_uri(db_uri)
    logger.info("Database connection successful and schema loaded by LangChain.")

    # --- 3. Initialize the LLM ---
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

    # --- 4. Create the Text-to-SQL Chain ---
    # This single line replaces all our manual prompt engineering.
    # It knows how to get the schema from the 'db' object and create an effective prompt.
    generate_query_chain = create_sql_query_chain(llm, db)

    # --- 5. Start the Interactive Loop ---
    print("-" * 50)
    print("LangChain Text-to-SQL Tool is Ready.")
    print("Type your question and press Enter.")
    print("Type 'exit' or 'quit' to end.")
    print("-" * 50)

    while True:
        try:
            user_question = input("> ")
            if user_question.lower() in ['exit', 'quit']:
                break

            if not user_question:
                continue

            logger.info("Generating SQL query with LangChain...")

            # --- 6. Invoke the Chain ---
            # We send the question to the chain...
            generated_sql = generate_query_chain.invoke({"question": user_question})

            # ...and LangChain returns the clean SQL query.
            print("\n--- Generated SQL ---")
            print(generated_sql.strip())
            print("----------------------\n")

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    run_langchain_sql_tool()