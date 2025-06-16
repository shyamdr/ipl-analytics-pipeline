# dashboard.py

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src import config
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set page configuration for a wider layout
st.set_page_config(layout="wide")

# --- Data Fetching Functions (with caching) ---
# st.cache_data is a Streamlit feature that caches the results of a function.
# This means the database query will only run once, making the app much faster.

@st.cache_data
def get_summary_stats(_engine):
    """Fetches high-level summary statistics."""
    logger.info("Fetching summary stats from database...")
    query = """
    SELECT
        (SELECT COUNT(*) FROM Matches) AS total_matches,
        (SELECT SUM(runs_total) FROM Deliveries) AS total_runs,
        (SELECT COUNT(*) FROM Wickets) AS total_wickets;
    """
    try:
        data = pd.read_sql(query, _engine)
        return data.iloc[0]
    except Exception as e:
        logger.error(f"Error fetching summary stats: {e}")
        return pd.Series({'total_matches': 0, 'total_runs': 0, 'total_wickets': 0})

@st.cache_data
def get_top_run_scorers(_engine, top_n=10):
    """Fetches the top N run scorers."""
    logger.info(f"Fetching top {top_n} run scorers from database...")
    query = f"""
    SELECT
        p.name AS player_name,
        SUM(d.runs_batter) AS total_runs
    FROM Deliveries d
    JOIN Players p ON d.batter_identifier = p.identifier
    GROUP BY p.name
    ORDER BY total_runs DESC
    LIMIT {top_n};
    """
    try:
        data = pd.read_sql(query, _engine)
        # Set player_name as the index for better charting
        return data.set_index('player_name')
    except Exception as e:
        logger.error(f"Error fetching top run scorers: {e}")
        return pd.DataFrame({'total_runs': []})

@st.cache_data
def get_recent_matches(_engine, limit=10):
    """Fetches the N most recent matches."""
    logger.info(f"Fetching {limit} recent matches from database...")
    query = f"""
    SELECT
        m.match_date,
        CONCAT(t1.team_name, ' vs ', t2.team_name) as match_description,
        v.venue_name,
        v.city
    FROM Matches m
    JOIN Teams t1 ON m.team1_id = t1.team_id
    JOIN Teams t2 ON m.team2_id = t2.team_id
    JOIN Venues v ON m.venue_id = v.venue_id
    ORDER BY m.match_date DESC
    LIMIT {limit};
    """
    try:
        data = pd.read_sql(query, _engine)
        return data
    except Exception as e:
        logger.error(f"Error fetching recent matches: {e}")
        return pd.DataFrame()

db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
engine = create_engine(db_uri)

# --- Build the Streamlit Dashboard ---

st.title("🏏 IPL Cricket Data Dashboard")

# --- Display Summary Metrics ---
summary_data = get_summary_stats(engine)

col1, col2, col3 = st.columns(3)
col1.metric("Total Matches Played", f"{summary_data.get('total_matches', 0):,}")
col2.metric("Total Runs Scored", f"{summary_data.get('total_runs', 0):,}")
col3.metric("Total Wickets Taken", f"{summary_data.get('total_wickets', 0):,}")

st.divider()

# --- Display Charts and DataFrames ---
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.header("Top 10 Run Scorers")
    top_scorers_data = get_top_run_scorers(engine)
    st.bar_chart(top_scorers_data)

with col_right:
    st.header("Recent Matches")
    recent_matches_data = get_recent_matches(engine)
    st.dataframe(recent_matches_data, use_container_width=True, hide_index=True)