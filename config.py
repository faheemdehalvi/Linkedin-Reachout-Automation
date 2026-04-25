# LinkedIn Automation Configuration
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Supabase Configuration
SUPABASE_URL = "https://rschzmdnqfmorvuzzpva.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJzY2h6bWRucWZtb3J2dXp6cHZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwMzk0MjcsImV4cCI6MjA5MjYxNTQyN30.-sD3m00jBmgW90EgNEk6l7_nqWpasBFLRLUCts2EzEQ"

# Legacy SQLite (fallback)
DATABASE_PATH = DB_DIR / "linkedin_context.db"

# API & Model Configuration (update with your keys)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-key-here")
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Agent settings
MAX_SUGGESTIONS_PER_DAY = 5
MIN_CONFIDENCE_SCORE = 0.7
