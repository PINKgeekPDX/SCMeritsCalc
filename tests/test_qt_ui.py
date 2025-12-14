import unittest
import sys
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

from src.meritscalc.qt_ui import QtMeritCalcApp
from src.meritscalc.settings import SettingsManager
from src.meritscalc.logic import MeritsCalculator

# Create QApplication instance if it doesn't exist
app = QApplication.instance() or QApplication(sys.argv)


class TestQtUI(unittest.TestCase):
    def setUp(self):
        self.settings = MagicMock(spec=SettingsManager)
        # Mock settings.get to return safe defaults
        self.settings.get.side_effect = lambda k, d=None: {
            "rate_merits_seconds": 1.0,
            "rate_merits_auec": 0.618,
            "fee_percent": 0.5,
            "ui_scale": 100,
            "font_size": 12,
            "window_transparency": 1.0,
            "shortcuts": {},
        }.get(k, d)

        self.settings.get_window_geometry.return_value = {
            "x": 100,
            "y": 100,
            "width": 800,
            "height": 600,
        }

        self.calculator = MeritsCalculator()

        # Patch QSystemTrayIcon to avoid system tray issues in test env
        with patch("src.meritscalc.qt_ui.QSystemTrayIcon"):
            self.window = QtMeritCalcApp(self.settings, self.calculator)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def test_initial_state(self):
        self.assertEqual(self.window.in_hours.text(), "00")
        self.assertEqual(self.window.in_minutes.text(), "00")

    def test_calculation_from_time(self):
        # 1 hour = 3600 seconds. rate = 1.0. merits = 3600.
        self.window.in_hours.setText("01")
        self.window.in_minutes.setText("00")
        self.window._on_time_edited()  # Simulate edit

        self.assertEqual(self.window.in_merits.text(), "3600")

    def test_calculation_from_merits(self):
        # 3600 merits = 1 hour
        self.window.in_merits.setText("3600")
        self.window._on_merits_edited()  # Simulate edit

        self.assertEqual(self.window.in_hours.text(), "01")
        self.assertEqual(self.window.in_minutes.text(), "00")

    def test_outputs_format(self):
        # 1000 merits. fee 0.5% = 5. total 1005.
        # auec 0.618 * 1000 = 618.
        self.window.in_merits.setText("1000")
        self.window._calculate()

        self.assertIn("1,005", self.window.out_merits_fee.text())
        self.assertIn("618", self.window.out_auec.text())


if __name__ == "__main__":
    unittest.main()
