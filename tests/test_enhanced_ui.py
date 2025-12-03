import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.meritscalc.settings import SettingsManager, DEFAULT_SETTINGS
from src.meritscalc.ui_new import EnhancedMeritsApp

class TestSettingsManager(unittest.TestCase):
    """Test the enhanced SettingsManager."""
    
    def setUp(self):
        """Setup test environment."""
        # Create temporary directory for test settings
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = Path(self.temp_dir) / "test_settings.json"
        
        # Mock the settings file path
        with patch('src.meritscalc.settings.SETTINGS_FILE', str(self.settings_file)):
            self.settings = SettingsManager()
    
    def tearDown(self):
        """Cleanup test environment."""
        # Remove temporary files
        if self.settings_file.exists():
            self.settings_file.unlink()
        if Path(self.temp_dir).exists():
            Path(self.temp_dir).rmdir()
    
    def test_default_settings_loaded(self):
        """Test that default settings are loaded."""
        self.assertEqual(self.settings.get("rate_merits_auec"), 0.618)
        self.assertEqual(self.settings.get("window_opacity"), 0.9)
        self.assertTrue(self.settings.get("snap_to_edges"))
        self.assertFalse(self.settings.get("snap_to_windows"))
    
    def test_settings_observer(self):
        """Test settings observer functionality."""
        observer_called = False
        observed_key = None
        observed_value = None
        
        def test_observer(key, value):
            nonlocal observer_called, observed_key, observed_value
            observer_called = True
            observed_key = key
            observed_value = value
        
        self.settings.add_observer(test_observer)
        self.settings.set("test_key", "test_value")
        
        self.assertTrue(observer_called)
        self.assertEqual(observed_key, "test_key")
        self.assertEqual(observed_value, "test_value")
    
    def test_bulk_settings_update(self):
        """Test bulk settings update."""
        settings_dict = {
            "window_opacity": 0.8,
            "always_on_top": True,
            "snap_to_edges": False
        }
        
        old_values = self.settings.set_bulk(settings_dict)
        
        # Check new values are set
        self.assertEqual(self.settings.get("window_opacity"), 0.8)
        self.assertTrue(self.settings.get("always_on_top"))
        self.assertFalse(self.settings.get("snap_to_edges"))
        
        # Check old values are returned
        self.assertEqual(old_values["window_opacity"], 0.9)
        self.assertEqual(old_values["always_on_top"], False)
        self.assertEqual(old_values["snap_to_edges"], True)
    
    def test_shortcut_management(self):
        """Test keyboard shortcut management."""
        # Test getting shortcut
        shortcut = self.settings.get_shortcut("save")
        self.assertEqual(shortcut["ctrl"], True)
        self.assertEqual(shortcut["key"], "S")
        
        # Test setting shortcut
        new_shortcut = {"ctrl": False, "shift": True, "alt": False, "key": "X"}
        self.settings.set_shortcut("test_action", new_shortcut)
        
        retrieved_shortcut = self.settings.get_shortcut("test_action")
        self.assertEqual(retrieved_shortcut, new_shortcut)
        
        # Test shortcut matching
        self.assertTrue(self.settings.is_shortcut_pressed("save", True, False, False, "S"))
        self.assertFalse(self.settings.is_shortcut_pressed("save", False, False, False, "S"))
    
    def test_window_geometry_management(self):
        """Test window geometry management."""
        geometry = self.settings.get_window_geometry()
        
        self.assertIn("window_x", geometry)
        self.assertIn("window_y", geometry)
        self.assertIn("window_width", geometry)
        self.assertIn("window_height", geometry)
        
        # Test setting window geometry
        self.settings.set_window_geometry(200, 300, 800, 600)
        
        new_geometry = self.settings.get_window_geometry()
        self.assertEqual(new_geometry["window_x"], 200)
        self.assertEqual(new_geometry["window_y"], 300)
        self.assertEqual(new_geometry["window_width"], 800)
        self.assertEqual(new_geometry["window_height"], 600)
    
    def test_aspect_ratio_management(self):
        """Test aspect ratio management."""
        # Test disabled aspect ratio
        self.assertIsNone(self.settings.get_aspect_ratio())
        
        # Test enabled aspect ratio
        self.settings.set("aspect_ratio_enforced", True)
        self.settings.set("aspect_ratio_width", 16)
        self.settings.set("aspect_ratio_height", 9)
        
        aspect_ratio = self.settings.get_aspect_ratio()
        self.assertEqual(aspect_ratio, (16, 9))
        
        # Test setting aspect ratio
        self.settings.set_aspect_ratio(4, 3)
        self.assertEqual(self.settings.get("aspect_ratio_width"), 4)
        self.assertEqual(self.settings.get("aspect_ratio_height"), 3)
    
    def test_settings_persistence(self):
        """Test settings persistence."""
        # Change some settings
        self.settings.set("window_opacity", 0.75)
        self.settings.set("always_on_top", True)
        
        # Create new settings manager (should load from file)
        with patch('src.meritscalc.settings.SETTINGS_FILE', str(self.settings_file)):
            new_settings = SettingsManager()
        
        # Check settings were persisted
        self.assertEqual(new_settings.get("window_opacity"), 0.75)
        self.assertTrue(new_settings.get("always_on_top"))


