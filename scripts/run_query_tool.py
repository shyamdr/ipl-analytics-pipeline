# scripts/run_query_tool.py
import os
import pathlib
import yaml  # Import the YAML library
import google.generativeai as genai
from dotenv import load_dotenv


def load_schema_from_ddl_files(ddl_path):
    """Reads all .sql files in a given directory to create a schema string."""
    schema_string = ""
    try:
        ddl_files = sorted(os.listdir(ddl_path))
        for filename in ddl_files:
            if filename.endswith(".sql"):
                with open(os.path.join(ddl_path, filename), 'r') as f:
                    schema_string += f.read() + "\n\n"
        return schema_string
    except FileNotFoundError:
        print(f"ERROR: DDL directory not found at '{ddl_path}'.")
        return None


def load_few_shot_examples(examples_path):
    """Loads few-shot examples from a YAML file."""
    try:
        with open(examples_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"WARNING: Few-shot examples file not found at '{examples_path}'. Proceeding without examples.")
        return []
    except yaml.YAMLError as e:
        print(f"ERROR: Could not parse YAML file: {e}")
        return []


def construct_prompt(schema, examples, user_question):
    """Dynamically constructs the master prompt from its components."""

    # Start with the main instruction
    instruction = "You are a PostgreSQL expert. Your task is to write a single, high-quality, executable PostgreSQL query based on the user's question. You must use the provided schema."

    # Format the few-shot examples
    example_prompts = ""
    if examples:
        for ex in examples:
            example_prompts += f"""### Example
Question: "{ex['question']}"
SQL Query:
{ex['sql']}
### End Example\n\n"""

    # Assemble the final prompt
    final_prompt = f"""{instruction}

### PostgreSQL Schema:
{schema}
### End Schema

{example_prompts}Now, based on the schema and the examples, write a PostgreSQL query for the following new question.
Only return the SQL query and nothing else.

Question: "{user_question}"

SQL Query:
"""
    return final_prompt


def run_text_to_sql_tool():
    """Main function to run the Text-to-SQL generation tool."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return

    try:
        genai.configure(api_key=api_key)
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error configuring API: {e}")
        return

    # --- Load Schema and Examples ONCE at the start ---
    project_root = pathlib.Path(__file__).parent.parent
    ddl_directory = project_root / "sql/DDL"
    examples_file = project_root / "src/text_to_sql/prompts/few_shot_examples.yaml"

    database_schema = load_schema_from_ddl_files(ddl_directory)
    few_shot_examples = load_few_shot_examples(examples_file)

    if not database_schema:
        return

    print("-" * 50)
    print("Database Schema and Examples loaded. The model is ready.")
    print("Type your question in plain English and press Enter.")
    print("Type 'exit' or 'quit' to end.")
    print("-" * 50)

    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    while True:
        user_question = input("> ")
        if user_question.lower() in ['exit', 'quit']:
            break

        if not user_question:
            continue

        # Construct the prompt dynamically for each question
        prompt = construct_prompt(database_schema, few_shot_examples, user_question)

        try:
            print("\nGenerating SQL query...")
            response = model.generate_content(prompt)
            generated_sql = response.text

            if "```sql" in generated_sql:
                generated_sql = generated_sql.split("```sql")[1].split("```")[0].strip()

            print("\n--- Generated SQL ---")
            print(generated_sql)
            print("----------------------\n")

        except Exception as e:
            print(f"\nAn error occurred while calling the Gemini API: {e}")


if __name__ == "__main__":
    run_text_to_sql_tool()