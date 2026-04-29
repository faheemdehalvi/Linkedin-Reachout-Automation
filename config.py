# LinkedIn Automation Configuration
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Supabase Configuration (loaded from .env)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Legacy SQLite (fallback)
DATABASE_PATH = DB_DIR / "linkedin_context.db"

# API & Model Configuration (loaded from .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")

# Agent settings
MAX_SUGGESTIONS_PER_DAY = 50
MAX_CONNECTION_TEXTS = 25
MAX_CONNECTION_REQUESTS = 25
MAX_CURATED_TEXTS = 25
MIN_CONFIDENCE_SCORE = 0.7