class TestEnhancedUI(unittest.TestCase):
    """Test the enhanced UI functionality."""
    
    def setUp(self):
        """Setup test environment."""
        # Mock settings manager
        self.settings = Mock(spec=SettingsManager)
        self.settings.get.return_value = None
        self.settings.get_window_geometry.return_value = {
            "window_x": 100, "window_y": 100, "window_width": 500, "window_height": 720
        }
        
        # Mock DPG functions
        self.dpg_patcher = patch('src.meritscalc.ui_new.dpg')
        self.mock_dpg = self.dpg_patcher.start()
        
        # Mock other dependencies
        self.ctypes_patcher = patch('src.meritscalc.ui_new.ctypes')
        self.mock_ctypes = self.ctypes_patcher.start()
        
        self.win32_patcher = patch('src.meritscalc.ui_new.win32gui')
        self.mock_win32 = self.win32_patcher.start()
    
    def tearDown(self):
        """Cleanup test environment."""
        self.dpg_patcher.stop()
        self.ctypes_patcher.stop()
        self.win32_patcher.stop()
    
    def test_app_initialization(self):
        """Test app initialization."""
        app = EnhancedMeritsApp(self.settings)
        
        # Verify DPG was configured
        self.mock_dpg.create_context.assert_called_once()
        self.mock_dpg.create_viewport.assert_called_once()
        self.mock_dpg.setup_dearpygui.assert_called_once()
        self.mock_dpg.show_viewport.assert_called_once()
    
    def test_window_geometry_initialization(self):
        """Test window geometry initialization."""
        app = EnhancedMeritsApp(self.settings)
        
        # Verify viewport was created with correct geometry
        viewport_call = self.mock_dpg.create_viewport.call_args
        self.assertEqual(viewport_call[1]['width'], 500)
        self.assertEqual(viewport_call[1]['height'], 720)
        self.assertEqual(viewport_call[1]['x_pos'], 100)
        self.assertEqual(viewport_call[1]['y_pos'], 100)
        self.assertEqual(viewport_call[1]['decorated'], False)  # Borderless
    
    def test_theme_setup(self):
        """Test theme setup."""
        app = EnhancedMeritsApp(self.settings)
        
        # Verify theme was created and bound
        self.mock_dpg.theme.assert_called()
        self.mock_dpg.bind_theme.assert_called()
    
    def test_tab_switching(self):
        """Test tab switching functionality."""
        app = EnhancedMeritsApp(self.settings)
        
        # Test switching to settings tab
        app._switch_tab("settings")
        self.assertEqual(app.current_tab, "settings")
        
        # Test switching to calculator tab
        app._switch_tab("calculator")
        self.assertEqual(app.current_tab, "calculator")
    
    def test_calculation_logic(self):
        """Test calculation logic."""
        app = EnhancedMeritsApp(self.settings)
        
        # Mock input values
        self.mock_dpg.get_value.side_effect = lambda tag: {
            "input_h": "01",
            "input_m": "30",
            "input_s": "45"
        }.get(tag, "")
        
        # Mock settings values
        self.settings.get.side_effect = lambda key, default=None: {
            "rate_merits_auec": 0.618,
            "fee_percent": 0.5
        }.get(key, default)
        
        # Perform calculation
        app._calculate()
        
        # Verify outputs were set
        # 1 hour 30 minutes 45 seconds = 5445 seconds = 5445 merits
        # aUEC value = 5445 * 0.618 = 3364.41
        # fee = 5445 * 0.005 = 27.225
        # total = 5445 + 27.225 = 5472.225
        
        self.mock_dpg.set_value.assert_any_call("out_merits", "5,445")
        self.mock_dpg.set_value.assert_any_call("out_auec", "3,364.41")
    
    def test_report_generation(self):
        """Test report generation."""
        app = EnhancedMeritsApp(self.settings)
        
        # Mock input values
        self.mock_dpg.get_value.side_effect = lambda tag: {
            "input_h": "02",
            "input_m": "15",
            "input_s": "30"
        }.get(tag, "")
        
        # Mock settings values
        self.settings.get.side_effect = lambda key, default=None: {
            "rate_merits_auec": 0.618,
            "fee_percent": 0.5
        }.get(key, default)
        
        # Generate report
        report = app._generate_report_text()
        
        # Verify report contains expected content
        self.assertIn("MeritsCalc Enhanced Report", report)
        self.assertIn("Sentence Length: 02:15:30", report)
        self.assertIn("Conversion Rate: 0.618000", report)
        self.assertIn("Fee Rate: 0.50%", report)
    
    def test_window_controls(self):
        """Test window control functions."""
        app = EnhancedMeritsApp(self.settings)
        
        # Test minimize
        app._minimize_window()
        self.mock_dpg.minimize_viewport.assert_called_once()
        
        # Test maximize
        app._toggle_maximize()
        self.assertTrue(app.maximized)
        
        # Test restore
        app._toggle_maximize()
        self.assertFalse(app.maximized)
    
    def test_transparency_handling(self):
        """Test transparency functionality."""
        app = EnhancedMeritsApp(self.settings)
        
        # Test transparency change
        app._on_transparency_change(None, 0.75)
        self.settings.set.assert_called_with("window_opacity", 0.75)
        self.mock_dpg.set_viewport_opacity.assert_called_with(0.75)
    
    def test_aspect_ratio_handling(self):
        """Test aspect ratio functionality."""
        app = EnhancedMeritsApp(self.settings)
        
        # Test aspect ratio toggle
        app._on_aspect_ratio_toggle(None, True)
        self.settings.set.assert_called_with("aspect_ratio_enforced", True)
    
    def test_keyboard_shortcuts(self):
        """Test keyboard shortcut handling."""
        app = EnhancedMeritsApp(self.settings)
        
        # Mock key states
        self.mock_dpg.is_key_down.side_effect = lambda key: {
            dpg.mvKey_Control: True,
            dpg.mvKey_Shift: False,
            dpg.mvKey_Alt: False
        }.get(key, False)
        
        # Mock shortcut settings
        self.settings.is_shortcut_pressed.return_value = True
        
        # Test save shortcut
        app._on_key_press(None, "S")
        self.settings.is_shortcut_pressed.assert_called_with("save", True, False, False, "S")
    
    def test_edge_snapping(self):
        """Test edge snapping functionality."""
        app = EnhancedMeritsApp(self.settings)
        
        # Mock screen size
        self.mock_ctypes.windll.user32.GetSystemMetrics.return_value = 1920  # Width
        
        # Mock settings
        self.settings.get.return_value = True  # snap_to_edges enabled
        
        # Test snapping to left edge
        x, y = app._apply_edge_snapping(5, 100)
        self.assertEqual(x, 0)
        
        # Test snapping to top edge
        x, y = app._apply_edge_snapping(100, 5)
        self.assertEqual(y, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Setup integration test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = Path(self.temp_dir) / "integration_settings.json"
        
        # Mock settings file path
        self.settings_patcher = patch('src.meritscalc.settings.SETTINGS_FILE', str(self.settings_file))
        self.settings_patcher.start()
    
    def tearDown(self):
        """Cleanup integration test environment."""
        self.settings_patcher.stop()
        
        # Cleanup temporary files
        if self.settings_file.exists():
            self.settings_file.unlink()
        if Path(self.temp_dir).exists():
            Path(self.temp_dir).rmdir()
    
    def test_complete_workflow(self):
        """Test complete application workflow."""
        # Create settings manager
        settings = SettingsManager()
        
        # Verify initial state
        self.assertEqual(settings.get("rate_merits_auec"), 0.618)
        self.assertEqual(settings.get("window_opacity"), 0.9)
        
        # Test settings changes
        settings.set("window_opacity", 0.8)
        settings.set("always_on_top", True)
        
        # Verify settings persistence
        new_settings = SettingsManager()
        self.assertEqual(new_settings.get("window_opacity"), 0.8)
        self.assertTrue(new_settings.get("always_on_top"))
        
        # Test window geometry management
        settings.set_window_geometry(200, 300, 800, 600)
        geometry = settings.get_window_geometry()
        self.assertEqual(geometry["window_x"], 200)
        self.assertEqual(geometry["window_y"], 300)
        self.assertEqual(geometry["window_width"], 800)
        self.assertEqual(geometry["window_height"], 600)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)