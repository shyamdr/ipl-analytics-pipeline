# main_sql_agent.py

import streamlit as st
import pandas as pd  # Needed for Streamlit UI (e.g. st.dataframe)
import logging

# Import the core AI functionality from the scripts folder
from scripts.run_advanced_langchain import run_advanced_langchain_tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="IPL Data Chatbot",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar for a single-page app
)

# --- Streamlit Session State Initialization ---
# This is crucial for remembering previous questions/answers across Streamlit reruns
if 'last_question' not in st.session_state:
    st.session_state['last_question'] = ""
if 'last_answer' not in st.session_state:
    st.session_state['last_answer'] = ""
if 'api_called_success' not in st.session_state:
    st.session_state['api_called_success'] = False
if 'last_results_data' not in st.session_state:
    st.session_state['last_results_data'] = []
if 'last_results_headers' not in st.session_state:
    st.session_state['last_results_headers'] = []

# --- Build the Streamlit Page ---
st.title("Ask Your Cricket guru! 🏏")

st.markdown("""
Welcome to the **IPL Cricket Data Agent**! Type your question about IPL matches, players, or teams in plain English, and I'll try to provide an answer.
""")

st.subheader("Guidelines for Querying:")
st.markdown("""
-   **Be Specific:** Mention player names, teams, seasons (e.g., "IPL 2023").
-   **Focus on Facts:** I'm best at answering questions that require data retrieval from the database (e.g., "how many", "who", "what is", "list").
-   **Limit Results:** By default, I'll return the top 5 results. If you need more, ask for "top N rows" (e.g., "top 10 batsmen"). I will not return more than 50 rows.
-   **Player Names:** I am trained to resolve common names (e.g., "Virat", "Raina", "Dhoni"), However, it is advisable to use the first and last name of the player if known (e.g., "Dale Steyn", "Yuvraj Singh")
""")

st.subheader("Current Limitations:")
st.markdown("""
-   **Scope of Data:** Currently, I have been equipped with only IPL match data.
-   **Missing Information:** I am not aware of the particular wicket keepers and Captains for individual matches, hence i cannot answer questions surrounding these topics.
-   **Data Freshness:** My knowledge is limited to the data loaded into the database (up to the last ETL run) Currently, until IPL 2025.
-   **Context Limit:** For very complex or long conversations, the underlying AI model has a token limit.
""")

st.divider()

# --- User Input Section ---
user_query = st.text_input("Your Question:", value=st.session_state['last_question'])

col1, col2 = st.columns([1, 1])
with col1:
    generate_button = st.button("Generate Answer")
with col2:
    clear_button = st.button("Clear")

if clear_button:
    st.session_state['last_question'] = ""
    st.session_state['last_answer'] = ""
    st.session_state['api_called_success'] = False
    st.session_state['last_results_data'] = []
    st.session_state['last_results_headers'] = []
    st.experimental_rerun()  # Clear and rerun the app to reset state

if generate_button and user_query:
    st.session_state['last_question'] = user_query

    # Call the core AI logic
    with st.spinner("Thinking... Generating SQL and fetching answer..."):
        final_answer, results_data, results_headers, success_status = run_advanced_langchain_tool(user_query)

    st.session_state['last_answer'] = final_answer
    st.session_state['api_called_success'] = success_status
    st.session_state['last_results_data'] = results_data
    st.session_state['last_results_headers'] = results_headers

    if not success_status:
        st.error(st.session_state['last_answer'])  # Display the error message from the AI directly

# --- Display Results Section ---
if st.session_state['api_called_success']:
    st.subheader("Answer:")
    st.info(st.session_state['last_answer'])  # Display the natural language answer

    if st.session_state['last_results_data']:
        st.subheader("Query Results:")
        df_results = pd.DataFrame(st.session_state['last_results_data'], columns=st.session_state['last_results_headers'])
        st.dataframe(df_results, use_container_width=True)
    elif st.session_state['api_called_success'] and not st.session_state['last_results_data']:
        st.info("The query executed successfully but returned no results from the database.")