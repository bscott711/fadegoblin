import time
import requests
import urllib.parse
import random
from pathlib import Path
from . import config
from .llm import get_auth_headers
from .prompts import ACTIONS, OUTFITS, STYLES, BACKGROUNDS


def generate_and_download_goblin_image() -> Path | None:
    selected_action = random.choice(ACTIONS)
    selected_outfit = random.choice(OUTFITS)
    selected_style = random.choice(STYLES)
    selected_bg = random.choice(BACKGROUNDS)

    print(
        f"🎲 Image Recipe: {selected_outfit}, {selected_action}, {selected_bg} ({selected_style})"
    )

    # --- CHANGED: Now generating a degenerate goblin ---
    image_prompt = (
        f"A degenerate green goblin {selected_outfit} {selected_action} {selected_bg}, "
        f"crazed, anxious, sweating expression, {selected_style}"
    )

    img_seed = int(time.time()) + random.randint(1, 1000)
    safe_prompt = urllib.parse.quote(image_prompt)

    image_url = f"https://gen.pollinations.ai/image/{safe_prompt}?seed={img_seed}&width=768&height=768&nologo=true&model=flux"
    image_path = config.BASE_DIR / "temp_meme.jpg"

    for attempt in range(3):
        try:
            print(f"🎨 Downloading image (Attempt {attempt + 1})...")
            response = requests.get(image_url, headers=get_auth_headers(), timeout=45)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
                return image_path
            else:
                print(
                    f"   ⚠️ Image Error (Attempt {attempt + 1}): {response.status_code}"
                )
        except Exception as e:
            print(f"   ⚠️ Image Connection Failed (Attempt {attempt + 1}): {e}")

        if attempt < 2:
            time.sleep(10)

    print("❌ Image generation failed. Proceeding with text only.")
    return None
