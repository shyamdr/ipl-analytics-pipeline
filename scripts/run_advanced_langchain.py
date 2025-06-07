# scripts/run_advanced_langchain.py
import os
import yaml
import pathlib
import logging
import pyperclip
from dotenv import load_dotenv

# --- LangChain Imports ---
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Import your config and db_utils
from src import config
from src import db_utils

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# --- Helper Functions ---
def load_few_shot_examples(examples_path):
    """Loads few-shot examples from a YAML file."""
    try:
        with open(examples_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"Few-shot examples file not found at '{examples_path}'.")
        return []
    except yaml.YAMLError as e:
        logger.error(f"Could not parse YAML file: {e}")
        return []


def format_examples(examples):
    """Formats the few-shot examples into a string for the prompt."""
    if not examples:
        return ""

    example_texts = []
    for ex in examples:
        example_texts.append(f"""
### Example
Question: "{ex['question']}"
SQL Query:
{ex['sql']}
### End Example""")

    # Join all example texts together
    return "\n\n".join(example_texts)


def run_advanced_langchain_tool():
    # --- 1. Load API Key ---
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return

    # --- 2. Connect to Database and Get Schema ---
    db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    logger.info("Connecting to the database...")
    db = SQLDatabase.from_uri(db_uri)
    db_schema = db.get_table_info()  # LangChain gets the schema for us
    logger.info("Database connection successful.")

    # --- 3. Load Few-Shot Examples ---
    project_root = pathlib.Path(__file__).parent.parent
    examples_file = project_root / "src/text_to_sql/prompts/few_shot_examples.yaml"
    few_shot_examples = load_few_shot_examples(examples_file)
    formatted_examples = format_examples(few_shot_examples)
    logger.info(f"Loaded {len(few_shot_examples)} few-shot examples.")

    # --- 4. Create a Custom Prompt Template ---
    template = """You are a PostgreSQL expert. Your task is to write a single, high-quality, executable PostgreSQL query based on the user's question. You must use the provided schema.

### PostgreSQL Schema:
{schema}
### End Schema

Here are some examples of good queries. Use them as a pattern for similar questions.
{examples}

Now, based on the schema and the examples, write a PostgreSQL query for the following new question.
Only return the SQL query and nothing else.

Question: "{question}"

SQL Query:
"""
    prompt = ChatPromptTemplate.from_template(template)

    # --- 5. Initialize the LLM ---
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)

    # --- 6. Create the Custom Chain using LangChain Expression Language (LCEL) ---
    sql_query_chain = (
            RunnablePassthrough.assign(schema=lambda x: db_schema)
            | RunnablePassthrough.assign(examples=lambda x: formatted_examples)
            | prompt
            | llm
            | StrOutputParser()
    )

    # --- 7. Start the Interactive Loop ---
    print("-" * 50)
    print("Advanced LangChain Text-to-SQL Tool is Ready.")
    print("-" * 50)

    while True:
        try:
            user_question = input("> ")
            if user_question.lower() in ['exit', 'quit']:
                break
            if not user_question:
                continue

            logger.info("Generating SQL query with custom LangChain prompt...")

            # Invoke the custom chain
            generated_sql = sql_query_chain.invoke({"question": user_question})

            cleaned_sql = generated_sql.strip()
            if cleaned_sql.startswith("```sql"):
                cleaned_sql = cleaned_sql.removeprefix("```sql").removesuffix("```").strip()
            elif cleaned_sql.startswith("'''sql"):
                cleaned_sql = cleaned_sql.removeprefix("'''sql").removesuffix("'''").strip()
            elif cleaned_sql.startswith("```"):
                cleaned_sql = cleaned_sql.removeprefix("```").removesuffix("```").strip()

            print("\n--- Generated SQL ---")
            print(cleaned_sql)
            print("----------------------\n")

            pyperclip.copy(cleaned_sql)
            logger.info("✅ SQL query copied to clipboard!")

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    run_advanced_langchain_tool()