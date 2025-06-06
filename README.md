# IPL Cricket Data Analytics and ETL Pipeline

This project is a comprehensive data engineering pipeline that extracts, transforms, and loads Indian Premier League (IPL) cricket data into a structured relational database. It processes raw JSON match files and master CSV data, populates a normalized PostgreSQL schema, and serves as a foundation for advanced analytics, API development, and data visualization.

A key feature currently under development is a Natural Language to SQL (NL-to-SQL) interface, allowing users to ask questions in plain English to query the database.

---

## Key Features

* **Modular ETL Pipeline:** The data processing is broken down into logical, maintainable Python scripts.
* **Staging and Normalization:** Raw JSON data is first staged and then transformed into a clean, relational schema in PostgreSQL.
* **Master Data Integration:** Ingests and integrates master player data from external CSV files.
* **Robust Logging:** The entire pipeline is configured with file-based logging to track progress and debug errors effectively.
* **(In Progress) Natural Language to SQL:** A feature to translate plain English questions into SQL queries using the Google Gemini API.

---

## Tech Stack

* **Language:** Python 3
* **Database:** PostgreSQL
* **Python Libraries:**
    * `psycopg2-binary`: For connecting to PostgreSQL.
    * `python-dotenv`: For managing environment variables.
    * `google-generativeai`: For interacting with the Gemini API.

---


## Setup and Installation

1.  **Clone Repository:**
    ```bash
    git clone [https://github.com/shyamdr/ipl-analytics-pipeline.git](https://github.com/shyamdr/ipl-analytics-pipeline.git)
    cd ipl-analytics-pipeline
    ```

2.  **Setup PostgreSQL:**
    * Ensure you have a running PostgreSQL instance.
    * Create a database (e.g., `ipl_data`).
    * Update the connection details in `src/config.py` if they differ from the defaults.

3.  **Create Python Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    python3 -m pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables:**
    * Create a file named `.env` in the project root.
    * Add your Google AI API key to this file:
        ```
        GOOGLE_API_KEY='YOUR_SECRET_API_KEY_HERE'
        ```
    * The `.env` file is listed in `.gitignore` and should never be committed to source control.

6.  **Create Database Schema:**
    * Run the DDL scripts located in the `sql/DDL/` directory against your PostgreSQL database using pgAdmin or `psql` to create all the necessary tables.

---

## How to Run the ETL Pipeline

To execute the entire ETL process from start to finish, run the main pipeline script from the project root directory:

```bash
python3 -m src.etl.main_etl_pipeline
