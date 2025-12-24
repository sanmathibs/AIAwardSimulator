"""
AI Award Interpreter - Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = BASE_DIR / "sessions"
TEMPLATES_DIR = BASE_DIR / "generation" / "templates"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)

# OpenAI Configuration
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
if not OPENAI_API_KEY:
    raise ValueError(
        "api_key not found. Please set it in streamlit secrets."
    )

# Model Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EXTRACTION_MODEL = "gpt-5.1-2025-11-13"  # Can use "gpt-4-0125-preview" for latest
GAP_ANALYSIS_MODEL = "gpt-5.1-2025-11-13"
GENERATION_MODEL = "gpt-5.1-2025-11-13"

# Cost tracking (per 1K tokens)
COSTS = {
    "text-embedding-3-small": {"input": 0.00002, "output": 0},
    "gpt-5.1-2025-11-13": {"input": 0.00125, "output": 0.01},
    "gpt-5.1-2025-11-13": {"input": 0.00125, "output": 0.01},
}

# Budget limits
MONTHLY_BUDGET_LIMIT = 100.0  # USD
SESSION_COST_WARNING_THRESHOLD = 2.0  # USD

# ChromaDB Configuration
CHROMA_PERSIST_DIR = str(SESSIONS_DIR / "chroma_db")

# Baseline Configuration
BASELINE_CONFIG_PATH = DATA_DIR / "baseline_config.json"

# Fair Work Configuration
FAIRWORK_BASE_URL = "https://awards.fairwork.gov.au"
FAIRWORK_TIMEOUT = 30  # seconds

# Extraction Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
CHUNK_SIZE = 1000  # characters per clause chunk
MAX_TOKENS_PER_REQUEST = 4000

# UI Configuration
APP_TITLE = "AI Award Interpreter"
APP_ICON = "⚖️"
