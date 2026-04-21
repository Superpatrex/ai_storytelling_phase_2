import os
import sys
from dotenv import load_dotenv

# Define the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file located at the root of the project
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Load the Gemini API key from the environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables. Please set it in your .env file.", file=sys.stderr)

# Load the Gemini model name from the environment variables, with a default fallback
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
DEFAULT_MODEL = GEMINI_MODEL_NAME

# Story Constants
MAX_LOOP_PROCESSES = int(os.getenv("MAX_LOOP_PROCESSES", 15))  # Maximum number of loop iterations before we force a fix
MAX_RED_HERRINGS = int(os.getenv("MAX_RED_HERRINGS", 3))  # Maximum number of red herrings to use in the story

# Define directories for state and output
STATE_DIR = os.path.join(BASE_DIR, "state")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Ensure the state and output directories exist
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
