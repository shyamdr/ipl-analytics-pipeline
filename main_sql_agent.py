# main_sql_agent.py

"""
TODO: Fine tune AI summarizer block to be more descriptive
TODO: Add charts or graph instead of tables
TODO: Allow users to download results into an excel/csv file
"""

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

# --- Sample Query Suggestions ---
SUGGESTIONS = [
    "Compare Virat Kohli's and Rohit Sharma's total runs and average across all IPL seasons.",
    "Which player has the best strike rate in death overs (overs 16-20) in IPL 2023 for players who faced at least 50 balls?",
    "List the top 3 venues with the highest average first innings score where at least 10 matches have been played.",
    "Find the number of centuries scored by each player in IPL history, ordered by the count of centuries descending.",
    "What is the average number of boundaries (fours and sixes combined) hit per match in IPL 2024?"
]

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
-   **Limit Results:** By default, I'll return the top 10 results. If you need more, ask for "top N rows" (e.g., "top 10 batsmen").
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

st.subheader("Here's some suggestions:")
# Use an expander to keep the UI clean if there are many suggestions
with st.expander("Show/Hide Suggestions"):
    cols = st.columns(3) # Display suggestions in 3 columns
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 3]: # Cycle through columns
            if st.button(suggestion, key=f"suggest_{i}"):
                st.session_state['last_question'] = suggestion
                # To immediately reflect the change in the text_input
                st.rerun()

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
    st.rerun()  # Clear and rerun the app to reset state

if generate_button and user_query:
    st.session_state['last_question'] = user_query

    # Call the core AI logic
    with st.spinner("Thinking... Generating query and fetching answer..."):
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
        num_rows = len(st.session_state['last_results_data'])
        custom_index = range(1, num_rows + 1)
        df_results = pd.DataFrame(
            st.session_state['last_results_data'],
            columns=st.session_state['last_results_headers'],
            index=custom_index)
        st.dataframe(df_results, use_container_width=True)
    elif st.session_state['api_called_success'] and not st.session_state['last_results_data']:
        st.info("The query executed successfully but returned no results from the database.")