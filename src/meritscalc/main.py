"""MeritsCalc application entry point and utilities."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from meritscalc.logic import MeritsCalculator
from meritscalc.qt_ui import create_qt_app
from meritscalc.settings import LOG_FILE, SettingsManager


def create_enhanced_icon():
    """Create enhanced system tray icon."""
    width = 64
    height = 64
    bg_color = (11, 13, 18, 255)
    accent_color = (0, 217, 255, 255)

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    # Gradient ring background; keep bounds valid
    for i in range(28):  # ensures x1 >= x0
        alpha = int(255 * (1 - i / 28))
        x0 = 4 + i
        y0 = 4 + i
        x1 = 60 - i
        y1 = 60 - i
        dc.ellipse(
            (x0, y0, x1, y1),
            fill=(bg_color[0], bg_color[1], bg_color[2], alpha),
            outline=(accent_color[0], accent_color[1], accent_color[2], alpha),
            width=2,
        )

    center_x, center_y = 32, 32
    points = [
        (center_x - 8, center_y - 12),
        (center_x + 2, center_y - 4),
        (center_x - 2, center_y + 4),
        (center_x + 8, center_y + 12),
        (center_x - 2, center_y + 4),
        (center_x + 2, center_y - 4),
        (center_x - 8, center_y - 12),
    ]

    dc.polygon(points, fill=accent_color)

    return image


def run_enhanced_tray(_app, _icon_image) -> None:
    """Placeholder for future system tray integration."""
    return None


def setup_logging():
    """Configure application logging to file and stdout."""
    log_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.getLogger("PIL").setLevel(logging.WARNING)


def main() -> None:
    """Launch the MeritsCalc Qt application."""
    setup_logging()
    logging.info("Starting MeritsCalc Enhanced")
    settings = SettingsManager()
    logging.info("Settings manager initialized")
    calculator = MeritsCalculator()
    app = create_qt_app(settings, calculator)
    logging.info("Qt app created successfully")
    app.run()
    logging.info("Application shutdown complete")


if __name__ == "__main__":
    main()
