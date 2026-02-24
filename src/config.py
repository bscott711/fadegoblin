import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_HANDLE = os.getenv("BOT_HANDLE")
APP_PASSWORD = os.getenv("APP_PASSWORD")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

TEXT_ONLY_ODDS = 0.3
BASE_DIR = Path(__file__).resolve().parent.parent


def check_env():
    if not all([BOT_HANDLE, APP_PASSWORD]):
        print("Error: Missing Bluesky credentials in .env file.")
        sys.exit(1)
    if not ODDS_API_KEY:
        print("Error: ODDS_API_KEY not found. Cannot fetch betting lines.")
        sys.exit(1)
    if not POLLINATIONS_API_KEY:
        print("⚠️ Warning: POLLINATIONS_API_KEY not found. Requests will likely fail.")
