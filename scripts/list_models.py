# list_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def discover_models():
    """Lists all available Gemini models."""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found.")

        genai.configure(api_key=api_key)

        print("Finding available models...\n")

        for m in genai.list_models():
            # Check if the model supports the 'generateContent' method
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model name: {m.name}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    discover_models()