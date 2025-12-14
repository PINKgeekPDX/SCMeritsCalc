"""Enhanced Star Citizen-inspired theme with holographic effects and animations."""

# Star Citizen Color Palette - Deep Space Theme (AAA Enhanced)
COLOR_BG_PRIMARY = "#06080a"  # Deeper space black
COLOR_BG_SECONDARY = "#0a0c0f"  # Dark panel background
COLOR_BG_TERTIARY = "#0f1419"  # Lighter panel background
COLOR_BG_PANEL = "#161b22"  # Panel background with slight glow
COLOR_BG_TRANSPARENT = "rgba(22, 27, 34, 0.85)"  # Semi-transparent holographic base

# Accent Colors - Star Citizen Blue/Cyan (More Vibrant)
COLOR_ACCENT_PRIMARY = "#00e8ff"  # Vibrant cyan
COLOR_ACCENT_SECONDARY = "#00b8e6"  # Medium cyan
COLOR_ACCENT_DARK = "#0078a8"  # Dark cyan
COLOR_ACCENT_GLOW = "#00ffff"  # Pure cyan glow
COLOR_ACCENT_LIGHT = "#00f0ff"  # Light cyan accent

# Additional Accents (Enhanced)
COLOR_ACCENT_GOLD = "#ffd700"  # Futuristic gold
COLOR_ACCENT_ORANGE = "#ffa500"  # Warning/alert orange
COLOR_ACCENT_PURPLE = "#9b59b6"  # Tech purple
COLOR_ACCENT_RED = "#ff4444"  # Error/alert red
COLOR_ACCENT_GREEN = "#20ff80"  # Success green

# Text Colors (Enhanced for AAA)
COLOR_TEXT_PRIMARY = "#f0f8ff"  # Bright white-blue
COLOR_TEXT_SECONDARY = "#b8d4ff"  # Soft blue-white
COLOR_TEXT_DIM = "#8fb8ff"  # Subdued blue
COLOR_TEXT_DISABLED = "#5a6e8a"  # Muted blue-gray
COLOR_TEXT_GLOW = "#00ffff"  # Glowing text effect

# Status Colors (More Vibrant)
COLOR_SUCCESS = "#20ff80"  # Vibrant green
COLOR_WARNING = "#ffcc00"  # Bright orange
COLOR_ERROR = "#ff4444"  # Intense red
COLOR_INFO = "#44aaff"  # Info blue

# Border Colors (Enhanced)
COLOR_BORDER_PRIMARY = "#00e8ff"
COLOR_BORDER_SECONDARY = "#0078a8"
COLOR_BORDER_DIM = "#003344"
COLOR_BORDER_GLOW = "#00ffff"

# Glow Effects (Enhanced Intensity)
GLOW_INTENSITY_LOW = "rgba(0, 232, 255, 0.2)"
GLOW_INTENSITY_MEDIUM = "rgba(0, 232, 255, 0.4)"
GLOW_INTENSITY_HIGH = "rgba(0, 232, 255, 0.7)"
GLOW_INTENSITY_MAX = "rgba(0, 255, 255, 0.9)"

# Holographic Effects
HOLOGRAPHIC_BASE = "rgba(22, 27, 34, 0.85)"
HOLOGRAPHIC_GRID = "rgba(0, 232, 255, 0.05)"
HOLOGRAPHIC_SCANLINE = "rgba(0, 232, 255, 0.1)"

# Fonts
FONT_FAMILY_PRIMARY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"
FONT_FAMILY_HEADER = "Segoe UI Semibold"

FONT_SIZE_XL = 18
FONT_SIZE_LG = 14
FONT_SIZE_MD = 11
FONT_SIZE_SM = 10
FONT_SIZE_XS = 9

# Animation Durations (ms)
ANIM_DURATION_FAST = 150
ANIM_DURATION_NORMAL = 300
ANIM_DURATION_SLOW = 500


