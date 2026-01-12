# scripts/test_google_search_api.py
from googleapiclient.discovery import build
import json
import os
from dotenv import load_dotenv

# Replace with your API key and Custom Search Engine ID
API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CSE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def google_search(search_term, api_key, cse_id, **kwargs):
    """Perform a Google search and return results."""
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cse_key = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    if not api_key:
        print("ERROR: GOOGLE_SEARCH_API_KEY not found. Please set it in your .env file.")
        return
    elif not cse_key:
        print("ERROR: GOOGLE_SEARCH_ENGINE_ID not found. Please set it in your .env file.")
        return

    query = "ESPNCRICINFO 28763"

    try:
        # Perform search for top 10 results
        results = google_search(query, api_key, cse_key, num=5)
        # Print results
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['link']}")
            print(f"   Snippet: {result['snippet']}\n")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()