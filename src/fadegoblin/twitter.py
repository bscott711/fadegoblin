import tweepy
from pathlib import Path
from fadegoblin import config

def post_to_twitter(text: str, image_path: Path | None = None):
    """Posts a status update to Twitter/X with an optional image."""
    if not all([config.TWITTER_API_KEY, config.TWITTER_API_SECRET, 
                config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET]):
        print("⚠️ Twitter credentials missing. Skipping X post.")
        return None

    try:
        # OAuth 1.0a handles for Media Upload (v1.1) and Tweeting (v2)
        auth = tweepy.OAuth1UserHandler(
            config.TWITTER_API_KEY, config.TWITTER_API_SECRET,
            config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET
        )
        api_v1 = tweepy.API(auth)
        client_v2 = tweepy.Client(
            consumer_key=config.TWITTER_API_KEY,
            consumer_secret=config.TWITTER_API_SECRET,
            access_token=config.TWITTER_ACCESS_TOKEN,
            access_token_secret=config.TWITTER_ACCESS_TOKEN_SECRET
        )

        media_ids = []
        if image_path and image_path.exists():
            print(f"🐦 Uploading image to X: {image_path.name}")
            media = api_v1.media_upload(filename=str(image_path))
            media_ids = [media.media_id]

        print("🐦 Sending tweet to @TheFadeGoblin...")
        response = client_v2.create_tweet(text=text, media_ids=media_ids if media_ids else None)
        
        tweet_id = response.data['id']
        print(f"✅ Successfully posted to X! (ID: {tweet_id})")
        return tweet_id

    except Exception as e:
        print(f"❌ Failed to post to X: {e}")
        return None
