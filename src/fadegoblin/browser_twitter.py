import sys
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from fadegoblin import config

def post_to_twitter_browser(tweet_text: str, image_path: Path | None = None) -> None:
    """Automate posting to Twitter using Playwright with Google Chrome."""
    username = config.TWITTER_USERNAME
    password = config.TWITTER_PASSWORD

    if not username or not password:
        print("⚠️ Twitter credentials missing. Skipping X browser post.")
        return

    with sync_playwright() as p:
        # headless=False is less likely to trigger immediate bot detection during login
        # In a server environment, this requires a display or xvfb
        print(f"🐦 Launching browser for @{username}...")
        browser = p.chromium.launch(headless=True) # Forced headless for server compat, user-agent helps
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            print("🐦 Navigating to X login...")
            page.goto("https://x.com/i/flow/login")

            # Fill Username
            page.wait_for_selector('input[autocomplete="username"]')
            page.fill('input[autocomplete="username"]', username)
            page.click('button:has-text("Next")')

            # Fill Password
            page.wait_for_selector('input[name="password"]')
            page.fill('input[name="password"]', password)
            page.click('button[data-testid="LoginForm_Login_Button"]')

            # Wait for home timeline to ensure login success
            print("🐦 Waiting for login confirmation...")
            page.wait_for_selector('[data-testid="primaryColumn"]', timeout=15000)

            # Navigate directly to the compose URL
            page.goto("https://x.com/compose/tweet")

            # Type the tweet
            print("🐦 Drafting the Manic Slip...")
            page.wait_for_selector('[data-testid="tweetTextarea_0"]')
            page.fill('[data-testid="tweetTextarea_0"]', tweet_text)

            # Upload image if provided
            if image_path and image_path.exists():
                print(f"🐦 Uploading image: {image_path.name}")
                # X uses a hidden file input for media
                page.set_input_files('input[data-testid="fileInput"]', str(image_path))
                # Wait for the image to be processed (look for the remove button as proof it loaded)
                page.wait_for_selector('[data-testid="attachments"]', timeout=10000)

            # Click post
            print("🐦 FIRING POST...")
            page.click('[data-testid="tweetButton"]')

            # Wait for the toast notification to confirm sending
            page.wait_for_selector('[data-testid="toast"]', timeout=10000)
            print("✅ Tweet posted successfully via browser automation.")

        except PlaywrightTimeoutError as e:
            print(
                f"❌ Automation timed out. DOM may have changed or login blocked: {e}",
                file=sys.stderr,
            )
            # Take a screenshot for debugging if it fails
            page.screenshot(path="twitter_error.png")
            print("📸 Screenshot saved as twitter_error.png")
        finally:
            browser.close()
