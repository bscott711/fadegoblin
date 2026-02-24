import argparse
import os
from datetime import datetime
from atproto import Client, models

from . import config
from .generator import generate_parlay_content


def main():
    config.check_env()

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

    # Generate the unhinged parlay and optional goblin image
    post_text, image_path = generate_parlay_content()

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
        client.login(config.BOT_HANDLE, config.APP_PASSWORD)

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
