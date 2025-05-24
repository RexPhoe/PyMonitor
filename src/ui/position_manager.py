"""
Position Manager Module

This module handles the positioning of the widget on the screen.
"""

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtWidgets import QApplication

class PositionManager:
    """Class responsible for managing widget position on screen"""
    
    def __init__(self, config):
        """
        Initialize the position manager.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
    
    def calculate_position(self, widget_size):
        """
        Calculate the widget position based on configuration.
        
        Args:
            widget_size: Current size of the widget
            
        Returns:
            QPoint: The calculated position
        """
        position = self.config["appearance"]["position"]
        
        # Get selected monitor
        monitor_index = self.config["appearance"].get("monitor_index", 0)
        screens = QApplication.screens()
        
        # Validate monitor index
        if monitor_index < 0 or monitor_index >= len(screens):
            # Fallback to primary monitor
            monitor_index = 0
        
        # Get the geometry of the selected monitor
        screen = screens[monitor_index]
        screen_geo = screen.geometry()
        
        # Get offset values
        offset_x = self.config["appearance"].get("offset_x", 0)
        offset_y = self.config["appearance"].get("offset_y", 0)
        
        x, y = screen_geo.x(), screen_geo.y()  # Start with monitor's top-left position
        
        if position == "top-left":
            # No adjustment needed for top-left
            pass
        elif position == "top-right":
            x = screen_geo.x() + screen_geo.width() - widget_size.width()
        elif position == "bottom-left":
            # For bottom positions, add extra bottom padding to prevent text clipping
            y = screen_geo.y() + screen_geo.height() - widget_size.height() - 10
        elif position == "bottom-right":
            x = screen_geo.x() + screen_geo.width() - widget_size.width()
            # For bottom positions, add extra bottom padding to prevent text clipping
            y = screen_geo.y() + screen_geo.height() - widget_size.height() - 10
        elif position == "center":
            x = screen_geo.x() + (screen_geo.width() - widget_size.width()) // 2
            y = screen_geo.y() + (screen_geo.height() - widget_size.height()) // 2
        elif position == "custom":
            custom_pos = self.config["appearance"]["custom_position"]
            x = screen_geo.x() + custom_pos[0]
            y = screen_geo.y() + custom_pos[1]
        
        # Apply offsets
        x += offset_x
        y += offset_y
        
        # Ensure widget stays on selected screen
        screen_right = screen_geo.x() + screen_geo.width()
        screen_bottom = screen_geo.y() + screen_geo.height()
        
        if x < screen_geo.x():
            x = screen_geo.x()
        elif x > screen_right - widget_size.width():
            x = screen_right - widget_size.width()
            
        if y < screen_geo.y():
            y = screen_geo.y()
        elif y > screen_bottom - widget_size.height():
            y = screen_bottom - widget_size.height()
        
        return QPoint(x, y)
    
    def update_custom_position(self, position):
        """
        Update the custom position in the configuration.
        
        Args:
            position: Current widget position (QPoint)
        """
        self.config["appearance"]["position"] = "custom"
        self.config["appearance"]["custom_position"] = [position.x(), position.y()]
    
    def get_screen_geometry(self):
        """
        Get the geometry of the currently selected monitor.
        
        Returns:
            QRect: The geometry of the selected monitor
        """
        monitor_index = self.config["appearance"].get("monitor_index", 0)
        screens = QApplication.screens()
        
        # Validate monitor index
        if monitor_index < 0 or monitor_index >= len(screens):
            monitor_index = 0
        
        screen = screens[monitor_index]
        return screen.geometry()
