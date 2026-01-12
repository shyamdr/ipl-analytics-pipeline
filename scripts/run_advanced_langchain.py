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

_global_llm_cache = {}


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
1. No. of rows to return : Regardless of any superlatives, such as "best, highest, biggest, lowest, smallest, some, a few" etc, by default, ALWAYS return 10 records (use LIMIT 10). If the user asks - "Give me top n rows" or "Give me exactly n rows" only then use LIMIT n. If the user question asks for a set of data that is fixed such as on a time-frame like "trend across all the seasons" or "year-wise" or something similar, then instead of default limit, use maximum limit i.e (LIMIT 100). If the user asks for more than 100 records, cap the final output to LIMIT 100. never output more than 100 rows.
2. Searching for a player : Do not use the original player name provided by the user in the SQL query for joins or filters. Use the function 'get_player_id_by_name' and pass the input name to search for the player_id from always. The result of this function is to be subsequently used to join or filters. NEVER use the function 'get_player_id_by_name' inside the WHERE clause of a large table. ALWAYS calculate the player_id in a CTE first using the 'MATERIALIZED' keyword. Refer one-shot example for a sample pattern
3. Choosing right columns : Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
4. Providing right columns : Make sure you do not provide any internal id columns to the user such as player_id, match_id, inning_id etc, instead always provide the actual dimension that is a real-world entity such as if you present venue_id, instead show the name of the venue, if the final output should contain match id, instead of match id, provide the details of the match such as the match was between the two teams A & B and when and where it was played, if required, etc.
5. **CRITICAL:** Ensure the generated SQL is always syntactically correct and executable in PostgreSQL. Double-check all keywords, table aliases(make sure they are not SQL keywords), and column references. If you are unsure, try a simpler approach.
6. Enrich data with context : When the user asks for an aggregate metric (e.g., "most toss wins", "highest run scorer", "most wickets"), DO NOT just return the single count.
   - **ALWAYS** include the context (the denominator) and a calculated percentage/ratio without changing the grain of the data.
   - Add additional fields without changing the granularity of the data to improve the data and user experience - 
        For each of the different types of questions, these are some example of columns that can be added
        team batting/player batting/batting partnership stats - player_name, matches played, batting average, batting strike rate, runs, boundaries, age, batting hand, player contribution split (partnerships), player contribution for team (individual player) etc.
        team bowling/player bowling/bowling partnership stats - player name, matches played, bowling average, bowling strike rate, wickets, economy, age, bowler type, bowling hand, player contribution split (partnerships), player contribution for team (individual player) etc.
        team fielding/player fielding stats - player name, matches played, catches, stumping, run outs, age etc.

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


def is_safe_query(sql_query: str) -> bool:
    """Enhanced safety check to ensure only SELECT statements are executed."""
    if not sql_query or not sql_query.strip():
        return False
    
    query_lower = sql_query.strip().lower()
    
    # Rule 1: Must start with SELECT or WITH (for CTEs)
    if not (query_lower.startswith("select") or query_lower.startswith("with")):
        logger.warning(f"Query rejected: Must start with SELECT or WITH")
        return False
    
    # Rule 2: Block dangerous keywords (data modification)
    dangerous_keywords = [
        "drop", "delete", "insert", "update", "truncate", 
        "alter", "create", "grant", "revoke", "exec", "execute",
        "pg_sleep", "waitfor", "dbms_lock"  # Time-based attacks
    ]
    for keyword in dangerous_keywords:
        # Use word boundaries to avoid false positives (e.g., "dropped" in column name)
        if f" {keyword} " in f" {query_lower} " or query_lower.endswith(f" {keyword}"):
            logger.warning(f"Query rejected: Contains dangerous keyword '{keyword}'")
            return False
    
    # Rule 3: Block query chaining (multiple statements)
    if ';' in query_lower.rstrip(';'):
        logger.warning("Query rejected: Multiple statements detected")
        return False
    
    # Rule 4: Block comment-based injection attempts
    if '--' in sql_query or '/*' in sql_query or '*/' in sql_query:
        logger.warning("Query rejected: SQL comments detected")
        return False
    
    return True


def execute_query(sql_query: str):

    conn = None
    results = []
    headers = []
    error_message = ""
    success = False

    """Executes a safe SQL query and displays the results in a formatted table."""
    if not is_safe_query(sql_query):
        logger.warning("Execution blocked: The generated query is not a safe SELECT statement.")
        return results, headers, False, error_message

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
                success = True
                error_message = "The query ran successfully but returned no results were obtained."
                #return [], []
            else:
                # Use tabulate to format the output nicely
                print(tabulate(results, headers=headers, tablefmt="psql"))
                success = True
                #return results, headers
            print("--------------------\n")
        else:
            conn.commit()
            logger.info("Query executed, but it did not return any data rows (e.g., it was an UPDATE or INSERT).")
            success = True
            error_message = "Query executed successfully, but no data was returned (e.g., not a SELECT query)."
            #return [], []

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Database query failed: {error}", exc_info=True)
        logger.error(error_message, exc_info=True)
        success = False

    finally:
        if conn:
            if 'cursor' in locals() and cursor and not cursor.closed:
                cursor.close()
            conn.close()

    return results, headers, success, error_message


