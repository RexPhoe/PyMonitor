"""
System Tray Module

This module contains the class for managing the system tray icon and menu.
"""

from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from PyQt6.QtGui import QAction
import qtawesome as qta

class SystemTrayManager:
    """Class responsible for managing the system tray icon and menu"""
    
    def __init__(self, parent=None):
        """
        Initialize the system tray manager.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.tray_icon = QSystemTrayIcon(parent)
        self.setup_tray()
    
    def setup_tray(self):
        """Set up the system tray icon and menu"""
        # Create menu for system tray
        self.tray_menu = QMenu()
        
        # Widget visibility option
        self.toggle_action = QAction("Hide")
        self.tray_menu.addAction(self.toggle_action)
        
        # Settings option with icon
        self.settings_action = QAction(qta.icon("fa5s.cog"), "Settings")
        self.tray_menu.addAction(self.settings_action)
        
        self.tray_menu.addSeparator()
        
        # Console toggle option
        self.console_action = QAction("Show Console")
        self.tray_menu.addAction(self.console_action)
        
        self.tray_menu.addSeparator()
        
        # Exit option
        self.exit_action = QAction("Exit")
        self.tray_menu.addAction(self.exit_action)
        
        # Set the tray icon and its menu
        self.tray_icon.setIcon(qta.icon("fa5s.desktop", color="blue"))
        self.tray_icon.setToolTip("Hardware Monitor")
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def connect_signals(self, toggle_callback, settings_callback, console_callback, exit_callback):
        """
        Connect signal handlers for tray menu actions.
        
        Args:
            toggle_callback: Callback for toggle widget visibility
            settings_callback: Callback for opening settings
            console_callback: Callback for toggling console
            exit_callback: Callback for exiting the application
        """
        self.toggle_action.triggered.connect(toggle_callback)
        self.settings_action.triggered.connect(settings_callback)
        self.console_action.triggered.connect(console_callback)
        self.exit_action.triggered.connect(exit_callback)
        self.tray_icon.activated.connect(self._tray_activated)
    
    def _tray_activated(self, reason):
        """
        Handle tray icon activation.
        
        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_action.triggered.emit()
    
    def show(self):
        """Show the tray icon"""
        self.tray_icon.show()
    
    def update_icon(self, metrics=None):
        """
        Update the tray icon based on system status.
        
        Args:
            metrics: Current system metrics
        """
        if metrics and "cpu" in metrics:
            try:
                cpu_usage = metrics["cpu"].get("usage", 0)
                
                # Choose icon based on CPU load
                if cpu_usage < 30:
                    icon = qta.icon("fa5s.thermometer-empty", color="green")
                elif cpu_usage < 70:
                    icon = qta.icon("fa5s.thermometer-half", color="orange")
                else:
                    icon = qta.icon("fa5s.thermometer-full", color="red")
                    
                self.tray_icon.setIcon(icon)
                self.tray_icon.setToolTip(f"Hardware Monitor - CPU: {cpu_usage:.1f}%")
                
            except Exception as e:
                print(f"Error updating tray icon: {e}")
                # Fallback icon
                self.tray_icon.setIcon(qta.icon("fa5s.desktop", color="blue"))
                self.tray_icon.setToolTip("Hardware Monitor")
        else:
            # No metrics yet, use default icon
            self.tray_icon.setIcon(qta.icon("fa5s.desktop", color="blue"))
            self.tray_icon.setToolTip("Hardware Monitor - Collecting Data...")
    
    def update_toggle_text(self, is_visible):
        """
        Update the toggle action text based on widget visibility.
        
        Args:
            is_visible: Whether the widget is currently visible
        """
        self.toggle_action.setText("Hide Widget" if is_visible else "Show Widget")
    
    def update_console_text(self, is_visible):
        """
        Update the console action text based on console visibility.
        
        Args:
            is_visible: Whether the console is currently visible
        """
        self.console_action.setText("Hide Console" if is_visible else "Show Console")
