import argparse
import os
import random
from datetime import datetime

from atproto import Client, models

from fadegoblin import config
from fadegoblin.betting import build_parlay
from fadegoblin.card import render_bet_card
from fadegoblin.ev_logic import get_sniper_bets, mark_bets_placed
from fadegoblin.generator import generate_post_content, generate_sniper_post_content
from fadegoblin.image import download_goblin_image, generate_goblin_prompt
from fadegoblin.odds import get_live_games
from fadegoblin.prompts import FALLBACK_QUOTES


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
        help="Run mode: 'degen' (random parlay) or 'sniper' (AlgoMLB DB picks)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"--- Starting FadeGoblin [{args.mode.upper()}] at {datetime.now()} ---")

    if args.mode == "sniper":
        _run_sniper(args.dry_run)
    else:
        _run_degen(args.dry_run)


def _run_degen(dry_run: bool) -> None:
    """Degen Mode: random parlay from live odds."""
    print("🎲 Mode: Degen. Fetching random live games...")
    games = get_live_games(max_games=15)
    chosen_legs = []
    final_odds_str = "N/A"

    if games:
        chosen_legs, final_odds_str = build_parlay(games)

    # --- Generate Content ---
    if chosen_legs:
        post_text = generate_post_content(chosen_legs, final_odds_str)
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

    _post_to_bluesky(post_text, image_path, dry_run)


def _run_sniper(dry_run: bool) -> None:
    """Sniper Mode: all +EV bets on a card, random POTD gets the writeup."""
    print("🎯 Mode: Sniper. Checking database for +EV bets...")
    all_legs, db_ids_to_update = get_sniper_bets()

    if not all_legs:
        print("💤 No pending/future EV bets found. Going back to sleep.")
        return

    print(f"📋 Found {len(all_legs)} +EV plays on the board.")

    # Randomly select a Play of the Day — the goblin picks on vibes, not math
    potd_index = random.randint(0, len(all_legs) - 1)
    potd_leg = all_legs[potd_index]

    # --- Render the bet card image ---
    card_path = render_bet_card(all_legs, potd_index)

    # --- Generate unhinged text for the POTD only ---
    post_text = generate_sniper_post_content(potd_leg)

    # --- Post (card image is always attached in sniper mode) ---
    _post_to_bluesky(post_text, card_path, dry_run, db_ids_to_update=db_ids_to_update)


def _post_to_bluesky(
    post_text: str,
    image_path: "os.PathLike | None",
    dry_run: bool,
    *,
    db_ids_to_update: list[str] | None = None,
) -> None:
    """Handles the Bluesky upload and optional DB ledger update."""
    if dry_run:
        print("\n🚫 DRY RUN MODE ENABLED. SKIPPING UPLOAD.")
        print(f"📝 Draft Post:\n{post_text}")
        if image_path:
            print(f"🖼️  Image: {image_path}")
        print("✅ Dry run complete.\n")
        return

    try:
        print("Connecting to Bluesky...")
        client = Client()
        client.login(config.BOT_HANDLE, config.APP_PASSWORD)

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = f.read()
            upload = client.upload_blob(img_data)
            client.send_post(
                text=post_text,
                embed=models.AppBskyEmbedImages.Main(
                    images=[
                        models.AppBskyEmbedImages.Image(
                            alt="FadeGoblin EV Board — today's +EV plays",
                            image=upload.blob,
                        )
                    ]
                ),
            )
            os.remove(image_path)
        else:
            client.send_post(text=post_text)

        print("✅ Successfully posted to the timeline!")

        # Mark DB bets as PLACED only after a successful post
        if db_ids_to_update:
            mark_bets_placed(db_ids_to_update)
            print(f"✅ Marked {len(db_ids_to_update)} EV bets as PLACED in database.")

    except Exception as e:
        print(f"❌ Error connecting or posting to Bluesky: {e}")