def summarize_results_with_ai(user_question: str, db_results: list, headers: list) -> str:
    """
    Takes the raw DB results and asks the AI to formulate a natural language answer.
    """
    if not db_results:
        return "The query ran successfully but returned no results."

    data_as_string = tabulate(db_results, headers=headers, tablefmt="psql")

    prompt = f"""
    You are a helpful cricket analyst. Your job is to answer the user's question in a clear, friendly, natural language sentence.
    Use the data provided below, which was retrieved from a database, to formulate your answer.
    
    Original user question: "{user_question}"
    
    **1. Summary Rules (CRITICAL):**
    - Your summary MUST be short and insightful (max 50-70 words).
    - DO NOT list all rows from the data. The user can see the full table separately.
    - Your goal is to synthesize the key trend, insight, or top 3-4 performers.
    - A good summary provides context that the raw numbers don't, for example, for the 
        user question - "give me the player and the match date for every single player's century who has scored atleast 2 centuries in their ipl career": 
        Bad Summary : "Here are the players who have scored at least two centuries in their IPL career, player x on date d1; player y on date d2, d3; ..."
        Good Summary(Preferred) : "While over 20 players have multiple centuries, Virat Kohli and Jos Buttler are in a class of their own, leading the pack with 7 each."
        Okay Summary(Also acceptable) : "Here's the list of all the players who have scored at least 2 centuries in their IPL career." (The results will be separately displayed in a table to the user)
        
    Data retrieved from database:
    {data_as_string}

    Based on the data, what is the answer to the user's question?
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Failed to summarize results with AI: {e}", exc_info=True)
        return "There was an error summarizing the results."


def run_advanced_langchain_tool(user_question: str) -> tuple[str, list, list, bool]:
    if not _global_llm_cache:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
            return "API key not found.", [], [], False

        try:
            genai.configure(api_key=api_key)
            logger.info("Gemini API configured successfully.")
            _global_llm_cache['llm'] = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            logger.error(f"Error configuring API: {e}")
            return f"API Configuration failed: {e}", [], [], False

    llm_model = _global_llm_cache['llm']

    db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    db = SQLDatabase.from_uri(db_uri, ignore_tables = ['people', 'stg_match_data', 'officials'])
    db_schema = db.get_table_info()

    #print(db.dialect)
    #print(db.get_usable_table_names())

    # Load few-shot examples
    project_root = pathlib.Path(__file__).parent.parent
    examples_file = project_root / "src/text_to_sql/prompts/few_shot_examples.yaml"
    few_shot_examples = load_few_shot_examples(examples_file)
    formatted_examples = format_examples(few_shot_examples)
    logger.info(f"Loaded {len(few_shot_examples)} few-shot examples and database schema.")

    # Build the LangChain componenets (Prompt and Chain)
    prompt_template = construct_prompt(db_schema, formatted_examples, "{question}")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
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

    final_answer = "Sorry, I couldn't process that request." # Default error message for the user
    results = []
    headers = []
    success_status = False

    try:
        logger.info(f"Generating SQL query for question: '{user_question}'")
        raw_sql_response = sql_query_chain.invoke(user_question)
        generated_sql = clean_generated_sql(raw_sql_response)
        logger.info(f"Generated SQL:\n{generated_sql.strip()}")

        # Copy results to clipboard
        #pyperclip.copy(generated_sql.strip())
        #logger.info("✅ SQL query also copied to clipboard.")

        # Execute the query to get raw data
        results, headers, success_from_exec, query_execution_error_msg = execute_query(generated_sql)

        if success_from_exec:
            if results:
                # If we have data, ask AI to summarize it
                logger.info("Summarizing results with AI ....")
                final_answer = summarize_results_with_ai(user_question, results, headers)
                success_status = True
                logger.info(f"AI Summary:\n{final_answer}")
            else:
                # If the query results nothing
                final_answer = query_execution_error_msg if query_execution_error_msg else "The query executed successfully but returned no results."
                success_status = True
                logger.info(final_answer)
        else:
            final_answer = "I encountered an issue while retrieving data. Please try rephrasing your question or check the data availability. (Technical details logged for debugging)."
            success_status = False
            logger.error(f"SQL execution failed for user question '{user_question}'. Error: {query_execution_error_msg}")

    except Exception as e:
        logger.error(f"An error occurred during AI SQL generation or execution: {e}", exc_info=True)
        final_answer = "I apologize, but I encountered an unexpected error. Could you please try asking your question again in a different way?"
        success_status = False

    return final_answer, results, headers, success_status


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.info("Running SQL Agent in standalone test mode.")

    # Example usage for testing
    test_question = "How many matches were played in IPL 2023?"
    final_answer, results_data, results_headers, success_status = run_advanced_langchain_tool(test_question)

    print("\n--- Standalone Test Results ---")
    print(f"Question: {test_question}")
    print(f"AI Answer: {final_answer}")
    if results_data:
        print("Query Results:\n", tabulate(results_data, headers=results_headers, tablefmt="psql"))
    else:
        print("No query results data.")
    print(f"Success: {success_status}")
    print("------------------------------")