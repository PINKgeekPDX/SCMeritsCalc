import unittest
import glfw

from src.meritscalc.settings import SettingsManager
from src.meritscalc.logic import MeritsCalculator
from src.meritscalc.ui import MeritsImGuiApp


class TestDPIScaling(unittest.TestCase):
    def test_content_scale_readable(self):
        sm = SettingsManager()
        calc = MeritsCalculator()
        app = MeritsImGuiApp(sm, calc)
        app._init_window()
        sx, sy = glfw.get_window_content_scale(app.window)
        self.assertTrue(sx > 0 and sy > 0)
        app._shutdown()


if __name__ == "__main__":
    unittest.main()
