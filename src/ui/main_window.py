"""
Main Window Module

This module contains the main window class that coordinates all UI components.
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

from src.ui.metrics_display import MetricsDisplay
from src.ui.system_tray import SystemTrayManager
from src.ui.position_manager import PositionManager

class MainWindow(QMainWindow):
    """Main window class for the hardware monitor widget"""
    
    def __init__(self, config_manager, metrics_worker, console_handler, settings_dialog_class):
        """
        Initialize the main window.
        
        Args:
            config_manager: Configuration manager instance
            metrics_worker: Metrics worker instance
            console_handler: Console handler for toggling console visibility
            settings_dialog_class: Class to use for the settings dialog
        """
        super().__init__()
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.metrics_worker = metrics_worker
        self.console_handler = console_handler
        self.settings_dialog_class = settings_dialog_class
        
        # Last collected metrics
        self.last_metrics = None
        
        # Set up UI components
        self.setup_ui()
        
        # Initialize system tray
        self.system_tray = SystemTrayManager(self)
        self.system_tray.connect_signals(
            self.toggle_visibility,
            self.open_settings,
            self.toggle_console,
            self.exit_app
        )
        self.system_tray.show()
        
        # Position manager
        self.position_manager = PositionManager(self.config)
        
        # Connect signals
        self.metrics_worker.metrics_ready.connect(self.on_metrics_ready)
        self.metrics_worker.error_occurred.connect(self.on_metrics_error)
        
        # For dragging
        self.draggable = True
        self.drag_position = None
        
        # Start metrics worker
        self.start_metrics_worker()
        
        # Apply initial position
        self.apply_position()
    
    def setup_ui(self):
        """Set up the main UI components"""
        # Apply window flags based on configuration
        self.update_window_flags()
        
        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        

        
        # Use fixed size policy to match the original behavior
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Set minimum and maximum sizes based on config
        max_width = self.config["appearance"]["max_width"]
        max_height = self.config["appearance"]["max_height"]
        self.setMinimumSize(max_width, 100)  # Ensure minimum width matches config
        self.setMaximumSize(16777215, 16777215)  # Very large maximum size (QWIDGETSIZE_MAX)
        
        # Apply style only to the main widget
        self.setObjectName("hardwareMonitorWidget")
        self.setStyleSheet("""
            #hardwareMonitorWidget {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Don't override resize-related methods to ensure proper sizing
        # but allow the widget to size itself based on content
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout for central widget with minimal margins to match original behavior
        self.main_layout = QVBoxLayout(self.central_widget)
        padding = self.config["appearance"]["padding"]
        self.main_layout.setContentsMargins(padding, padding, padding, padding)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create metrics display
        self.metrics_display = MetricsDisplay(self.config)
        self.main_layout.addWidget(self.metrics_display)
        
        # Set opacity
        self.setWindowOpacity(self.config["appearance"]["opacity"])
    
    def on_metrics_ready(self, metrics):
        """
        Handle metrics from worker thread.
        
        Args:
            metrics: Dictionary of metrics from the worker
        """
        # Store last metrics
        self.last_metrics = metrics
        
        # Update metrics display using formatter
        from src.ui.metrics_formatter import MetricsFormatter
        
        formatted_metrics = {}
        
        if "cpu" in metrics:
            formatted_metrics["cpu"] = MetricsFormatter.format_cpu_metrics(metrics["cpu"])
        
        if "gpu" in metrics:
            formatted_metrics["gpu"] = MetricsFormatter.format_gpu_metrics(metrics["gpu"])
        
        if "ram" in metrics:
            formatted_metrics["ram"] = MetricsFormatter.format_ram_metrics(metrics["ram"])
        
        if "network" in metrics:
            formatted_metrics["network"] = MetricsFormatter.format_network_metrics(metrics["network"])
        
        # Update metrics display
        self.metrics_display.update_metrics(formatted_metrics)
        
        # Update tray icon
        self.system_tray.update_icon(metrics)
    
    def on_metrics_error(self, error_message):
        """
        Handle errors from worker thread.
        
        Args:
            error_message: Error message from the worker
        """
        print(f"Error collecting metrics: {error_message}")
    
    def start_metrics_worker(self, restart=False):
        """
        Start the metrics worker thread.
        
        Args:
            restart: Whether to restart an existing worker
        """
        # Ensure the interval is correct (between 0.1 and 5 seconds)
        interval = float(self.config["appearance"]["refresh_rate"])
        interval = max(0.1, min(interval, 5.0))
            
        # Stop the worker if it's already running and we're restarting
        if restart and self.metrics_worker.running:
            self.metrics_worker.stop()
            
        # Start worker thread with the correct interval
        self.metrics_worker.start(interval=interval)
    
    def apply_position(self):
        """Apply the configured position to the widget"""
        # Make sure the content is properly sized
        self.metrics_display.updateGeometry()
        
        # First, let Qt determine the proper size based on content
        self.adjustSize()
        
        # Make sure the widget is wide enough to display all content
        max_width = self.config["appearance"]["max_width"]
        current_width = max(self.width(), max_width)
        
        # Use content height, but ensure it fits within max_height
        max_height = self.config["appearance"]["max_height"]
        calculated_height = self.metrics_display.sizeHint().height() + 20
        current_height = min(max_height, calculated_height)
        
        # Resize the widget
        self.resize(current_width, current_height)
        
        # Calculate position
        position = self.position_manager.calculate_position(self.geometry().size())
        
        # Move widget to calculated position
        self.move(position)
    
    def update_window_flags(self):
        """Update window flags based on the keep_on_top setting"""
        import platform
        
        # Determine if we should keep the window on top
        keep_on_top = self.config["appearance"].get("keep_on_top", True)
        
        # Start with frameless window
        flags = Qt.WindowType.FramelessWindowHint
        
        # Add stay-on-top flag if enabled
        if keep_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        
        # Platform-specific flags
        if platform.system() == "Darwin":  # macOS
            # macOS-specific flags - simpler set to avoid compatibility issues
            flags |= Qt.WindowType.Tool
        else:  # Windows and Linux
            # Additional flags for Windows and Linux
            flags |= (
                Qt.WindowType.Tool |
                Qt.WindowType.NoDropShadowWindowHint |
                Qt.WindowType.MSWindowsFixedSizeDialogHint |
                Qt.WindowType.BypassWindowManagerHint
            )
        
        # Apply the flags
        self.setWindowFlags(flags)
    
    def update_config(self, new_config):
        """
        Update the configuration and apply changes.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config = new_config
        self.config_manager.update_config(new_config)
        
        # Update opacity
        self.setWindowOpacity(self.config["appearance"]["opacity"])
        
        # Update window flags (for keep_on_top setting)
        self.update_window_flags()
        
        # Update position manager
        self.position_manager = PositionManager(self.config)
        
        # Update metrics display
        self.metrics_display.config = self.config
        self.metrics_display.setup_metric_sections()
        self.metrics_display.update_style()
        
        # Apply new position
        self.apply_position()
        
        # Restart metrics worker with new refresh rate
        self.start_metrics_worker(restart=True)
    
    def toggle_visibility(self):
        """Toggle widget visibility"""
        if self.isVisible():
            self.hide()
            self.system_tray.update_toggle_text(False)
        else:
            self.show()
            self.apply_position()
            self.system_tray.update_toggle_text(True)
    
    def open_settings(self):
        """Open the settings dialog"""
        dialog = self.settings_dialog_class(self.config, self)
        if dialog.exec():
            # If dialog was accepted, update and save config
            new_config = dialog.get_config()
            self.update_config(new_config)
    
    def toggle_console(self):
        """Toggle console window visibility"""
        is_visible = self.console_handler.toggle_console()
        self.system_tray.update_console_text(is_visible)
    
    def exit_app(self):
        """Exit the application"""
        # Stop the metrics worker thread
        self.metrics_worker.stop()
        
        # Save configuration before exit
        self.config_manager.save_config()
        
        # Show console before exit
        if hasattr(self.console_handler, 'is_windows') and self.console_handler.is_windows():
            self.console_handler.show_console()
        
        # Quit the application
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
    
    # Event handlers for dragging
    def mousePressEvent(self, event):
        """Handle mouse press events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton and self.draggable:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
            # Record that this is now a custom position
            self.config["appearance"]["position"] = "custom"
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging"""
        if self.drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton and self.draggable:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            
            # Update custom position in config
            self.position_manager.update_custom_position(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton and self.draggable:
            self.drag_position = None
            # Save the final position
            self.config_manager.save_config()
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_settings()
            event.accept()
    
    def sizeHint(self):
        """
        Get the suggested size for the window.
        
        Returns:
            QSize: The suggested size
        """
        # Use the configured max width and let height adjust to content
        max_width = self.config["appearance"]["max_width"]
        
        if hasattr(self, 'metrics_display'):
            # Get the display's size hint
            hint = self.metrics_display.sizeHint()
            return QSize(max_width, hint.height())
            
        # Default size if metrics display is not available
        return QSize(max_width, 300)
