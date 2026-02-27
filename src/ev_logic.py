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


def get_sniper_bets() -> tuple[list[dict], list[int]]:
    """Fetches PENDING bets from DB that haven't started yet."""
    if not config.DATABASE_URL:
        print("⚠️ DATABASE_URL not set. Cannot run EV Sniper.")
        return [], []

    engine = create_engine(config.DATABASE_URL)

    # We can use p.id again!
    query = text("""
        SELECT p.id, p.match_id, p.outcome, p.odds as dec_odds, p.ev,
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
    df = df.sort_values(by="ev", ascending=False).head(1)
    formatted_legs = []
    db_ids_to_update = []

    for _, row in df.iterrows():
        if row["outcome"] == "H":
            pick_name = row["home_team"]
        elif row["outcome"] == "A":
            pick_name = row["away_team"]
        else:
            pick_name = "Draw"

        formatted_legs.append(
            {
                "game": f"{row['away_team']} @ {row['home_team']}",
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
