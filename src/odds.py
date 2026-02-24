import random
import requests
from . import config

# We heavily weight soccer leagues here to satisfy the 3-way moneyline craving
ACTIVE_LEAGUES = [
    "soccer_epl",
    "soccer_uefa_champs_league",
    "soccer_italy_serie_a",
    "soccer_spain_la_liga",
    "soccer_usa_mls",
    "basketball_nba",
    "icehockey_nhl",
]


def get_live_games(num_games=3):
    """
    Fetches upcoming games for a random active league.
    Returns a list of parsed games with their odds.
    """
    random.shuffle(ACTIVE_LEAGUES)

    for league in ACTIVE_LEAGUES:
        print(f"🎲 Checking odds for {league}...")
        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
        params = {
            "api_key": config.ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",  # Head-to-Head (Moneyline)
            "oddsFormat": "american",
            "bookmakers": "draftkings",  # Using one standard book for clean lines
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()

            if not data:
                continue  # Try the next league if this one has no games today

            parsed_games = []
            for game in data:
                # Dig into the JSON to find the DraftKings h2h market
                if not game.get("bookmakers"):
                    continue
                market = game["bookmakers"][0].get("markets", [])
                if not market:
                    continue

                outcomes = market[0].get("outcomes", [])

                home_odds = None
                away_odds = None
                draw_odds = None

                # Safely parse 2-way or 3-way (Soccer) moneylines
                for outcome in outcomes:
                    if outcome["name"] == game["home_team"]:
                        home_odds = outcome["price"]
                    elif outcome["name"] == game["away_team"]:
                        away_odds = outcome["price"]
                    elif outcome["name"].lower() == "draw":
                        draw_odds = outcome["price"]

                # Format the odds with a + for positive American odds
                def fmt(odds):
                    return f"+{odds}" if odds > 0 else str(odds)

                game_info = {
                    "sport": league,
                    "home": game["home_team"],
                    "away": game["away_team"],
                    "home_odds": fmt(home_odds) if home_odds else "N/A",
                    "away_odds": fmt(away_odds) if away_odds else "N/A",
                }

                if draw_odds:
                    game_info["draw_odds"] = fmt(draw_odds)
                    game_info["desc"] = (
                        f"{game['away_team']} ({game_info['away_odds']}) @ {game['home_team']} ({game_info['home_odds']}) | Draw ({game_info['draw_odds']})"
                    )
                else:
                    game_info["desc"] = (
                        f"{game['away_team']} ({game_info['away_odds']}) @ {game['home_team']} ({game_info['home_odds']})"
                    )

                parsed_games.append(game_info)

                if len(parsed_games) >= num_games:
                    break

            if parsed_games:
                return parsed_games

        except Exception as e:
            print(f"⚠️ Odds API Error on {league}: {e}")
            continue

    print("❌ Could not find any active games across the targeted leagues.")
    return None
