"""
Configuration module for the Week 5 ReAct Loop & Tool Calling Project.
Sets up the environment, loads API keys, and initializes the Gemini Client.
Also provides a robust retry mechanism to handle free-tier rate limits (429 RESOURCE_EXHAUSTED).
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Define base paths
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from the project-level .env file first,
# then from the backend .env as a fallback.
if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")
elif (BASE_DIR.parent / ".env").exists():
    load_dotenv(BASE_DIR.parent / ".env")
else:
    load_dotenv()

# Get the API Key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "API Key not found. Please ensure GOOGLE_API_KEY or GEMINI_API_KEY "
        "is set in your environment or .env file."
    )

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# Configuration settings
DEFAULT_MODEL = "gemini-3.1-flash-lite"
MAX_ITERATIONS = 5
EVAL_SCORE_THRESHOLD = 0.7  # Passing threshold for groundedness and answer relevance


def call_with_retry(api_func, *args, **kwargs):
    """
    Executes a Gemini API function, automatically retrying with exponential backoff
    if rate limit (429 RESOURCE_EXHAUSTED) is encountered.
    """
    max_retries = 6
    backoff = 22.0  # Free tier allows 5 RPM, so we wait 22 seconds between retries/requests
    
    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"\n[SYSTEM] Rate limit hit (429). Retrying in {backoff:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(backoff)
                backoff *= 1.5
            else:
                raise e
    raise RuntimeError("Max retries exceeded for Gemini API call due to rate limits.")
