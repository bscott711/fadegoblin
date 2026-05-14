"""Renders a dark-themed bet card image showing all +EV plays with POTD highlight."""

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from fadegoblin import config

# ── Layout constants ──────────────────────────────────────────────────
CARD_WIDTH = 768
PADDING = 30
ROW_HEIGHT = 52
HEADER_HEIGHT = 90
FOOTER_HEIGHT = 50

# ── Colour palette ────────────────────────────────────────────────────
BG_COLOR = (18, 18, 24)
HEADER_BG = (24, 24, 36)
ROW_DARK = (26, 26, 38)
ROW_LIGHT = (32, 32, 46)
POTD_BG = (15, 60, 30)
POTD_BORDER = (0, 255, 100)
ACCENT_GREEN = (0, 255, 100)
TEXT_WHITE = (240, 240, 245)
TEXT_DIM = (160, 160, 175)
TEXT_EDGE = (100, 220, 130)
DIVIDER = (50, 50, 65)

# ── Font helpers ──────────────────────────────────────────────────────
_FONT_PATH = Path(__file__).parent / "assets" / "Inter.ttf"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load Inter if bundled, otherwise fall back to default."""
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except (OSError, IOError):
        return ImageFont.load_default()


def render_bet_card(legs: list[dict], potd_index: int) -> Path:
    """
    Renders all +EV legs onto a dark-themed card image.

    Parameters
    ----------
    legs : list[dict]
        Each dict has keys: game, pick, odds, edge.
    potd_index : int
        Index into ``legs`` for the Play of the Day row.

    Returns
    -------
    Path
        Path to the saved PNG.
    """
    num_rows = len(legs)
    table_top = HEADER_HEIGHT + 10
    col_header_h = 32
    table_body_top = table_top + col_header_h
    card_height = table_body_top + (num_rows * ROW_HEIGHT) + FOOTER_HEIGHT + PADDING

    img = Image.new("RGB", (CARD_WIDTH, card_height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_title = _load_font(26)
    font_date = _load_font(14)
    font_col = _load_font(13)
    font_row = _load_font(16)
    font_edge = _load_font(15)
    font_potd_label = _load_font(12)
    font_footer = _load_font(12)

    # ── Header ────────────────────────────────────────────────────────
    draw.rectangle([(0, 0), (CARD_WIDTH, HEADER_HEIGHT)], fill=HEADER_BG)

    title = "🎯  FADEGOBLIN EV BOARD"
    draw.text((PADDING, 20), title, fill=ACCENT_GREEN, font=font_title)

    date_str = datetime.now().strftime("%B %d, %Y")
    draw.text((PADDING, 56), date_str, fill=TEXT_DIM, font=font_date)

    # Subtle accent line under header
    draw.rectangle(
        [(PADDING, HEADER_HEIGHT - 3), (CARD_WIDTH - PADDING, HEADER_HEIGHT - 1)],
        fill=ACCENT_GREEN,
    )

    # ── Column headers ────────────────────────────────────────────────
    col_x = {"game": PADDING + 8, "pick": 420, "odds": 620}

    col_y = table_top + 8
    for label, x in [("MATCHUP", col_x["game"]), ("PICK", col_x["pick"]),
                     ("ODDS", col_x["odds"])]:
        draw.text((x, col_y), label, fill=TEXT_DIM, font=font_col)

    draw.line(
        [(PADDING, table_body_top - 1), (CARD_WIDTH - PADDING, table_body_top - 1)],
        fill=DIVIDER,
        width=1,
    )

    # ── Rows ──────────────────────────────────────────────────────────
    for i, leg in enumerate(legs):
        y = table_body_top + i * ROW_HEIGHT
        is_potd = i == potd_index

        # Row background
        if is_potd:
            draw.rectangle([(PADDING - 4, y), (CARD_WIDTH - PADDING + 4, y + ROW_HEIGHT - 2)], fill=POTD_BG)
            # Left accent bar
            draw.rectangle([(PADDING - 4, y), (PADDING, y + ROW_HEIGHT - 2)], fill=POTD_BORDER)
        else:
            bg = ROW_DARK if i % 2 == 0 else ROW_LIGHT
            draw.rectangle([(PADDING - 4, y), (CARD_WIDTH - PADDING + 4, y + ROW_HEIGHT - 2)], fill=bg)

        text_y = y + (ROW_HEIGHT - 2 - 18) // 2  # vertically centre 18px text

        # Game
        game_color = TEXT_WHITE if is_potd else TEXT_DIM
        draw.text((col_x["game"], text_y), leg["game"], fill=game_color, font=font_row)

        # Pick
        pick_color = ACCENT_GREEN if is_potd else TEXT_WHITE
        draw.text((col_x["pick"], text_y), leg["pick"], fill=pick_color, font=font_row)

        # Odds
        draw.text((col_x["odds"], text_y), str(leg["odds"]), fill=TEXT_WHITE, font=font_row)

        # POTD label
        if is_potd:
            label_y = y + 2
            label_x = CARD_WIDTH - PADDING - 4
            potd_text = "⭐ POTD"
            bbox = draw.textbbox((0, 0), potd_text, font=font_potd_label)
            tw = bbox[2] - bbox[0]
            draw.text((label_x - tw, label_y), potd_text, fill=ACCENT_GREEN, font=font_potd_label)

        # Divider between rows
        if i < num_rows - 1:
            line_y = y + ROW_HEIGHT - 2
            draw.line(
                [(PADDING + 8, line_y), (CARD_WIDTH - PADDING - 8, line_y)],
                fill=DIVIDER,
                width=1,
            )

    # ── Footer ────────────────────────────────────────────────────────
    footer_y = table_body_top + num_rows * ROW_HEIGHT + 12
    draw.text(
        (PADDING, footer_y),
        "@fadegoblin.bsky.social  •  powered by AlgoMLB",
        fill=TEXT_DIM,
        font=font_footer,
    )

    # ── Save ──────────────────────────────────────────────────────────
    output_path = config.BASE_DIR / "temp_card.png"
    img.save(str(output_path), "PNG")
    print(f"🃏 Card saved → {output_path} ({num_rows} plays, POTD row {potd_index})")
    return output_path
