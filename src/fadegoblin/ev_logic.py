import pandas as pd
from sqlalchemy import create_engine, text

from fadegoblin import config


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


def get_sniper_bets() -> tuple[list[dict], list[str]]:
    """Fetches the SINGLE best PENDING bet from AlgoMLB DB that hasn't started yet."""
    if not config.DATABASE_URL:
        print("⚠️ DATABASE_URL not set. Cannot run EV Sniper.")
        return [], []

    engine = create_engine(config.DATABASE_URL)

    # Adapted to AlgoMLB's bankroll_ledger and game_results schema
    query = text("""
        SELECT b.transaction_id as id, b.game_id as match_id, b.selection as outcome,
               'ML' as market_type, b.odds as dec_odds, b.edge as ev,
               g.home_team, g.away_team, g.game_datetime as date_time_utc
        FROM bankroll_ledger b
        JOIN game_results g ON b.game_id = g.game_id
        WHERE b.status = 'PENDING'
        AND g.game_datetime > NOW()
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        return [], []

    # ONLY GRAB THE TOP BET (1 EV Bet per Post) based on AlgoMLB's calculated edge
    df = df.sort_values(by="ev", ascending=False).head(1)

    formatted_legs = []
    db_ids_to_update = []

    for _, row in df.iterrows():
        # Create compact abbreviations for Twitter
        home = abbreviate_team(row["home_team"])
        away = abbreviate_team(row["away_team"])

        pick_name = str(row["outcome"])
        if pick_name == row["home_team"]:
            pick_name = home
        elif pick_name == row["away_team"]:
            pick_name = away

        formatted_legs.append(
            {
                "game": f"{away} @ {home}",
                "pick": pick_name,
                "odds": decimal_to_american(row["dec_odds"]),
            }
        )
        db_ids_to_update.append(str(row["id"]))

    return formatted_legs, db_ids_to_update


def mark_bets_placed(pick_ids: list[str]) -> None:
    """Updates the AlgoMLB ledger so we don't tweet the same bet twice."""
    if not pick_ids or not config.DATABASE_URL:
        return

    engine = create_engine(config.DATABASE_URL)
    with engine.connect() as conn:
        for pid in pick_ids:
            # Updates AlgoMLB's bankroll_ledger status
            conn.execute(
                text(
                    "UPDATE bankroll_ledger SET status = 'PLACED' WHERE transaction_id = :pid"
                ),
                {"pid": pid},
            )
        conn.commit()