# Get comprehensive stylesheet for the entire application
def get_main_stylesheet() -> str:
    """Get the main application stylesheet with enhanced AAA holographic effects."""
    return f"""
    /* Main Window */
    QMainWindow {{
        background-color: {COLOR_BG_PRIMARY};
        color: {COLOR_TEXT_PRIMARY};
    }}
    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-radius: 4px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_BG_SECONDARY}, stop:1 {COLOR_BG_TERTIARY});
        padding: 4px;
    }}

    QTabBar::tab {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_BG_TERTIARY}, stop:1 {COLOR_BG_SECONDARY});
        color: {COLOR_TEXT_DIM};
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 4px 12px;
        margin-right: 1px;
        font-weight: bold;
        font-size: {FONT_SIZE_XS}pt;
        min-width: 60px;
    }}

    QTabBar::tab:selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_ACCENT_PRIMARY}, stop:1 {COLOR_ACCENT_SECONDARY});
        color: {COLOR_BG_PRIMARY};
        border-color: {COLOR_ACCENT_PRIMARY};
    }}

    QTabBar::tab:hover:!selected {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_BG_PANEL}, stop:1 {COLOR_BG_TERTIARY});
        color: {COLOR_TEXT_PRIMARY};
        border-color: {COLOR_ACCENT_SECONDARY};
    }}

    /* Group Boxes - Holographic Panels */
    QGroupBox {{
        color: {COLOR_TEXT_SECONDARY};
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-radius: 4px;
        margin-top: 4px;
        padding-top: 6px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(26, 31, 40, 0.8), stop:1 rgba(15, 20, 25, 0.9));
        font-weight: bold;
        font-size: {FONT_SIZE_XS}pt;
    }}

    QGroupBox:title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {COLOR_ACCENT_PRIMARY};
        background: transparent;
        border: none;
    }}

    QGroupBox:hover {{
        border-color: {COLOR_ACCENT_PRIMARY};
    }}

    /* Line Edits - Holographic Input Fields */
    QLineEdit {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(26, 31, 40, 0.9), stop:1 rgba(15, 20, 25, 0.95));
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-radius: 4px;
        padding: 4px 6px;
        font-size: {FONT_SIZE_SM}pt;
        font-weight: bold;
        selection-background-color: {COLOR_ACCENT_SECONDARY};
        selection-color: {COLOR_BG_PRIMARY};
    }}

    QLineEdit:focus {{
        border: 2px solid {COLOR_ACCENT_PRIMARY};
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(0, 217, 255, 0.1), stop:1 rgba(15, 20, 25, 0.95));
    }}

    QLineEdit[mode="auto"] {{
        border-color: {COLOR_ACCENT_PRIMARY};
    }}

    QLineEdit[mode="manual"] {{
        border-color: {COLOR_ACCENT_GOLD};
    }}

    QLineEdit:hover {{
        border-color: {COLOR_ACCENT_SECONDARY};
    }}

    /* Labels */
    QLabel {{
        color: {COLOR_TEXT_PRIMARY};
        background: transparent;
    }}

    QLabel[class="header"] {{
        color: {COLOR_ACCENT_PRIMARY};
        font-size: {FONT_SIZE_LG}pt;
        font-weight: bold;
    }}

    QLabel[class="value"] {{
        color: {COLOR_TEXT_PRIMARY};
        font-size: {FONT_SIZE_XL}pt;
        font-weight: bold;
    }}

    QLabel[class="output"] {{
        color: {COLOR_ACCENT_PRIMARY};
        font-size: 36pt;
        font-weight: bold;
    }}

    /* Push Buttons - Glowing Sci-Fi Buttons */
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_BG_PANEL}, stop:1 {COLOR_BG_SECONDARY});
        color: {COLOR_TEXT_PRIMARY};
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-radius: 4px;
        padding: 4px 8px;
        font-weight: bold;
        font-size: {FONT_SIZE_XS}pt;
        min-width: 60px;
        min-height: 24px;
    }}

    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_ACCENT_SECONDARY}, stop:1 {COLOR_ACCENT_DARK});
        border-color: {COLOR_ACCENT_PRIMARY};
        color: {COLOR_BG_PRIMARY};
    }}

    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_ACCENT_PRIMARY}, stop:1 {COLOR_ACCENT_SECONDARY});
        border-color: {COLOR_ACCENT_GLOW};
    }}

    QPushButton:disabled {{
        background: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_DISABLED};
        border-color: {COLOR_BORDER_DIM};
    }}

    /* Checkboxes */
    QCheckBox {{
        color: {COLOR_TEXT_PRIMARY};
        spacing: 6px;
        font-size: {FONT_SIZE_SM}pt;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-radius: 3px;
        background: {COLOR_BG_SECONDARY};
    }}

    QCheckBox::indicator:hover {{
        border-color: {COLOR_ACCENT_SECONDARY};
        background: {COLOR_BG_PANEL};
    }}

    QCheckBox::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_ACCENT_PRIMARY}, stop:1 {COLOR_ACCENT_SECONDARY});
        border-color: {COLOR_ACCENT_PRIMARY};
        image: none;
    }}

    QCheckBox::indicator:checked:hover {{
    }}

    /* Sliders */
    QSlider::groove:horizontal {{
        border: 1px solid {COLOR_BORDER_SECONDARY};
        height: 8px;
        background: {COLOR_BG_SECONDARY};
        border-radius: 4px;
    }}

    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_ACCENT_PRIMARY}, stop:1 {COLOR_ACCENT_SECONDARY});
        border: 2px solid {COLOR_ACCENT_PRIMARY};
        width: 20px;
        height: 20px;
        margin: -6px 0;
        border-radius: 10px;
    }}

    QSlider::handle:horizontal:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_ACCENT_GLOW}, stop:1 {COLOR_ACCENT_PRIMARY});
    }}

    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_ACCENT_SECONDARY}, stop:1 {COLOR_ACCENT_PRIMARY});
        border-radius: 4px;
    }}

    /* Spin Boxes */
    QDoubleSpinBox, QSpinBox {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(26, 31, 40, 0.9), stop:1 rgba(15, 20, 25, 0.95));
        color: {COLOR_TEXT_PRIMARY};
        border: 2px solid {COLOR_BORDER_SECONDARY};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: {FONT_SIZE_MD}pt;
        selection-background-color: {COLOR_ACCENT_SECONDARY};
    }}

    QDoubleSpinBox:focus, QSpinBox:focus {{
        border-color: {COLOR_ACCENT_PRIMARY};
    }}

    QDoubleSpinBox::up-button, QSpinBox::up-button {{
        background: {COLOR_BG_SECONDARY};
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-top-right-radius: 4px;
        width: 20px;
    }}

    QDoubleSpinBox::down-button, QSpinBox::down-button {{
        background: {COLOR_BG_SECONDARY};
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-bottom-right-radius: 4px;
        width: 20px;
    }}

    QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
    QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
        background: {COLOR_ACCENT_SECONDARY};
        border-color: {COLOR_ACCENT_PRIMARY};
    }}

    /* Progress Bars */
    QProgressBar {{
        border: 2px solid {COLOR_BORDER_SECONDARY};
        border-radius: 6px;
        text-align: center;
        background: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
        font-weight: bold;
        height: 24px;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_ACCENT_SECONDARY}, stop:1 {COLOR_ACCENT_PRIMARY});
        border-radius: 4px;
    }}

    /* Scroll Areas */
    QScrollArea {{
        border: 1px solid {COLOR_BORDER_SECONDARY};
        border-radius: 6px;
        background: {COLOR_BG_SECONDARY};
    }}

    QScrollBar:vertical {{
        background: {COLOR_BG_SECONDARY};
        width: 12px;
        border: none;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER_SECONDARY};
        min-height: 30px;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {COLOR_ACCENT_SECONDARY};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Table Widgets */
    QTableWidget {{
        background: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 2px solid {COLOR_BORDER_SECONDARY};
        border-radius: 6px;
        gridline-color: {COLOR_BORDER_DIM};
        font-size: {FONT_SIZE_SM}pt;
    }}

    QTableWidget::item {{
        padding: 6px;
        border: none;
    }}

    QTableWidget::item:selected {{
        background: {COLOR_ACCENT_SECONDARY};
        color: {COLOR_BG_PRIMARY};
    }}

    QHeaderView::section {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_BG_PANEL}, stop:1 {COLOR_BG_SECONDARY});
        color: {COLOR_ACCENT_PRIMARY};
        padding: 8px;
        border: 1px solid {COLOR_BORDER_SECONDARY};
        font-weight: bold;
        font-size: {FONT_SIZE_SM}pt;
    }}

    /* Text Edit */
    QTextEdit {{
        background: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT_PRIMARY};
        border: 2px solid {COLOR_BORDER_SECONDARY};
        border-radius: 6px;
        padding: 8px;
        font-size: {FONT_SIZE_SM}pt;
        selection-background-color: {COLOR_ACCENT_SECONDARY};
    }}

    QTextEdit:focus {{
        border-color: {COLOR_ACCENT_PRIMARY};
    }}

    /* Dialog */
    QDialog {{
        background-color: {COLOR_BG_PRIMARY};
        color: {COLOR_TEXT_PRIMARY};
    }}

    /* Dialog Button Box */
    QDialogButtonBox QPushButton {{
        min-width: 80px;
        padding: 8px 16px;
    }}
    """


def get_dialog_stylesheet() -> str:
    """Get stylesheet specifically for dialogs."""
    return (
        get_main_stylesheet()
        + f"""
    QDialog {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {COLOR_BG_SECONDARY}, stop:1 {COLOR_BG_PRIMARY});
    }}
    """
    )
