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
def get_summary_stats(_engine, season):
    """Fetches high-level summary statistics for a given season."""
    logger.info(f"Fetching summary stats for season {season}...")
    query = """
    SELECT
        COUNT(DISTINCT m.match_id) AS total_matches,
        SUM(d.runs_total) AS total_runs,
        COUNT(w.wicket_id) AS total_wickets
    FROM Matches m
    LEFT JOIN Innings i ON m.match_id = i.match_id
    LEFT JOIN Deliveries d ON i.inning_id = d.inning_id
    LEFT JOIN Wickets w ON d.delivery_id = w.delivery_id
    WHERE m.season_year = %(season)s;
    """
    try:
        data = pd.read_sql(query, _engine, params={"season": season})
        return data.iloc[0]
    except Exception as e:
        logger.error(f"Error fetching summary stats for season {season}: {e}")
        return pd.Series({'total_matches': 0, 'total_runs': 0, 'total_wickets': 0})

# Replace with this updated function
@st.cache_data
def get_top_run_scorers(_engine, season, top_n=10):
    """Fetches the top N run scorers for a given season."""
    logger.info(f"Fetching top {top_n} run scorers for season {season}...")
    query = f"""
    SELECT
        p.name AS player_name,
        SUM(d.runs_batter) AS total_runs
    FROM Deliveries d
    JOIN Players p ON d.batter_identifier = p.identifier
    JOIN Innings i ON d.inning_id = i.inning_id
    JOIN Matches m ON i.match_id = m.match_id
    WHERE m.season_year = %(season)s -- New WHERE clause
    GROUP BY p.name
    ORDER BY total_runs DESC
    LIMIT {top_n};
    """
    try:
        # Use params to safely pass the season to the query
        data = pd.read_sql(query, _engine, params={"season": season})
        return data.set_index('player_name')
    except Exception as e:
        logger.error(f"Error fetching top run scorers for season {season}: {e}")
        return pd.DataFrame({'total_runs': []})

@st.cache_data
def get_recent_matches(_engine, season, limit=10):
    """Fetches the N most recent matches for a given season."""
    logger.info(f"Fetching {limit} recent matches for season {season}...")
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
    WHERE m.season_year = %(season)s -- New WHERE clause
    ORDER BY m.match_date DESC
    LIMIT {limit};
    """
    try:
        data = pd.read_sql(query, _engine, params={"season": season})
        return data
    except Exception as e:
        logger.error(f"Error fetching recent matches for season {season}: {e}")
        return pd.DataFrame()

@st.cache_data
def get_season_list(_engine):
    """Fetches a sorted list of unique seasons."""
    logger.info("Fetching season list from database...")
    query = "SELECT DISTINCT season_year FROM Matches ORDER BY season_year DESC;"
    try:
        data = pd.read_sql(query, _engine)
        # Convert the DataFrame column to a list
        return data['season_year'].tolist()
    except Exception as e:
        logger.error(f"Error fetching season list: {e}")
        return []

db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
engine = create_engine(db_uri)

# --- Build the Streamlit Dashboard ---

st.title("🏏 IPL Cricket Data Dashboard")

# --- Get data for the filter ---
season_list = get_season_list(engine)

# --- Create the sidebar for filters ---
st.sidebar.header("Filters")
selected_season = st.sidebar.selectbox("Select a Season", options=season_list)

st.title(f"🏏 IPL Cricket Data Dashboard - Season {selected_season}")

# --- Display Summary Metrics ---
summary_data = get_summary_stats(engine, selected_season)

col1, col2, col3 = st.columns(3)
col1.metric("Total Matches Played", f"{summary_data.get('total_matches', 0):,}")
col2.metric("Total Runs Scored", f"{summary_data.get('total_runs', 0):,}")
col3.metric("Total Wickets Taken", f"{summary_data.get('total_wickets', 0):,}")

st.divider()

# --- Display Charts and DataFrames ---
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.header("Top 10 Run Scorers")
    top_scorers_data = get_top_run_scorers(engine, selected_season)
    st.bar_chart(top_scorers_data)

with col_right:
    st.header("Recent Matches")
    recent_matches_data = get_recent_matches(engine, selected_season)
    st.dataframe(recent_matches_data, use_container_width=True, hide_index=True)