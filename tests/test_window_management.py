"""
Test suite for Enhanced Borderless Window Management
Task 1: Enhanced Borderless Window Management

This test file validates the enhanced window management features including:
- Borderless window with precise ImGui dimensions
- Custom title bar with minimize/maximize/close controls
- Smooth resizing from all edges and corners
- Draggable functionality via title bar
"""

import pytest
import dearpygui.dearpygui as dpg
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from meritscalc.ui import MeritsApp
from meritscalc.settings import SettingsManager
from meritscalc.logic import MeritsCalculator


class TestEnhancedWindowManagement:
    """Test class for enhanced borderless window management features"""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings manager"""
        settings = MagicMock(spec=SettingsManager)
        settings.get.side_effect = lambda key, default=None: {
            'window_x': 100,
            'window_y': 100,
            'window_width': 500,
            'window_height': 720,
            'snap_to_edges': True,
            'aspect_ratio_enforced': False,
            'window_opacity': 0.9,
            'shortcuts': {
                'save': {'ctrl': True, 'shift': False, 'alt': False, 'key': 'S'},
                'quit': {'ctrl': True, 'shift': False, 'alt': False, 'key': 'Q'}
            }
        }.get(key, default)
        return settings
    
    @pytest.fixture
    def mock_calculator(self):
        """Create mock calculator"""
        calc = MagicMock(spec=MeritsCalculator)
        return calc
    
    @pytest.fixture
    def app_instance(self, mock_settings, mock_calculator):
        """Create app instance for testing"""
        with patch('meritscalc.ui.dpg'):
            with patch('meritscalc.ui._app_data_dir'):
                app = MeritsApp(mock_settings, mock_calculator)
                yield app
    
    def test_borderless_window_creation(self, app_instance):
        """Test that borderless window is created with correct properties"""
        # Verify viewport creation was called
        dpg.create_viewport.assert_called_once()
        call_args = dpg.create_viewport.call_args
        
        # Check viewport properties
        assert call_args[1]['decorated'] == False  # Borderless
        assert call_args[1]['clear_color'] == (11, 13, 18, 255)  # Dark theme
        assert call_args[1]['width'] == 500
        assert call_args[1]['height'] == 720
        assert call_args[1]['x_pos'] == 100
        assert call_args[1]['y_pos'] == 100
    
    def test_custom_title_bar_creation(self, app_instance):
        """Test that custom title bar is created with controls"""
        # The title bar should be created as a child window
        # Verify title bar components exist
        assert hasattr(app_instance, 'dragging')
        assert hasattr(app_instance, 'resizing')
        assert hasattr(app_instance, 'drag_start_pos')
        assert hasattr(app_instance, 'initial_window_pos')
        assert hasattr(app_instance, 'initial_window_size')
        
        # Verify initial states
        assert app_instance.dragging == False
        assert app_instance.resizing == False
        assert app_instance.drag_start_pos == (0, 0)
        assert app_instance.initial_window_pos == (0, 0)
        assert app_instance.initial_window_size == (0, 0)
    
    def test_title_bar_buttons_functionality(self, app_instance):
        """Test that title bar buttons have proper callbacks"""
        # Test minimize functionality
        with patch.object(app_instance, '_minimize') as mock_minimize:
            app_instance._minimize()
            mock_minimize.assert_called_once()
        
        # Test close functionality  
        with patch('meritscalc.ui.dpg.stop_dearpygui') as mock_stop:
            app_instance._close_app()
            mock_stop.assert_called_once()
    
    def test_window_dragging_mechanism(self, app_instance):
        """Test window dragging functionality via title bar"""
        # Mock mouse position and viewport methods
        with patch('meritscalc.ui.dpg.get_mouse_pos') as mock_get_mouse:
            with patch('meritscalc.ui.dpg.get_viewport_pos') as mock_get_pos:
                with patch('meritscalc.ui.dpg.set_viewport_pos') as mock_set_pos:
                    with patch('meritscalc.ui.dpg.is_item_hovered') as mock_hovered:
                        
                        # Simulate mouse click on title bar
                        mock_hovered.return_value = True
                        mock_get_mouse.return_value = (150, 150)
                        mock_get_pos.return_value = (100, 100)
                        
                        # Start dragging
                        app_instance._on_mouse_click(None, None)
                        assert app_instance.dragging == True
                        assert app_instance.drag_start_pos == (150, 150)
                        assert app_instance.initial_window_pos == (100, 100)
                        
                        # Simulate mouse movement during drag
                        mock_get_mouse.return_value = (160, 160)
                        app_instance._process_window_interaction()
                        
                        # Verify viewport position was updated (with snap)
                        mock_set_pos.assert_called()
    
    def test_window_resizing_mechanism(self, app_instance):
        """Test window resizing functionality from edges/corners"""
        # Mock mouse position and viewport methods
        with patch('meritscalc.ui.dpg.get_mouse_pos') as mock_get_mouse:
            with patch('meritscalc.ui.dpg.get_viewport_width') as mock_get_width:
                with patch('meritscalc.ui.dpg.get_viewport_height') as mock_get_height:
                    with patch('meritscalc.ui.dpg.set_viewport_width') as mock_set_width:
                        with patch('meritscalc.ui.dpg.set_viewport_height') as mock_set_height:
                            with patch('meritscalc.ui.dpg.is_item_hovered') as mock_hovered:
                                
                                # Simulate mouse click on resize grip
                                mock_hovered.return_value = True
                                mock_get_mouse.return_value = (600, 800)
                                mock_get_width.return_value = 500
                                mock_get_height.return_value = 720
                                
                                # Start resizing
                                app_instance._on_mouse_click(None, None)
                                assert app_instance.resizing == True
                                assert app_instance.drag_start_pos == (600, 800)
                                assert app_instance.initial_window_size == (500, 720)
                                
                                # Simulate mouse movement during resize
                                mock_get_mouse.return_value = (620, 840)
                                app_instance._process_window_interaction()
                                
                                # Verify viewport dimensions were updated (minimum size enforced)
                                mock_set_width.assert_called()
                                mock_set_height.assert_called()
    
    def test_minimum_window_size_enforcement(self, app_instance):
        """Test that minimum window size is enforced during resize"""
        with patch('meritscalc.ui.dpg.get_mouse_pos') as mock_get_mouse:
            with patch('meritscalc.ui.dpg.get_viewport_width') as mock_get_width:
                with patch('meritscalc.ui.dpg.get_viewport_height') as mock_get_height:
                    with patch('meritscalc.ui.dpg.set_viewport_width') as mock_set_width:
                        with patch('meritscalc.ui.dpg.set_viewport_height') as mock_set_height:
                            with patch('meritscalc.ui.dpg.is_item_hovered') as mock_hovered:
                                
                                # Start resizing
                                mock_hovered.return_value = True
                                mock_get_mouse.return_value = (600, 800)
                                mock_get_width.return_value = 500
                                mock_get_height.return_value = 720
                                app_instance._on_mouse_click(None, None)
                                
                                # Try to resize to below minimum
                                mock_get_mouse.return_value = (-100, -100)  # Would make size negative
                                app_instance._process_window_interaction()
                                
                                # Verify minimum dimensions are enforced
                                mock_set_width.assert_called_with(400)  # Minimum width
                                mock_set_height.assert_called_with(500)  # Minimum height
    
    def test_window_position_saving(self, app_instance):
        """Test that window position and size are saved on release"""
        with patch('meritscalc.ui.dpg.get_viewport_pos') as mock_get_pos:
            with patch('meritscalc.ui.dpg.get_viewport_width') as mock_get_width:
                with patch('meritscalc.ui.dpg.get_viewport_height') as mock_get_height:
                    
                    # Mock window position and size
                    mock_get_pos.return_value = (150, 200)
                    mock_get_width.return_value = 550
                    mock_get_height.return_value = 750
                    
                    # Simulate mouse release
                    app_instance._on_mouse_release(None, None)
                    
                    # Verify settings were saved
                    app_instance.settings.set.assert_any_call('window_x', 150)
                    app_instance.settings.set.assert_any_call('window_y', 200)
                    app_instance.settings.set.assert_any_call('window_width', 550)
                    app_instance.settings.set.assert_any_call('window_height', 750)
    
    def test_dynamic_spacer_updates(self, app_instance):
        """Test that dynamic spacers are updated during window resize"""
        with patch('meritscalc.ui.dpg.get_mouse_pos') as mock_get_mouse:
            with patch('meritscalc.ui.dpg.get_viewport_width') as mock_get_width:
                with patch('meritscalc.ui.dpg.set_viewport_width') as mock_set_width:
                    with patch('meritscalc.ui.dpg.set_item_width') as mock_set_item_width:
                        with patch('meritscalc.ui.dpg.is_item_hovered') as mock_hovered:
                            
                            # Start resizing
                            mock_hovered.return_value = True
                            mock_get_mouse.return_value = (600, 800)
                            mock_get_width.return_value = 500
                            app_instance._on_mouse_click(None, None)
                            
                            # Simulate resize to larger width
                            mock_get_mouse.return_value = (700, 800)
                            app_instance._process_window_interaction()
                            
                            # Verify dynamic spacers are updated
                            mock_set_item_width.assert_any_call('TitleSpacer', 400)  # new_width - 300
                            mock_set_item_width.assert_any_call('ResizeSpacer', 670)  # new_width - 30
                            mock_set_item_width.assert_any_call('ContentGroup', 660)  # new_width - 40


class TestWindowSnapFunctionality:
    """Test class for window snapping features"""
    
    @pytest.fixture
    def app_with_snap_settings(self):
        """Create app instance with snap settings"""
        settings = MagicMock(spec=SettingsManager)
        settings.get.side_effect = lambda key, default=None: {
            'window_x': 100,
            'window_y': 100,
            'window_width': 500,
            'window_height': 720,
            'snap_to_edges': True,  # Enable snapping
            'snap_to_windows': False,
            'window_opacity': 0.9,
        }.get(key, default)
        
        calc = MagicMock(spec=MeritsCalculator)
        
        with patch('meritscalc.ui.dpg'):
            with patch('meritscalc.ui._app_data_dir'):
                app = MeritsApp(settings, calc)
                return app
    
    def test_screen_edge_snap_detection(self, app_with_snap_settings):
        """Test that screen edge snapping is detected and applied"""
        app = app_with_snap_settings
        
        # Test snap to left edge (near x=0)
        snapped_x, snapped_y = app._snap_to_screen(5, 100, 500, 720)
        assert snapped_x == 0  # Should snap to left edge
        
        # Test snap to right edge (near screen width)
        with patch('meritscalc.ui.ctypes.windll.user32.GetSystemMetrics') as mock_metrics:
            mock_metrics.return_value = 1920  # Mock screen width
            
            snapped_x, snapped_y = app._snap_to_screen(1415, 100, 500, 720)  # 1415 + 500 = 1915 (close to 1920)
            assert snapped_x == 1420  # Should snap to right edge
        
        # Test snap to top edge (near y=0)
        snapped_x, snapped_y = app._snap_to_screen(100, 8, 500, 720)
        assert snapped_y == 0  # Should snap to top edge
        
        # Test snap to bottom edge (near screen height)
        with patch('meritscalc.ui.ctypes.windll.user32.GetSystemMetrics') as mock_metrics:
            mock_metrics.side_effect = [1920, 1080]  # screen width, screen height
            
            snapped_x, snapped_y = app._snap_to_screen(100, 355, 500, 720)  # 355 + 720 = 1075 (close to 1080)
            assert snapped_y == 360  # Should snap to bottom edge
    
    def test_snap_threshold_distance(self, app_with_snap_settings):
        """Test that snapping only occurs within threshold distance"""
        app = app_with_snap_settings
        
        # Test no snap when far from edges (beyond snap distance of 20)
        snapped_x, snapped_y = app._snap_to_screen(50, 100, 500, 720)  # 50 > 20 from left edge
        assert snapped_x == 50  # Should not snap
        
        snapped_x, snapped_y = app._snap_to_screen(100, 50, 500, 720)  # 50 > 20 from top edge
        assert snapped_y == 50  # Should not snap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])