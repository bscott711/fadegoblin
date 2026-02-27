import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_HANDLE = os.getenv("BOT_HANDLE")
APP_PASSWORD = os.getenv("APP_PASSWORD")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")  # [NEW] Added for EV Sniper

TEXT_ONLY_ODDS = 0.1
BASE_DIR = Path(__file__).resolve().parent.parent


def validate_config() -> None:
    missing = []
    if not BOT_HANDLE:
        missing.append("BOT_HANDLE")
    if not APP_PASSWORD:
        missing.append("APP_PASSWORD")
    if not ODDS_API_KEY:
        missing.append("ODDS_API_KEY")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
