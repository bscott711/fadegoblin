"""Renders a compact, dark-themed bet card image showing all +EV plays."""

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from fadegoblin import config

# ── Layout constants ──────────────────────────────────────────────────
CARD_WIDTH = 480  # Much narrower
PADDING = 20
ROW_HEIGHT = 44
HEADER_HEIGHT = 60
FOOTER_HEIGHT = 36

# ── Colour palette ────────────────────────────────────────────────────
BG_COLOR = (18, 18, 24)
ROW_DARK = (26, 26, 38)
ROW_LIGHT = (32, 32, 46)
POTD_BG = (15, 60, 30)
POTD_BORDER = (0, 255, 100)
ACCENT_GREEN = (0, 255, 100)
TEXT_WHITE = (240, 240, 245)
TEXT_DIM = (160, 160, 175)
DIVIDER = (50, 50, 65)

# ── Font helpers ──────────────────────────────────────────────────────
_FONT_PATH = Path(__file__).parent / "assets" / "Inter.ttf"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load Inter if bundled, otherwise fall back to default."""
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except (OSError, IOError):
        return ImageFont.load_default()


def render_bet_card(legs: list[dict], potd_index: int, background_path: Path | None = None) -> Path:
    """
    Renders a compact card overlay.
    """
    num_rows = len(legs)
    col_header_h = 28
    
    # Base table height calculation
    base_table_height = HEADER_HEIGHT + col_header_h + (num_rows * ROW_HEIGHT) + FOOTER_HEIGHT + 10
    
    if background_path and background_path.exists():
        # Load and fit background to card dimensions
        bg_img = Image.open(background_path).convert("RGB")
        target_h = max(1024, base_table_height + 300) 
        img = ImageOps.fit(bg_img, (768, target_h), centering=(0.5, 0.4))
        card_height = target_h
        canvas_width = 768
    else:
        img = Image.new("RGB", (CARD_WIDTH, base_table_height), BG_COLOR)
        card_height = base_table_height
        canvas_width = CARD_WIDTH

    draw = ImageDraw.Draw(img)
    
    # If we have a background, we'll draw the table in a rounded box at the bottom
    if background_path:
        table_x1 = (canvas_width - CARD_WIDTH) // 2
        table_x2 = table_x1 + CARD_WIDTH
        table_y2 = card_height - 30
        table_y1 = table_y2 - base_table_height
        
        draw.rounded_rectangle([table_x1, table_y1, table_x2, table_y2], radius=12, fill=(10, 10, 15, 230))
        x_offset = table_x1
        y_offset = table_y1
    else:
        x_offset = 0
        y_offset = 0

    table_top = y_offset + HEADER_HEIGHT
    table_body_top = table_top + col_header_h

    font_title = _load_font(18)
    font_date = _load_font(11)
    font_col = _load_font(11)
    font_row = _load_font(14)
    font_footer = _load_font(10)

    # ── Header ────────────────────────────────────────────────────────
    title = "💚  THE GOBLIN'S MANIC SLIP"
    draw.text((x_offset + PADDING, y_offset + 12), title, fill=ACCENT_GREEN, font=font_title)

    date_str = datetime.now().strftime("%B %d, %Y")
    draw.text((x_offset + PADDING, y_offset + 38), date_str, fill=TEXT_DIM, font=font_date)

    # ── Column headers ────────────────────────────────────────────────
    col_x = {"matchup": x_offset + PADDING + 4, "odds": x_offset + CARD_WIDTH - PADDING - 60}

    col_y = table_top + 4
    draw.text((col_x["matchup"], col_y), "MATCHUP (PICK BOLD)", fill=TEXT_DIM, font=font_col)
    draw.text((col_x["odds"], col_y), "ODDS", fill=TEXT_DIM, font=font_col)

    draw.line(
        [(x_offset + PADDING, table_body_top - 1), (x_offset + CARD_WIDTH - PADDING, table_body_top - 1)],
        fill=DIVIDER,
        width=1,
    )

    # ── Rows ──────────────────────────────────────────────────────────
    for i, leg in enumerate(legs):
        y = table_body_top + i * ROW_HEIGHT
        is_potd = i == potd_index

        if is_potd:
            draw.rectangle([(x_offset + 8, y), (x_offset + CARD_WIDTH - 8, y + ROW_HEIGHT - 2)], fill=POTD_BG)
            draw.rectangle([(x_offset + 8, y), (x_offset + 12, y + ROW_HEIGHT - 2)], fill=POTD_BORDER)
        else:
            bg = ROW_DARK if i % 2 == 0 else ROW_LIGHT
            draw.rectangle([(x_offset + 8, y), (x_offset + CARD_WIDTH - 8, y + ROW_HEIGHT - 2)], fill=bg)

        text_y = y + (ROW_HEIGHT - 2 - 16) // 2

        # Matchup with Highlighted Pick
        game_text = leg["game"]  # e.g. "SEA @ HOU"
        pick_text = leg["pick"]  # e.g. "HOU"
        
        # Split game into parts
        parts = game_text.split(" @ ")
        if len(parts) == 2:
            away, home = parts
            away_color = ACCENT_GREEN if pick_text == away else (TEXT_WHITE if is_potd else TEXT_DIM)
            home_color = ACCENT_GREEN if pick_text == home else (TEXT_WHITE if is_potd else TEXT_DIM)
            
            draw.text((col_x["matchup"], text_y), away, fill=away_color, font=font_row)
            
            # Draw "@"
            bbox = draw.textbbox((0, 0), away, font=font_row)
            at_x = col_x["matchup"] + (bbox[2] - bbox[0]) + 6
            draw.text((at_x, text_y), "@", fill=TEXT_DIM, font=font_row)
            
            # Draw home
            bbox_at = draw.textbbox((0, 0), "@", font=font_row)
            home_x = at_x + (bbox_at[2] - bbox_at[0]) + 6
            draw.text((home_x, text_y), home, fill=home_color, font=font_row)
        else:
            draw.text((col_x["matchup"], text_y), game_text, fill=TEXT_WHITE, font=font_row)

        # Odds
        draw.text((col_x["odds"], text_y), str(leg["odds"]), fill=TEXT_WHITE, font=font_row)

        # POTD badge
        if is_potd:
            potd_tag_y = y + 2
            potd_tag_x = x_offset + CARD_WIDTH - 15
            draw.text((potd_tag_x - 35, potd_tag_y), "POTD", fill=ACCENT_GREEN, font=font_footer)

    # ── Footer ────────────────────────────────────────────────────────
    footer_y = y_offset + base_table_height - 24
    draw.text(
        (x_offset + PADDING, footer_y),
        "@fadegoblin  •  AlgoMLB",
        fill=TEXT_DIM,
        font=font_footer,
    )

    # ── Save ──────────────────────────────────────────────────────────
    output_path = config.BASE_DIR / "temp_card.png"
    img.save(str(output_path), "PNG")
    return output_path
