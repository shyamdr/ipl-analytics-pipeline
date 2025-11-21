# test_api.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def run_api_test():
    """
    Configures the Gemini API key from an environment variable and runs a simple test query.
    """
    try:
        # For professional projects, it's best practice to load secrets like API keys
        # from environment variables rather than hardcoding them in the script.
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it before running.")

        genai.configure(api_key=api_key)

        print("Successfully configured Gemini API.")

        # Let's start with a simple question to make sure the connection works
        prompt = "Who won the 2023 Men's ODI Cricket World Cup and who was the player of the final?"

        print(f"\nSending prompt: '{prompt}'")

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt)

        print("\n--- Gemini's Response ---")
        print(response.text)
        print("-------------------------\n")
        print("API test was successful!")

    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    run_api_test()