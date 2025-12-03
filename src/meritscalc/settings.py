"""Enhanced settings manager with observers and advanced features."""

import json
import os
from pathlib import Path
from typing import Any


def _user_documents_dir() -> Path:
    """Get the user documents directory."""
    base = Path(os.environ.get("USERPROFILE", str(Path.home())))
    return base / "Documents"


def _app_data_dir() -> Path:
    """Get the application data directory."""
    d = _user_documents_dir() / "PINK" / "SCMeritCalc"
    d.mkdir(parents=True, exist_ok=True)
    return d


SETTINGS_FILE = str(_app_data_dir() / "settings.json")
LOG_FILE = str(_app_data_dir() / "ScMeritCalc.log")

DEFAULT_SETTINGS = {
    # Core calculation settings
    "rate_merits_seconds": 1.0,
    "rate_merits_auec": 0.618,
    "discount_percent": 0.0,
    "fee_percent": 0.5,
    # Window appearance and behavior
    "window_x": 100,
    "window_y": 100,
    "window_width": 500,
    "window_height": 720,
    "window_opacity": 0.9,
    "aspect_ratio_enforced": False,
    "aspect_ratio_width": 16,
    "aspect_ratio_height": 9,
    "always_on_top": False,
    # Window snapping and positioning
    "snap_to_edges": True,
    "snap_to_windows": False,
    "snap_distance": 20,
    "edge_snap_distance": 20,
    "window_snap_distance": 30,
    "show_snap_preview": True,
    # UI behavior
    "minimize_to_tray": False,
    # Transparency and visual effects
    "transparency_enabled": True,
    "transparency_default": 0.9,
    "transparency_min": 0.3,
    "transparency_max": 1.0,
    # High DPI and scaling
    "dpi_aware": True,
    "auto_scale_ui": True,
    "auto_scale_bias": 0.90,
    "ui_scale": 100.0,
    # Keyboard shortcuts (customizable)
    "shortcuts": {
        "save": {"ctrl": True, "shift": False, "alt": False, "key": "S"},
        "quit": {"ctrl": True, "shift": False, "alt": False, "key": "Q"},
        "copy_report": {"ctrl": True, "shift": False, "alt": False, "key": "C"},
        "clear": {"ctrl": True, "shift": False, "alt": False, "key": "R"},
        "minimize": {"ctrl": False, "shift": False, "alt": False, "key": "Escape"},
        "toggle_transparency": {"ctrl": True, "shift": True, "alt": False, "key": "T"},
        "toggle_always_on_top": {"ctrl": True, "shift": True, "alt": False, "key": "A"},
    },
    # Last used inputs
    "last_inputs": {
        "time_h": "00",
        "time_m": "00",
        "time_s": "00",
        "merits": "00",
        "auec": "00",
    },
    # File paths and preferences
    "default_report_path": "",
    "confirm_exit": True,
    # Performance settings
    "target_fps": 60,
    "vsync_enabled": True,
    "redraw_on_change": True,
}


class SettingsManager:
    """Enhanced settings manager with observers and advanced features."""

    def __init__(self):
        self._settings = DEFAULT_SETTINGS.copy()
        self._observers = []
        self._load_settings()

    def _load_settings(self):
        """Load settings from file."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._settings.update(loaded_settings)
        except (IOError, json.JSONDecodeError, OSError) as e:
            print(f"Error loading settings: {e}")
            # Keep defaults if loading fails

    def save_settings(self):
        """Save settings to file."""
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and notify observers."""
        self._settings[key] = value
        for observer in self._observers:
            try:
                observer(key, value)
            except (OSError, IOError) as e:
                print(f"Error in settings observer: {e}")
        self.save_settings()

    def add_observer(self, observer):
        """Add a settings change observer."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """Remove a settings change observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def bulk_update(self, updates):
        """Update multiple settings at once."""
        for key, value in updates.items():
            self._settings[key] = value

        # Notify observers for each change
        for key, value in updates.items():
            for observer in self._observers:
                try:
                    observer(key, value)
                except (OSError, IOError) as e:
                    print(f"Error in settings observer: {e}")

        # Always save
        self.save_settings()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = DEFAULT_SETTINGS.copy()
        self.save_settings()

        # Notify observers for all changed keys
        for key, value in self._settings.items():
            for observer in self._observers:
                try:
                    observer(key, value)
                except (OSError, IOError) as e:
                    print(f"Error in settings observer: {e}")

    def get_aspect_ratio(self):
        """Get current aspect ratio if enforced."""
        if self._settings.get("aspect_ratio_enforced", False):
            return (
                self._settings.get("aspect_ratio_width", 16),
                self._settings.get("aspect_ratio_height", 9),
            )
        return None

    def set_window_geometry(self, x, y, width, height):
        """Set window geometry settings."""
        updates = {
            "window_x": x,
            "window_y": y,
            "window_width": width,
            "window_height": height,
        }
        self.bulk_update(updates)

    def get_window_geometry(self):
        """Get window geometry settings."""
        return {
            "x": self._settings.get("window_x", 100),
            "y": self._settings.get("window_y", 100),
            "width": self._settings.get("window_width", 500),
            "height": self._settings.get("window_height", 720),
        }
