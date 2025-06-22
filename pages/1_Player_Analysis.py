# pages/1_Player_Analysis.py

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

st.set_page_config(layout="wide")


# --- Database Connection ---
@st.cache_resource
def get_db_engine():
    """Creates and returns a SQLAlchemy engine, cached for performance."""
    logger.info("Creating new SQLAlchemy engine.")
    db_uri = f"postgresql+psycopg2://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    return create_engine(db_uri)


engine = get_db_engine()


# --- Data Fetching Functions for this Page ---
@st.cache_data
def get_player_list(_engine):
    """Fetches a list of all players for the dropdown."""
    logger.info("Fetching player list...")
    query = "SELECT first_last_name as name, identifier FROM Players WHERE full_name IS NOT NULL AND full_name != 'N/A' ORDER BY first_last_name;"
    try:
        data = pd.read_sql(query, _engine)
        return data
    except Exception as e:
        logger.error(f"Error fetching player list: {e}")
        return pd.DataFrame({'name': [], 'identifier': []})


@st.cache_data
def get_player_stats_by_season(_engine, player_id):
    """Fetches a player's batting stats grouped by season."""
    logger.info(f"Fetching seasonal stats for player_id: {player_id}")
    query = """
    SELECT
        m.season_year,
        SUM(d.runs_batter) AS total_runs,
        COUNT(d.delivery_id) AS balls_faced,
        COUNT(w.wicket_id) AS dismissals
    FROM Deliveries d
    JOIN Innings i ON d.inning_id = i.inning_id
    JOIN Matches m ON i.match_id = m.match_id
    LEFT JOIN Wickets w ON d.delivery_id = w.delivery_id AND d.batter_identifier = w.player_out_identifier
    WHERE d.batter_identifier = %(player_id)s
    GROUP BY m.season_year
    ORDER BY m.season_year;
    """
    try:
        data = pd.read_sql(query, _engine, params={"player_id": player_id})
        # Calculate Strike Rate and Average
        data['strike_rate'] = (data['total_runs'] / data['balls_faced'] * 100).round(2)
        data['average'] = (data['total_runs'] / data['dismissals'].replace(0, 1)).round(2)  # Avoid division by zero
        return data.set_index('season_year')
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        return pd.DataFrame()


# --- Build the Streamlit Page ---
st.title("Player Performance Analysis")

player_list_df = get_player_list(engine)

# --- Player Selection Dropdown ---
selected_player_name = st.selectbox(
    "Select a Player",
    options=player_list_df['name'],
    key='player_select_box'
)

if selected_player_name:
    # Get the identifier for the selected player
    player_id = player_list_df[player_list_df['name'] == selected_player_name]['identifier'].iloc[0]

    st.header(f"Batting Performance: {selected_player_name}")

    player_stats_df = get_player_stats_by_season(engine, player_id)

    if not player_stats_df.empty:
        # --- Display KPIs ---
        overall_stats = player_stats_df.sum()
        total_runs = int(overall_stats['total_runs'])
        total_balls = int(overall_stats['balls_faced'])
        total_dismissals = int(overall_stats['dismissals'])

        career_sr = round((total_runs / total_balls * 100), 2) if total_balls > 0 else 0
        career_avg = round((total_runs / total_dismissals), 2) if total_dismissals > 0 else total_runs

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Runs", f"{total_runs:,}")
        col2.metric("Career Average", f"{career_avg}")
        col3.metric("Career Strike Rate", f"{career_sr}")

        st.divider()

        # --- Display Chart ---
        st.subheader("Runs per Season")
        st.bar_chart(player_stats_df['total_runs'])

        st.subheader("Seasonal Stats")
        st.dataframe(player_stats_df[['total_runs', 'average', 'strike_rate', 'balls_faced', 'dismissals']],
                     use_container_width=True)
    else:
        st.warning("No batting data found for this player.")