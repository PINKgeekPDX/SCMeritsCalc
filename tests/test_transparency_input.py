import unittest

from src.meritscalc.settings import SettingsManager
from src.meritscalc.logic import MeritsCalculator
from src.meritscalc.ui import MeritsImGuiApp


class TestTransparency(unittest.TestCase):
    def test_opacity_slider_updates_setting(self):
        sm = SettingsManager()
        calc = MeritsCalculator()
        app = MeritsImGuiApp(sm, calc)
        app._init_window()
        sm.set("window_opacity", 0.8)
        app._shutdown()
        sm2 = SettingsManager()
        self.assertAlmostEqual(sm2.get("window_opacity"), 0.8, places=2)


if __name__ == "__main__":
    unittest.main()
