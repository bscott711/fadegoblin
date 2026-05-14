import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Directories ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# --- Database ---
# Supports both DATABASE_URL (Standard) and DATABASE__URL (AlgoMLB compat)
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE__URL")

# --- Bluesky Credentials ---
BSKY_HANDLE = os.getenv("BOT_HANDLE")
BSKY_PASSWORD = os.getenv("APP_PASSWORD")

# --- Twitter/X Credentials ---
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# --- LLM / Image Generation ---
POLLINATIONS_AUTH = os.getenv("POLLINATIONS_AUTH")

# --- Tuning ---
TEXT_ONLY_ODDS = 0.05  # 5% chance of no image

def validate_config():
    """Ensures critical environment variables are set."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL must be set.")
    
    # We require at least one social target
    bsky_ready = all([BSKY_HANDLE, BSKY_PASSWORD])
    twitter_ready = all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET])
    
    if not bsky_ready and not twitter_ready:
        raise ValueError("At least one set of social credentials (Bluesky or Twitter) must be set.")
    
    if bsky_ready:
        print(f"✅ Bluesky configured as @{BSKY_HANDLE}")
    if twitter_ready:
        print(f"✅ Twitter/X configured (Keys found)")
