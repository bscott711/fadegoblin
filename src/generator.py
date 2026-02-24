import random
from datetime import datetime
from pathlib import Path

from . import config
from .image import generate_and_download_goblin_image
from .llm import get_ai_text
from .odds import get_live_games
from .prompts import FALLBACK_QUOTES, PERSONAS


def calculate_parlay_odds(odds_list: list[int]) -> str:
    """Safely converts American odds to Decimal, multiplies them, and converts back."""
    if not odds_list:
        return "N/A"

    if len(odds_list) == 1:
        odd = odds_list[0]
        return f"+{odd}" if odd > 0 else str(odd)

    decimal_total = 1.0
    for odd in odds_list:
        if odd > 0:
            decimal_total *= (odd / 100.0) + 1.0
        elif odd < 0:
            decimal_total *= (100.0 / abs(odd)) + 1.0

    if decimal_total >= 2.0:
        american = int(round((decimal_total - 1.0) * 100.0))
        return f"+{american}"
    else:
        american = int(round(-100.0 / (decimal_total - 1.0)))
        return str(american)


def generate_parlay_content() -> tuple[str, Path | None]:
    print("🎲 Constructing today's mortal locks...")

    # Pull extra games so Python has room to filter
    games = get_live_games(num_games=6)
    if not games:
        print("⚠️ No games found. Using fallback.")
        return random.choice(FALLBACK_QUOTES), None

    # --- PYTHON BANKROLL MANAGEMENT (Filtering & Math) ---
    valid_legs = []
    for g in games:
        for side, odds_val in [
            (g["home"], g["home_odds"]),
            (g["away"], g["away_odds"]),
            ("Draw", g.get("draw_odds", "N/A")),
        ]:
            if odds_val != "N/A":
                int_odds = int(odds_val)
                # Drop heavy favorites worse than -350
                if int_odds >= -350:
                    valid_legs.append(
                        {
                            "game": f"{g['away']} @ {g['home']}",
                            "pick": side,
                            "odds": int_odds,
                        }
                    )

    chosen_legs = []
    final_odds_str = ""

    # Try up to 100 times to build a mathematically sound bet (capped at +350)
    for _ in range(100):
        # 40% chance of straight bet, 40% 2-leg, 20% 3-leg
        num_legs = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
        sample = random.sample(valid_legs, min(num_legs, len(valid_legs)))

        # Prevent taking two sides of the same game
        seen_games = set()
        conflict = False
        for leg in sample:
            if leg["game"] in seen_games:
                conflict = True
                break
            seen_games.add(leg["game"])
        if conflict:
            continue

        odds_ints = [leg["odds"] for leg in sample]
        calc_str = calculate_parlay_odds(odds_ints)
        calc_int = int(calc_str)

        # Keep the final ticket reasonable
        if -200 <= calc_int <= 350:
            chosen_legs = sample
            final_odds_str = calc_str
            break

    # Safety net if the loop fails
    if not chosen_legs and valid_legs:
        chosen_legs = [random.choice(valid_legs)]
        final_odds_str = calculate_parlay_odds([chosen_legs[0]["odds"]])

    bet_type = "Parlay Odds" if len(chosen_legs) > 1 else "Odds"

    leg_descriptions = [
        f"{leg['pick']} to win their matchup ({leg['game']})" for leg in chosen_legs
    ]
    locked_bet_text = "\n".join([f"- {desc}" for desc in leg_descriptions])

    if len(chosen_legs) > 1:
        bet_summary = "a parlay on: " + " AND ".join(
            [leg["pick"] for leg in chosen_legs]
        )
    else:
        bet_summary = "a straight bet on: " + chosen_legs[0]["pick"]

    print(f"📈 Locked Ticket ({final_odds_str}):\n{locked_bet_text}")

    # --- PERSONA & THEME INCEPTION ---
    current_day = datetime.now().weekday()
    daily_pair = [PERSONAS[current_day * 2], PERSONAS[current_day * 2 + 1]]
    selected_style = random.choice(daily_pair)

    print(f"🎭 Selected Persona: {selected_style['name']}")

    print("   🧠 Brainstorming abstract logic...")
    theme_prompt = (
        f"Brainstorm 3 highly specific, absurd reasons to bet {bet_summary}. "
        f"Persona: '{selected_style['name']}'. "
        f"CRITICAL RULES: DO NOT narrate a physical scene. Focus entirely on bizarre logic. "
        f"Output ONLY the 3 concepts separated by a pipe character (|)."
    )

    raw_themes = get_ai_text(theme_prompt)
    chosen_theme = "my gut feeling"
    if raw_themes:
        themes = [t.strip() for t in raw_themes.split("|") if len(t.strip()) > 5]
        if themes:
            chosen_theme = random.choice(themes)
            print(f"   💡 Chosen Concept: {chosen_theme}")

    # --- FINAL TWEET GENERATION ---
    full_prompt = (
        f"Persona: {selected_style['prompt']}\n"
        f"Task: Write a short social media post announcing your bet.\n"
        f"ADAPT this specific bizarre logic into your own words: '{chosen_theme}'.\n"
        f"You are locking in this exact ticket:\n{locked_bet_text}\n"
        f"CRITICAL RULES:\n"
        f"1. Keep it under 250 characters.\n"
        f"2. Do NOT say the teams in the parlay are playing each other. They are in completely separate games.\n"
        f"3. Do not write out the odds numbers. Do not use hashtags.\n"
        f"4. NEVER ask questions, apologize, offer options, or break character.\n"
        f"Output ONLY the final in-character text, nothing else."
    )

    quote = get_ai_text(full_prompt)

    if not quote or "Do you want me to" in quote or "Options:" in quote:
        print("⚠️ API broke character. Using fallback.")
        quote = random.choice(FALLBACK_QUOTES)

    final_post = f"{quote}\n\n{bet_type}: {final_odds_str}"
    print(f"📝 Final Drafted Pick:\n{final_post}")

    if random.random() < config.TEXT_ONLY_ODDS:
        print("   🎲 Dice Roll: decided on TEXT ONLY mode. Skipping image.")
        return final_post, None

    image_path = generate_and_download_goblin_image()
    return final_post, image_path
