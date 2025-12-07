import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch

from src.meritscalc.settings import SettingsManager, DEFAULT_SETTINGS

class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = Path(self.temp_dir) / "settings.json"
        
        # Patch the SETTINGS_FILE constant in the module
        self.patcher = patch('src.meritscalc.settings.SETTINGS_FILE', str(self.settings_file))
        self.patcher.start()
        
        self.settings = SettingsManager()

    def tearDown(self):
        self.patcher.stop()
        if self.settings_file.exists():
            self.settings_file.unlink()
        if Path(self.temp_dir).exists():
            try:
                Path(self.temp_dir).rmdir()
            except OSError:
                pass

    def test_default_values(self):
        self.assertEqual(self.settings.get("rate_merits_seconds"), 1.0)
        self.assertEqual(self.settings.get("fee_percent"), 0.5)

    def test_set_and_get(self):
        self.settings.set("test_key", "test_value")
        self.assertEqual(self.settings.get("test_key"), "test_value")

    def test_persistence(self):
        self.settings.set("rate_merits_seconds", 2.0)
        
        # Create a new instance, should load from file
        new_settings = SettingsManager()
        self.assertEqual(new_settings.get("rate_merits_seconds"), 2.0)

    def test_observer(self):
        observed = {}
        def observer(k, v):
            observed[k] = v
        
        self.settings.add_observer(observer)
        self.settings.set("fee_percent", 1.0)
        self.assertEqual(observed.get("fee_percent"), 1.0)

    def test_geometry(self):
        self.settings.set_window_geometry(10, 20, 300, 400)
        geo = self.settings.get_window_geometry()
        self.assertEqual(geo["x"], 10)
        self.assertEqual(geo["y"], 20)
        self.assertEqual(geo["width"], 300)
        self.assertEqual(geo["height"], 400)

if __name__ == "__main__":
    unittest.main()


