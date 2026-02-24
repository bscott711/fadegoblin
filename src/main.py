import argparse
import os
import random
from datetime import datetime

from atproto import Client, models

from . import config
from .betting import build_parlay
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
        "--dry-run",
        action="store_true",
        help="Generate content but skip posting to Bluesky",
    )
    args = parser.parse_args()

    print(
        f"--- Starting FadeGoblin run at {datetime.now()} (Dry Run: {args.dry_run}) ---"
    )

    print("🎲 Fetching live games...")
    games = get_live_games(max_games=15)

    if games:
        print("🎲 Constructing today's mortal locks...")
        chosen_legs, final_odds_str = build_parlay(games)
        post_text = generate_post_content(chosen_legs, final_odds_str)
    else:
        print("⚠️ No games found. Using fallback.")
        post_text = random.choice(FALLBACK_QUOTES)

    image_path = None
    if random.random() < config.TEXT_ONLY_ODDS:
        print("   🎲 Dice Roll: decided on TEXT ONLY mode. Skipping image.")
    else:
        prompt = generate_goblin_prompt()
        target_path = config.BASE_DIR / "temp_meme.jpg"
        image_path = download_goblin_image(prompt, target_path)

    if args.dry_run:
        print("\n🚫 DRY RUN MODE ENABLED. SKIPPING UPLOAD.")
        print(f"📝 Draft Post:\n{post_text}")
        if image_path:
            print(f"🖼️ Image saved to: {image_path}")
        else:
            print("🖼️ No image generated (Text Only Mode)")
        print("✅ Dry run complete.\n")
        return

    try:
        print("Connecting to Bluesky...")
        client = Client()
        client.login(config.BOT_HANDLE, config.APP_PASSWORD)  # type: ignore

        if image_path and image_path.exists():
            print("Uploading goblin image...")
            with open(image_path, "rb") as f:
                img_data = f.read()
            upload = client.upload_blob(img_data)

            print("📝 Posting with image...")
            client.send_post(
                text=post_text,
                embed=models.AppBskyEmbedImages.Main(
                    images=[
                        models.AppBskyEmbedImages.Image(
                            alt="A degenerate sports betting goblin",
                            image=upload.blob,
                        )
                    ]
                ),
            )
            os.remove(image_path)
        else:
            print("📝 Posting Text Only...")
            client.send_post(text=post_text)

        print("✅ Successfully posted to the timeline! Time to fade.")

    except Exception as e:
        print(f"❌ Error connecting or posting to Bluesky: {e}")


if __name__ == "__main__":
    main()
