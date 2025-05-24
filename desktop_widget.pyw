#!/usr/bin/env python
"""
Hardware Monitor Desktop Widget

This application displays hardware metrics as a semi-transparent overlay on the desktop
and provides a system tray icon for configuration and control.
"""

import sys
from PyQt6.QtWidgets import QApplication

from src.core.config_manager import ConfigManager
from src.core.metrics_worker import MetricsWorker
from src.ui.main_window import MainWindow
from src.utils.console_handler import ConsoleHandler
from monitor.utils.hardware_monitor import HardwareMonitor
from settings_dialog import SettingsDialog


def main():
    """Main entry point for the application"""
    # Create QApplication first
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed
    
    # Hide console window by default on Windows
    if ConsoleHandler.is_windows():
        ConsoleHandler.hide_console()
    
    # Initialize components
    config_manager = ConfigManager()
    hardware_monitor = HardwareMonitor()
    metrics_worker = MetricsWorker(hardware_monitor)
    
    # Create main window
    window = MainWindow(
        config_manager=config_manager,
        metrics_worker=metrics_worker,
        console_handler=ConsoleHandler,
        settings_dialog_class=SettingsDialog
    )
    
    # Show the window
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
