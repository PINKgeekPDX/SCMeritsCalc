import unittest

from src.meritscalc.settings import SettingsManager
from src.meritscalc.logic import MeritsCalculator
from src.meritscalc.ui import MeritsImGuiApp


class TestSettingsPersistence(unittest.TestCase):
    def test_geometry_persists(self):
        sm = SettingsManager()
        calc = MeritsCalculator()
        app = MeritsImGuiApp(sm, calc)
        app._init_window()
        app._set_window_pos(123, 234, 640, 480)
        app._shutdown()
        sm2 = SettingsManager()
        self.assertEqual(sm2.get("window_x"), 123)
        self.assertEqual(sm2.get("window_y"), 234)
        self.assertEqual(sm2.get("window_width"), 640)
        self.assertEqual(sm2.get("window_height"), 480)

    def test_shortcuts_persist(self):
        sm = SettingsManager()
        shortcuts = sm.get("shortcuts")
        shortcuts["save"] = {"ctrl": True, "shift": True, "alt": False, "key": "S"}
        sm.set("shortcuts", shortcuts)
        sm2 = SettingsManager()
        self.assertTrue(sm2.get("shortcuts")["save"]["shift"]) 


if __name__ == "__main__":
    unittest.main()
