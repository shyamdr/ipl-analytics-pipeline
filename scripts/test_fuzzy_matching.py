# test_fuzzy_matching.py

import logging
from fuzzywuzzy import fuzz
from src import db_utils
import re

#logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def find_player_matches(search_term: str, threshold: int = 85):
    """
    Connects to the database and finds player names that have a high
    similarity score to the search term.
    """
    conn = None
    matches = []

    logger.info(f"Searching for players similar to '{search_term}' with a threshold of {threshold}%...")

    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()

        # Fetch all relevant player names from your database
        cursor.execute("SELECT identifier, name, unique_name, full_name FROM Players ORDER BY unique_name;")
        all_players = cursor.fetchall()
        best_score = 0

        for identifier, name, unique_name, full_name in all_players:

            # Finding first_last_name
            words = full_name.split()
            num_words = len(words)

            if num_words <= 2 : # The name is already in the desired format.
                first_last_name = full_name
            else:
                first_word, last_word, word_before_last = words[0], words[-1], words[-2]
                if word_before_last.lower() in ['de', 'al', 'ul']:
                    first_last_name = f"{first_word} {word_before_last} {last_word}"
                else:
                    first_last_name = f"{first_word} {last_word}"

            if

            unique_name_new = re.sub(r'\(.*\)', '', str(unique_name)).strip()

            # Combine all name parts into one long string, safely ignoring any None values
            name_parts = [name, unique_name_new, full_name]
            combined_names_string = ' '.join(part for part in name_parts if part)

            # Get a unique set of words to create a clean searchable string
            unique_words = dict.fromkeys(combined_names_string.lower().split())
            searchable_name_string = " ".join(unique_words)

            # if name == "SK Raina":
            #     print(searchable_name_string)

            first_last_name =

            score1 = fuzz.token_set_ratio(search_term.lower(), searchable_name_string)

            score2 = fuzz.partial_token_sort_ratio(search_term.lower(), full_name)
            score3 = fuzz.partial_token_sort_ratio(search_term.lower(), unique_name_new.lower())

            player_best_score = max(score1, score2)

            if player_best_score >= threshold:
                matches.append({
                    "identifier": identifier,
                    "name": name,
                    "unique_name": unique_name,
                    "score": player_best_score
                })
                print("full_name string is : " + searchable_name_string)

            if score1 == 100:
                logger.info("Found a perfect match. Stopping search.")
                matches = [matches[-1]]  # Keep only the last-appended match (the perfect one)
                break
            elif score2 == 100:
                logger.info("Found a match")
                matches = [matches[-1]]
                break
            elif score3 == 100:
                logger.info("found something")
                matches = [matches[-1]]

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

    # Sort the results by score, descending
    sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)

    # Print the results
    if not sorted_matches:
        logger.warning("No matches found above the threshold.")
    else:
        print("\n--- Potential Matches Found ---")
        for match in sorted_matches:
            print(f"Score: {match['score']}%\t| Name: {match['name']} (ID: {match['identifier']})")
        print("----------------------------\n")


if __name__ == "__main__":
    # --- Test it out here ---
    # You can change "virat" to "raina", "dhoni", "vk", etc. to test.
    input_word = "sachin"
    find_player_matches(input_word)