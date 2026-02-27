import pandas as pd
from sqlalchemy import create_engine, text
from . import config


def decimal_to_american(decimal_odds: float) -> str:
    """Goblins don't read decimal odds. Convert to American."""
    if decimal_odds >= 2.0:
        american = int(round((decimal_odds - 1.0) * 100.0))
        return f"+{american}"
    else:
        american = int(round(-100.0 / (decimal_odds - 1.0)))
        return str(american)


def abbreviate_team(name: str) -> str:
    """
    Converts single words to 3 letters ('Arsenal' -> 'ARS')
    and CamelCase to acronyms ('AstonVilla' -> 'AV', 'BrightonandHoveAlbion' -> 'BHA').
    """
    uppers = [char for char in name if char.isupper()]
    if len(uppers) > 1:
        return "".join(uppers)
    return name[:3].upper()


def get_sniper_bets() -> tuple[list[dict], list[int]]:
    """Fetches the SINGLE best PENDING bet from DB that hasn't started yet."""
    if not config.DATABASE_URL:
        print("⚠️ DATABASE_URL not set. Cannot run EV Sniper.")
        return [], []

    engine = create_engine(config.DATABASE_URL)

    query = text("""
        SELECT p.id, p.match_id, p.outcome, p.market_type, p.odds as dec_odds, p.ev,
               m.home_team, m.away_team, m.date_time_utc
        FROM daily_picks p
        JOIN matches m ON p.match_id = m.match_id
        WHERE p.status = 'PENDING'
        AND m.date_time_utc > NOW()
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        return [], []

    # ONLY GRAB THE TOP BET (1 EV Bet per Post)
    df = df.sort_values(by="ev", ascending=False).head(1)

    formatted_legs = []
    db_ids_to_update = []

    for _, row in df.iterrows():
        # Create compact abbreviations for Twitter
        home = abbreviate_team(row["home_team"])
        away = abbreviate_team(row["away_team"])

        # Handle the different markets properly with shortened names
        if row["market_type"] == "1X2":
            if row["outcome"] == "H":
                pick_name = home
            elif row["outcome"] == "A":
                pick_name = away
            else:
                pick_name = "Draw"
        elif row["market_type"] == "OU2.5":
            if row["outcome"] == "O":
                pick_name = "O 2.5G"
            else:
                pick_name = "U 2.5G"
        else:
            pick_name = str(row["outcome"])

        formatted_legs.append(
            {
                "game": f"{away} @ {home}",
                "pick": pick_name,
                "odds": decimal_to_american(row["dec_odds"]),
            }
        )
        db_ids_to_update.append(row["id"])

    return formatted_legs, db_ids_to_update


def mark_bets_placed(pick_ids: list[int]) -> None:
    """Updates the database so we don't tweet the same bet twice."""
    if not pick_ids or not config.DATABASE_URL:
        return

    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as conn:
        for pid in pick_ids:
            # Clean, fast primary key update
            conn.execute(
                text("UPDATE daily_picks SET status = 'PLACED' WHERE id = :pid"),
                {"pid": pid},
            )
        conn.commit()
