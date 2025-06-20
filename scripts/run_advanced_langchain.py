# scripts/run_advanced_langchain.py
import os

import psycopg2
import yaml
import pathlib
import logging
import pyperclip
import google.generativeai as genai
from dotenv import load_dotenv
from tabulate import tabulate

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


def construct_prompt(schema, examples, user_question):
    template = """You are a PostgreSQL expert. Your task is to write a single, high-quality, executable PostgreSQL query based on the user's question. You must use the provided schema. Given an input question, first create a syntactically correct postgresql query to run, then look at the results of the query and return the answer to the input question.

Here's some general guidelines to follow :
1. No. of rows to return : Regardless of any superlatives, such as "best, highest, biggest, lowest, smallest, some, a few" etc, ALWAYS return 3 records (use LIMIT 3). By default always use LIMIT 3.  If the user asks - "Give me top n rows" or "Give me exactly n rows" only then use LIMIT n. if the user asks for more than 50 records, cap the final output to LIMIT 50. never output more than 50 rows.
2. Searching for a player : Do not use the original player name provided by the user in the SQL query for joins or filters. Use the function 'get_player_id_by_name' and pass the input name to search for the player_id from always. The result of this function is to be subsequently used to join or filters.
3. Choosing right columns : Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
4. Providing right columns : Make sure you do not provide any internal id columns to the user such as player_id, match_id, inning_id etc, instead always provide the actual dimension that is a real-world entity such as if you present venue_id, instead show the name of the venue, if the final output should contain match id, instead of match id, provide the details of the match such as the match was between the two teams A & B and when and where it was played, if required, etc.

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
    return ChatPromptTemplate.from_template(template)


def clean_generated_sql(raw_sql: str) -> str:
    cleaned_sql = raw_sql.strip()
    if cleaned_sql.startswith("```sql"):
        cleaned_sql = cleaned_sql.removeprefix("```sql").removesuffix("```").strip()
    elif cleaned_sql.startswith("'''sql"):
        cleaned_sql = cleaned_sql.removeprefix("'''sql").removesuffix("'''").strip()
    elif cleaned_sql.startswith("```"):
        cleaned_sql = cleaned_sql.removeprefix("```").removesuffix("```").strip()
    return cleaned_sql.strip()


# Replace with this function
def is_safe_query(sql_query: str) -> bool:
    """A safety check to ensure only SELECT statements are executed."""
    query_lower = sql_query.strip().lower()
    # Rule 1: Must be a read-only query
    if not (query_lower.startswith("select") or query_lower.startswith("with")):
        return False
    # Rule 2: Must not contain any dangerous or data-modifying keywords
    dangerous_keywords = ["drop", "delete", "insert", "update", "truncate", "grant", "revoke"]
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            return False
    # Rule 3: Ensure no query chaining is attempted (check for semicolon in middle)
    if ';' in query_lower.rstrip(';'):
        return False
    return True


def execute_query(sql_query: str):
    """Executes a safe SQL query and displays the results in a formatted table."""
    if not is_safe_query(sql_query):
        logger.warning("Execution blocked: The generated query is not a safe SELECT statement.")
        return

    conn = None
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        logger.info("Executing safe query against the database...")
        cursor.execute(sql_query)

        if cursor.description:
            headers = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            print("\n--- Query Results ---")
            if not results:
                print("The query returned no results.")
            else:
                # Use tabulate to format the output nicely
                print(tabulate(results, headers=headers, tablefmt="psql"))
            print("--------------------\n")
        else:
            conn.commit()
            logger.info("Query executed, but it did not return any data rows (e.g., it was an UPDATE or INSERT).")

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Database query failed: {error}", exc_info=True)
    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()


def run_advanced_langchain_tool():
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return

    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        logger.info("Gemini API configured successfully.")
    except Exception as e:
        logger.error(f"Error configuring API: {e}")
        return

    db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    db = SQLDatabase.from_uri(db_uri, ignore_tables = ['people', 'stg_match_data', 'officials'])
    db_schema = db.get_table_info()

    #print(db.dialect)
    #print(db.get_usable_table_names())

    project_root = pathlib.Path(__file__).parent.parent
    examples_file = project_root / "src/text_to_sql/prompts/few_shot_examples.yaml"
    few_shot_examples = load_few_shot_examples(examples_file)
    formatted_examples = format_examples(few_shot_examples)
    logger.info(f"Loaded {len(few_shot_examples)} few-shot examples and database schema.")

    prompt_template = construct_prompt(db_schema, formatted_examples, "{question}")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20", temperature=0)
    sql_query_chain = (
            {
                "schema": lambda x: db_schema,  # Always use the db_schema we loaded
                "examples": lambda x: formatted_examples,  # Always use the examples we loaded
                "question": RunnablePassthrough()  # Pass the user's question through
            }
            | prompt_template
            | llm
            | StrOutputParser()
    )

    print("-" * 50)
    print("Advanced LangChain Text-to-SQL Tool is Ready.")
    print("Type your question and press Enter. Type 'exit' to quit.")
    print("-" * 50)

    while True:
        try:
            user_question = input("> ")
            if user_question.lower() in ['exit', 'quit']:
                break
            if not user_question:
                continue

            logger.info("Generating SQL query with custom LangChain prompt...")
            raw_sql_response = sql_query_chain.invoke(user_question)

            cleaned_sql = clean_generated_sql(raw_sql_response)

            print("\n--- Generated SQL ---")
            print(cleaned_sql)

            pyperclip.copy(cleaned_sql)
            logger.info("✅ SQL query also copied to clipboard.")

            print("----------------------\n")

            # --- MODIFIED: Execute the query ---
            execute_query(cleaned_sql)

        except Exception as e:
            logger.error(f"An error occurred in the main loop: {e}", exc_info=True)


if __name__ == "__main__":
    run_advanced_langchain_tool()