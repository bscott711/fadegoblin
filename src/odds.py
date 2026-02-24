import random

import requests

from . import config

ACTIVE_LEAGUES = [
    "soccer_epl",
    "soccer_uefa_champs_league",
    "soccer_italy_serie_a",
    "soccer_spain_la_liga",
    "soccer_usa_mls",
    "basketball_nba",
    "icehockey_nhl",
]


def get_live_games(max_games=15):
    """
    Fetches upcoming games across multiple random active leagues to allow cross-sport parlays.
    """
    random.shuffle(ACTIVE_LEAGUES)

    parsed_games = []
    leagues_queried = 0

    # Query up to 3 leagues per run to mix sports safely within the 500/month API limit
    for league in ACTIVE_LEAGUES:
        if leagues_queried >= 3 or len(parsed_games) >= max_games:
            break

        print(f"🎲 Checking odds for {league}...")
        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
        params = {
            "api_key": config.ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "american",
            "bookmakers": "draftkings",
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            leagues_queried += 1

            data = r.json()
            if not data:
                continue

            for game in data:
                if not game.get("bookmakers"):
                    continue
                market = game["bookmakers"][0].get("markets", [])
                if not market:
                    continue

                outcomes = market[0].get("outcomes", [])

                home_odds = away_odds = draw_odds = None

                for outcome in outcomes:
                    if outcome["name"] == game["home_team"]:
                        home_odds = outcome["price"]
                    elif outcome["name"] == game["away_team"]:
                        away_odds = outcome["price"]
                    elif outcome["name"].lower() == "draw":
                        draw_odds = outcome["price"]

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

                parsed_games.append(game_info)

                if len(parsed_games) >= max_games:
                    break

        except Exception as e:
            print(f"⚠️ Odds API Error on {league}: {e}")
            continue

    return parsed_games
