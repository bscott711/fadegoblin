import random
from datetime import datetime
from typing import Any

from .llm import get_ai_text
from .prompts import FALLBACK_QUOTES, PERSONAS


def generate_post_content(
    chosen_legs: list[dict[str, Any]], final_odds_str: str
) -> str:
    """Generates the social media post content based on the selected legs."""
    if not chosen_legs:
        return random.choice(FALLBACK_QUOTES)

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
    return final_post
