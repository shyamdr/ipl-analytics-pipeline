# test_fuzzy_matching.py

import logging
from fuzzywuzzy import fuzz
from src import db_utils

#logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def find_player_matches(search_term: str, threshold: int = 80):
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
        cursor.execute("SELECT identifier, name, unique_name, full_name FROM Players;")
        all_players = cursor.fetchall()

        for identifier, name, unique_name, full_name in all_players:
            # We use fuzz.partial_ratio, which is great for finding a substring
            # e.g., finding "Raina" inside "SK Raina"
            all_words_string = f"{name} {unique_name} {full_name}"
            all_words_list = all_words_string.split()
            union_string = " ".join(dict.fromkeys(all_words_list))

            if name == "SK Raina":
                print(union_string)

            #score1 = fuzz.partial_ratio(search_term.lower(), str(name).lower())
            #score2 = fuzz.partial_ratio(search_term.lower(), str(unique_name).lower())
            score3 = fuzz.token_set_ratio(search_term.lower(), str(union_string).lower())

            # Take the higher of the two scores
            best_score = score3 #max(score1, score2)

            if best_score >= threshold:
                matches.append({
                    "identifier": identifier,
                    "name": name,
                    "unique_name": unique_name,
                    "score": best_score
                })

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
    input_word = "Suresh Raina"
    find_player_matches(input_word)