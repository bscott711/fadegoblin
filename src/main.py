import argparse
import os
import random
from datetime import datetime

from atproto import Client, models

from . import config
from .betting import build_parlay
from .ev_logic import get_sniper_bets, mark_bets_placed  # [NEW]
from .generator import generate_post_content
from .image import download_goblin_image, generate_goblin_prompt
from .odds import get_live_games
from .prompts import FALLBACK_QUOTES


def main() -> None:
    try:
        config.validate_config()
    except ValueError as e:
        print(f"Error: {e}")
        return

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        choices=["degen", "sniper"],
        default="degen",
        help="Run mode: 'degen' (random parlay) or 'sniper' (AlgoEPL DB picks)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"--- Starting FadeGoblin [{args.mode.upper()}] at {datetime.now()} ---")

    chosen_legs = []
    final_odds_str = "N/A"
    db_ids_to_update = []

    if args.mode == "degen":
        print("🎲 Mode: Degen. Fetching random live games...")
        games = get_live_games(max_games=15)
        if games:
            chosen_legs, final_odds_str = build_parlay(games)

    elif args.mode == "sniper":
        print("🎯 Mode: Sniper. Checking database for +EV bets...")
        chosen_legs, db_ids_to_update = get_sniper_bets()
        if not chosen_legs:
            print("💤 No pending/future EV bets found. Going back to sleep.")
            return  # Exit silently so it doesn't spam the timeline with fallbacks

        # If multiple EV bets exist, calculate their parlay odds for the text,
        # or just show them as a bundle.
        from .betting import calculate_parlay_odds

        # Extract the integer from the string "+150" or "-150" for the calculator
        raw_odds = [int(leg["odds"].replace("+", "")) for leg in chosen_legs]
        final_odds_str = calculate_parlay_odds(raw_odds)

    # --- Generate Content ---
    if chosen_legs:
        post_text = generate_post_content(chosen_legs, final_odds_str)
        # Tweak the text slightly if it's an EV play
        if args.mode == "sniper":
            post_text = f"👺 {post_text}"
    else:
        print("⚠️ No games found. Using fallback.")
        post_text = random.choice(FALLBACK_QUOTES)

    # --- Image Logic ---
    image_path = None
    if random.random() < config.TEXT_ONLY_ODDS:
        print("   🎲 Dice Roll: decided on TEXT ONLY mode. Skipping image.")
    else:
        prompt = generate_goblin_prompt()
        target_path = config.BASE_DIR / "temp_meme.jpg"
        image_path = download_goblin_image(prompt, target_path)

    # --- Dry Run Exit ---
    if args.dry_run:
        print("\n🚫 DRY RUN MODE ENABLED. SKIPPING UPLOAD.")
        print(f"📝 Draft Post:\n{post_text}")
        print("✅ Dry run complete.\n")
        return

    # --- Post to Bluesky ---
    try:
        print("Connecting to Bluesky...")
        client = Client()
        client.login(config.BOT_HANDLE, config.APP_PASSWORD)

        if image_path and image_path.exists():
            with open(image_path, "rb") as f:
                img_data = f.read()
            upload = client.upload_blob(img_data)
            client.send_post(
                text=post_text,
                embed=models.AppBskyEmbedImages.Main(
                    images=[
                        models.AppBskyEmbedImages.Image(
                            alt="A degenerate sports betting goblin", image=upload.blob
                        )
                    ]
                ),
            )
            os.remove(image_path)
        else:
            client.send_post(text=post_text)

        print("✅ Successfully posted to the timeline!")

        # 🚨 Mark DB Bets as Placed ONLY after a successful post 🚨
        if args.mode == "sniper" and db_ids_to_update:
            mark_bets_placed(db_ids_to_update)
            print(f"✅ Marked {len(db_ids_to_update)} EV bets as PLACED in database.")

    except Exception as e:
        print(f"❌ Error connecting or posting to Bluesky: {e}")
