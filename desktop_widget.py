#!/usr/bin/env python
"""
Hardware Monitor Desktop Widget

This application displays hardware metrics as a semi-transparent overlay on the desktop
and provides a system tray icon for configuration and control.
"""

import sys
import os
import json
import threading
import time
from queue import Queue
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QMainWindow, QMenu, QSystemTrayIcon,
                            QDialog, QTabWidget, QPushButton, QColorDialog,
                            QFontDialog, QSlider, QComboBox, QCheckBox, QSpinBox,
                            QGroupBox, QFormLayout, QFrame, QProgressBar, QScrollArea,
                            QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QSettings, QObject
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPalette, QFontMetrics
import qtawesome as qta

from monitor.utils.hardware_monitor import HardwareMonitor
from settings_dialog import SettingsDialog


class MetricsWorker(QObject):
    """Worker class for collecting hardware metrics in a background thread"""
    # Signal to emit when metrics are collected
    metrics_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, hardware_monitor):
        super().__init__()
        self.hardware_monitor = hardware_monitor
        self.running = False
        self.thread = None
        self.interval = 1.0  # Default update interval in seconds
    
    def start(self, interval=1.0):
        """Start the worker thread"""
        self.interval = interval
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
    
    def _run(self):
        """Main worker loop - runs in a separate thread"""
        while self.running:
            try:
                # Collect metrics
                metrics = self.hardware_monitor.get_all_metrics()
                # Emit signal with metrics
                self.metrics_ready.emit(metrics)
            except Exception as e:
                # Emit error signal
                self.error_occurred.emit(str(e))
            
            # Sleep for the specified interval
            time.sleep(self.interval)

# Default configuration
DEFAULT_CONFIG = {
    "appearance": {
        "font_family": "Consolas",
        "font_size": 10,
        "font_color": "#FFFFFF",
        "background_color": "#000000",
        "opacity": 0.7,
        "refresh_rate": 1.0,  # seconds
        "position": "bottom-right",
        "padding": 10,
        "custom_position": [100, 100],  # [x, y]
        "max_width": 400,  # Maximum width for the widget
        "max_height": 800,  # Maximum height for the widget
        "monitor_index": 0,  # Default to primary monitor
        "offset_x": 0,  # Fine-tune X position
        "offset_y": 0   # Fine-tune Y position
    },
    "layout": {
        "type": "vertical",  # "vertical", "horizontal", or "grid"
        "columns": 2,  # Number of columns when using grid layout
        "spacing": 5,  # Spacing between items
        "use_scroll": True,  # Use scrollbar if content exceeds size
        # Component order (lower values appear first)
        "component_order": {
            "cpu": 1,
            "gpu": 2,
            "ram": 3,
            "network": 4
        },
        # Metric order within each component (lower values appear first)
        "metric_order": {
            "cpu_usage": 1,
            "cpu_temperature": 2,
            "cpu_frequency": 3,
            "cpu_voltage": 4,
            "gpu_core_usage": 1,
            "gpu_core_temperature": 2,
            "gpu_core_frequency": 3,
            "gpu_memory_frequency": 4,
            "gpu_memory_temperature": 5,
            "gpu_hotspot_temperature": 6,
            "gpu_vram_usage": 7,
            "gpu_vram_memory": 8,
            "gpu_fan_speed": 9,
            "ram_percent": 1,
            "ram_used_total": 2,
            "ram_available": 3,
            "ram_temperature": 4,
            "network_upload_speed": 1,
            "network_download_speed": 2,
            "network_total_sent": 3,
            "network_total_received": 4
        }
    },
    "display": {
        # Category visibility
        "show_cpu": True,
        "show_gpu": True,
        "show_ram": True,
        "show_network": True,
        "show_titles": True,
        "compact_mode": False,
        
        # CPU metrics - from CPUMetricsCollector.get_metrics()
        "show_cpu_usage": True,      # cpu.usage
        "show_cpu_temperature": True, # cpu.temperature
        "show_cpu_frequency": True,   # cpu.frequency
        "show_cpu_voltage": True,     # cpu.voltage
        
        # GPU metrics - from GPUMetricsCollector.get_metrics()
        "show_gpu_core_usage": True,           # gpu.core_usage
        "show_gpu_core_temperature": True,     # gpu.core_temperature
        "show_gpu_core_frequency": True,       # gpu.core_frequency
        "show_gpu_memory_frequency": True,     # gpu.memory_frequency
        "show_gpu_memory_temperature": True,   # gpu.memory_temperature
        "show_gpu_hotspot_temperature": True,  # gpu.hotspot_temperature
        "show_gpu_vram_usage": True,           # gpu.vram_usage_percent
        "show_gpu_vram_memory": True,          # gpu.vram_used_gb and gpu.vram_total_gb
        "show_gpu_fan_speed": True,            # gpu.fan_speed
        
        # RAM metrics - from RAMMetricsCollector.get_metrics()
        "show_ram_percent": True,       # ram.percent
        "show_ram_used_total": True,     # ram.used and ram.total
        "show_ram_available": True,      # ram.available
        "show_ram_temperature": True,    # ram.ram_temperature
        
        # Network metrics - from NetworkMetricsCollector.get_metrics()
        "show_network_upload_speed": True,      # network.upload_speed
        "show_network_download_speed": True,    # network.download_speed
        "show_network_total_sent": True,        # network.total_sent
        "show_network_total_received": True     # network.total_received
    }
}

class HardwareWidget(QMainWindow):
    """Main desktop widget showing hardware metrics"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize hardware monitor
        self.hardware_monitor = HardwareMonitor()
        
        # Load settings
        self.config = self.load_config()
        
        # Setup metrics worker
        self.metrics_worker = MetricsWorker(self.hardware_monitor)
        self.metrics_worker.metrics_ready.connect(self.on_metrics_ready)
        self.metrics_worker.error_occurred.connect(self.on_metrics_error)
        
        # Last collected metrics
        self.last_metrics = None
        
        # Setup UI components
        self.setup_ui()
        
        # Initialize system tray
        self.setup_system_tray()
        
        # Eliminar completamente la barra de estado que puede mostrar controles de redimensionamiento
        self.setStatusBar(None)
        
        # Start metrics worker
        self.start_metrics_worker()
        
        # Apply initial position
        self.apply_position()
    
    def load_config(self):
        """Load configuration from file or use defaults"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Ensure all default keys exist (for compatibility with older configs)
                for section in DEFAULT_CONFIG:
                    if section not in config:
                        config[section] = DEFAULT_CONFIG[section]
                    else:
                        for key in DEFAULT_CONFIG[section]:
                            if key not in config[section]:
                                config[section][key] = DEFAULT_CONFIG[section][key]
                return config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return DEFAULT_CONFIG.copy()
        else:
            # Save default config
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        """Set up the main UI components"""
        # Completely remove any window decoration
        # The BypassWindowManagerHint and X11BypassWindowManagerHint flags are critical
        # to remove any window controls
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint |
            Qt.WindowType.MSWindowsFixedSizeDialogHint |
            Qt.WindowType.BypassWindowManagerHint
        )
        # Make background completely transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        # Fixed size policy to prevent resizing
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(1, 1)  # Very small minimum size
        self.setMaximumSize(16777215, 16777215)  # Very large maximum size (QWIDGETSIZE_MAX)
        
        # Apply style ONLY to the main widget, without affecting other dialogs
        # We use objectName to limit the scope of the style
        self.setObjectName("hardwareMonitorWidget")
        self.setStyleSheet("""
            #hardwareMonitorWidget {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Override resize-related methods
        self.resizeEvent = lambda event: None
        self.sizeHint = lambda: QSize(10, 10)  # Small suggested size
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Apply background color and opacity
        self.update_style()
        
        # Create layout for metrics
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(
            self.config["appearance"]["padding"],
            self.config["appearance"]["padding"],
            self.config["appearance"]["padding"],
            self.config["appearance"]["padding"]
        )
        
        # Create sections for each hardware component
        self.setup_metric_sections()
        
        # Make widget draggable
        self.draggable = True
        self.drag_position = None
    
    def setup_metric_sections(self):
        """Create sections for each hardware component using flexible layout"""
        # Clear existing widgets if any
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # También limpiar sublayouts
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget():
                        subitem.widget().deleteLater()
        
        # Create main container que se adaptará automáticamente al tamaño del contenido
        main_container = QWidget()
        
        # Create layout based on configuration
        if self.config["layout"]["type"] == "horizontal":
            content_layout = QHBoxLayout(main_container)
        elif self.config["layout"]["type"] == "grid":
            content_layout = QGridLayout(main_container)
        else:  # Default to vertical
            content_layout = QVBoxLayout(main_container)
        
        # Set spacing and margins
        content_layout.setSpacing(self.config["layout"]["spacing"])
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Añadir container directamente al layout principal
        # No usamos scroll area por petición del usuario
        self.main_layout.addWidget(main_container)
        
        # Asegurar que el container no tenga borde ni controles de redimensionamiento
        main_container.setStyleSheet("border: none; background-color: transparent;")
        main_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Font and color setup
        font = QFont(
            self.config["appearance"]["font_family"],
            self.config["appearance"]["font_size"]
        )
        color = QColor(self.config["appearance"]["font_color"])
        
        # Prepare components in order of preference
        components = []
        component_keys = ["cpu", "gpu", "ram", "network"]
        
        # Add components that are enabled
        for key in component_keys:
            if self.config["display"][f"show_{key}"]:
                # Use component order from config, with fallback values
                order = self.config["layout"].get("component_order", {}).get(key, component_keys.index(key))
                components.append((key, order))
        
        # Sort components by their configured order
        components.sort(key=lambda x: x[1])
        
        # Dictionaries to store all label references
        self.component_titles = {}
        self.component_labels = {key: [] for key in component_keys}
        
        # Grid layout positioning helpers
        grid_row, grid_col = 0, 0
        num_columns = self.config["layout"].get("columns", 2)
        
        # Create sections for each component
        for component_name, _ in components:
            # Create container for this component
            component_container = QWidget()
            component_layout = QVBoxLayout(component_container)
            component_layout.setContentsMargins(5, 5, 5, 5)
            component_layout.setSpacing(2)
            
            # Add title if enabled
            if self.config["display"]["show_titles"]:
                title_text = component_name.upper()
                title_label = QLabel(title_text)
                title_label.setFont(font)
                title_label.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
                component_layout.addWidget(title_label)
                self.component_titles[component_name] = title_label
            
            # Create placeholder for the metrics
            # We'll determine the actual number of metrics when we update them
            max_placeholders = 10  # Maximum number of metrics per component
            labels = []
            for i in range(max_placeholders):
                label = QLabel("")
                label.setFont(font)
                label.setStyleSheet(f"color: {color.name()};")
                label.setVisible(False)  # Hidden by default until populated
                component_layout.addWidget(label)
                labels.append(label)
            
            # Store labels in the appropriate dictionary
            self.component_labels[component_name] = labels
            
            # Add the component container to the layout based on type
            if self.config["layout"]["type"] == "grid":
                content_layout.addWidget(component_container, grid_row, grid_col)
                grid_col += 1
                if grid_col >= num_columns:
                    grid_col = 0
                    grid_row += 1
            else:
                content_layout.addWidget(component_container)
            
        # Add a stretch at the end if not using grid layout
        if self.config["layout"]["type"] != "grid":
            content_layout.addStretch()
    
    def on_metrics_ready(self, metrics):
        """Handle metrics from worker thread"""
        # Store last metrics
        self.last_metrics = metrics
        
        # We no longer use the loading indicator (status_indicator)
        # as it has been completely removed
        
        # Update metrics display
        self._update_metrics_display(metrics)
        
        # Update tray icon based on new metrics
        self.update_tray_icon()
    
    def on_metrics_error(self, error_message):
        """Handle errors from worker thread"""
        print(f"Error collecting metrics: {error_message}")
        # We no longer show a visual error indicator
        # Only log the error to the console
    
    def start_metrics_worker(self):
        """Start the metrics worker thread"""
        # Ensure the interval is correct (between 0.1 and 5 seconds)
        interval = self.config["appearance"]["refresh_rate"]
        if interval < 0.1:
            interval = 0.1
        elif interval > 5.0:
            interval = 5.0
            
        print(f"Starting metrics collector with interval: {interval} seconds")
        
        # Stop the worker if it's already running to restart it with the new interval
        if hasattr(self, 'metrics_worker') and self.metrics_worker.running:
            self.metrics_worker.stop()
            
        # Start worker thread with the correct interval
        self.metrics_worker.start(interval=interval)
    
    def stop_metrics_worker(self):
        """Stop the metrics worker thread"""
        self.metrics_worker.stop()
    
    def _update_metrics_display(self, metrics):
        """Update displayed metrics using the new flexible layout"""
        try:
            # Ensure metrics are valid
            if not metrics:
                print("No metrics data received")
                return
                
            # Debug info
            print(f"CPU metrics keys: {metrics.get('cpu', {}).keys()}")
            print(f"GPU metrics keys: {metrics.get('gpu', {}).keys()}")
            print(f"RAM metrics keys: {metrics.get('ram', {}).keys()}")
            print(f"Network metrics keys: {metrics.get('network', {}).keys()}")
            
            # Update each component section based on available metrics and settings
            self._update_component_metrics("cpu", metrics)
            self._update_component_metrics("gpu", metrics)
            self._update_component_metrics("ram", metrics)
            self._update_component_metrics("network", metrics)
                
        except Exception as e:
            print(f"Error updating metrics display: {e}")
    
    def _update_component_metrics(self, component_name, metrics):
        """Update a specific component's metrics based on configuration"""
        if not self.config["display"][f"show_{component_name}"] or component_name not in metrics or not metrics[component_name]:
            return
            
        component_data = metrics[component_name]
        
        # Define metric handlers for each component
        metric_handlers = {
            "cpu": {
                "cpu_usage": self._format_cpu_usage,
                "cpu_temperature": self._format_cpu_temperature,
                "cpu_frequency": self._format_cpu_frequency,
                "cpu_voltage": self._format_cpu_voltage
            },
            "gpu": {
                "gpu_core_usage": self._format_gpu_core_usage,
                "gpu_core_temperature": self._format_gpu_core_temperature,
                "gpu_core_frequency": self._format_gpu_core_frequency,
                "gpu_memory_frequency": self._format_gpu_memory_frequency,
                "gpu_memory_temperature": self._format_gpu_memory_temperature,
                "gpu_hotspot_temperature": self._format_gpu_hotspot_temperature,
                "gpu_vram_usage": self._format_gpu_vram_usage,
                "gpu_vram_memory": self._format_gpu_vram_memory,
                "gpu_fan_speed": self._format_gpu_fan_speed
            },
            "ram": {
                "ram_percent": self._format_ram_percent,
                "ram_used_total": self._format_ram_used_total,
                "ram_available": self._format_ram_available,
                "ram_temperature": self._format_ram_temperature
            },
            "network": {
                "network_upload_speed": self._format_network_upload,
                "network_download_speed": self._format_network_download,
                "network_total_sent": self._format_network_sent,
                "network_total_received": self._format_network_received
            }
        }
        
        # Collect all enabled metrics for this component
        metrics_to_display = []
        for metric_key, formatter in metric_handlers[component_name].items():
            display_key = f"show_{metric_key}"
            if display_key in self.config["display"] and self.config["display"][display_key]:
                # Get order for this metric
                order = self.config["layout"]["metric_order"].get(metric_key, 999)
                # Format the metric text
                formatted_text = formatter(component_data)
                # Store tuple of (order, formatted_text)
                metrics_to_display.append((order, formatted_text))
        
        # Sort metrics by their configured order
        metrics_to_display.sort(key=lambda x: x[0])
        
        # Extract just the formatted text from the sorted list
        display_texts = [item[1] for item in metrics_to_display]
        
        # Update labels in the component
        labels = self.component_labels[component_name]
        for i, text in enumerate(display_texts):
            if i < len(labels):
                labels[i].setText(text)
                labels[i].setVisible(True)  # Make label visible
        
        # Hide any unused labels
        for i in range(len(display_texts), len(labels)):
            labels[i].setText("")
            labels[i].setVisible(False)  # Hide unused labels
    
    # CPU metric formatters
    def _format_cpu_usage(self, data):
        usage = data.get("usage")
        return f"Usage: {usage:.1f}%" if usage is not None else "Usage: N/A"
    
    def _format_cpu_temperature(self, data):
        temp = data.get("temperature")
        return f"Temp: {temp:.1f}°C" if temp is not None else "Temp: N/A"
    
    def _format_cpu_frequency(self, data):
        freq = data.get("frequency")
        if freq is not None:
            # Convert MHz to GHz if needed
            if freq > 1000:  # If value is in MHz
                freq = freq / 1000
            return f"Freq: {freq:.2f} GHz"
        return "Freq: N/A"
    
    def _format_cpu_voltage(self, data):
        voltage = data.get("voltage")
        return f"Voltage: {voltage:.3f}V" if voltage is not None else "Voltage: N/A"
    
    # GPU metric formatters
    def _format_gpu_core_usage(self, data):
        usage = data.get("core_usage")
        return f"Core Usage: {usage:.1f}%" if usage is not None else "Core Usage: N/A"
    
    def _format_gpu_core_temperature(self, data):
        temp = data.get("core_temperature")
        return f"Core Temp: {temp:.1f}°C" if temp is not None else "Core Temp: N/A"
    
    def _format_gpu_core_frequency(self, data):
        freq = data.get("core_frequency")
        return f"Core Freq: {freq:.0f} MHz" if freq is not None else "Core Freq: N/A"
    
    def _format_gpu_memory_frequency(self, data):
        freq = data.get("memory_frequency")
        return f"Mem Freq: {freq:.0f} MHz" if freq is not None else "Mem Freq: N/A"
    
    def _format_gpu_memory_temperature(self, data):
        temp = data.get("memory_temperature")
        return f"Mem Temp: {temp:.1f}°C" if temp is not None else "Mem Temp: N/A"
    
    def _format_gpu_hotspot_temperature(self, data):
        temp = data.get("hotspot_temperature")
        return f"Hotspot: {temp:.1f}°C" if temp is not None else "Hotspot: N/A"
    
    def _format_gpu_vram_usage(self, data):
        usage = data.get("vram_usage_percent")
        return f"VRAM usage: {usage:.1f}%" if usage is not None else "VRAM usage: N/A"
    
    def _format_gpu_vram_memory(self, data):
        used = data.get("vram_used_gb")
        total = data.get("vram_total_gb")
        if used is not None and total is not None and total > 0:
            return f"VRAM: {used:.1f}/{total:.1f} GB"
        return "VRAM: N/A"
    
    def _format_gpu_fan_speed(self, data):
        speed = data.get("fan_speed")
        return f"Fan: {speed:.0f}%" if speed is not None else "Fan: N/A"
    
    # RAM metric formatters
    def _format_ram_percent(self, data):
        percent = data.get("percent")
        return f"Usage: {percent:.1f}%" if percent is not None else "Usage: N/A"
    
    def _format_ram_used_total(self, data):
        used = data.get("used")
        total = data.get("total")
        if used is not None and total is not None:
            return f"Used: {used:.1f}/{total:.1f} GB"
        return "Used: N/A"
    
    def _format_ram_available(self, data):
        available = data.get("available")
        return f"Available: {available:.1f} GB" if available is not None else "Available: N/A"
    
    def _format_ram_temperature(self, data):
        temp = data.get("ram_temperature")
        return f"Temp: {temp:.1f}°C" if temp is not None else "Temp: N/A"
    
    # Network metric formatters
    def _format_network_upload(self, data):
        upload = data.get("upload_speed")
        return f"Upload: {upload:.2f} MB/s" if upload is not None else "Upload: N/A"
    
    def _format_network_download(self, data):
        download = data.get("download_speed")
        return f"Download: {download:.2f} MB/s" if download is not None else "Download: N/A"
    
    def _format_network_sent(self, data):
        sent = data.get("total_sent")
        return f"Total Sent: {sent:.1f} GB" if sent is not None else "Total Sent: N/A"
    
    def _format_network_received(self, data):
        received = data.get("total_received")
        return f"Total Recv: {received:.1f} GB" if received is not None else "Total Recv: N/A"
                        
    def update_style(self):
        """Update the widget style based on current settings"""
        opacity = self.config["appearance"]["opacity"]
        bg_color = QColor(self.config["appearance"]["background_color"])
        
        # Set widget background - completely transparent regardless of opacity setting
        self.setObjectName("hardwareMonitorWidget")
        self.setStyleSheet(f"""
            #hardwareMonitorWidget {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        # Update font for labels
        font = QFont(
            self.config["appearance"]["font_family"],
            self.config["appearance"]["font_size"]
        )
        
        # Apply configured opacity to text color only
        color = QColor(self.config["appearance"]["font_color"])
        
        # Create style for labels with the opacity applied only to text
        label_style = f"color: rgba({color.red()}, {color.green()}, {color.blue()}, {opacity});"
        
        # Apply to specific widget labels, not to all QLabels in the application
        for labels in [getattr(self, attr, []) for attr in ["cpu_labels", "gpu_labels", "ram_labels", "network_labels"]]:
            for label in labels:
                if label:
                    label.setFont(font)
                    label.setStyleSheet(label_style)
        
        # Aplicar también a las etiquetas de título si existen
        for title_label in [getattr(self, attr, None) for attr in ["cpu_title", "gpu_title", "ram_title", "network_title"]]:
            if title_label:
                title_label.setFont(font)
                title_label.setStyleSheet(label_style)
        
        # Update padding
        padding = self.config["appearance"]["padding"]
        if hasattr(self, 'main_layout'):
            self.main_layout.setContentsMargins(padding, padding, padding, padding)
    
    def apply_position(self):
        """Apply the configured position to the widget"""
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
        
        # Ensure the widget is displayed completely on the selected monitor
        # First, reset any previous size constraints
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX
        
        # Set a flexible size policy that allows the widget to grow/shrink based on content
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Update the size to fit the content exactly
        self.adjustSize()
        
        # Add extra padding to prevent text from being cut off
        extra_margin = 40  # pixels of extra margin to avoid text clipping
        self.resize(self.width() + extra_margin, self.height() + extra_margin)
        
        # Get the final geometry for position calculation
        window_geo = self.geometry()
        
        # Get offset values
        offset_x = self.config["appearance"].get("offset_x", 0)
        offset_y = self.config["appearance"].get("offset_y", 0)
        
        x, y = screen_geo.x(), screen_geo.y()  # Start with monitor's top-left position
        
        if position == "top-left":
            # No adjustment needed for top-left
            pass
        elif position == "top-right":
            x = screen_geo.x() + screen_geo.width() - window_geo.width()
        elif position == "bottom-left":
            # For bottom positions, add extra bottom padding to prevent text clipping
            y = screen_geo.y() + screen_geo.height() - window_geo.height() - 10
        elif position == "bottom-right":
            x = screen_geo.x() + screen_geo.width() - window_geo.width()
            # For bottom positions, add extra bottom padding to prevent text clipping
            y = screen_geo.y() + screen_geo.height() - window_geo.height() - 10
        elif position == "center":
            x = screen_geo.x() + (screen_geo.width() - window_geo.width()) // 2
            y = screen_geo.y() + (screen_geo.height() - window_geo.height()) // 2
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
        elif x > screen_right - window_geo.width():
            x = screen_right - window_geo.width()
            
        if y < screen_geo.y():
            y = screen_geo.y()
        elif y > screen_bottom - window_geo.height():
            y = screen_bottom - window_geo.height()
        
        # Move widget to calculated position
        self.move(x, y)
    
    def setup_system_tray(self):
        """Set up system tray icon and menu"""
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set icon
        self.update_tray_icon()
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Add actions
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        # Hide/Show action
        self.toggle_action = QAction("Hide", self)
        self.toggle_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.toggle_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        # Set the menu
        self.tray_icon.setContextMenu(tray_menu)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def update_tray_icon(self):
        """Update the tray icon based on system status"""
        # Check if metrics are available
        if not hasattr(self, 'tray_icon') or not self.tray_icon:
            return
            
        if self.last_metrics and "cpu" in self.last_metrics:
            try:
                cpu_usage = self.last_metrics["cpu"].get("cpu_usage", 0)
                
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
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visibility()
    
    def toggle_visibility(self):
        """Toggle widget visibility"""
        if self.isVisible():
            self.hide()
            self.toggle_action.setText("Show")
        else:
            self.show()
            self.apply_position()
            self.toggle_action.setText("Hide")
    
    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # If dialog was accepted, update and save config
            self.config = dialog.get_config()
            self.save_config()
            
            # Apply new settings
            self.setup_metric_sections()
            self.update_style()
            self.apply_position()
            
            # Restart metrics worker with new refresh rate
            self.start_metrics_worker(restart=True)
    
    def start_metrics_worker(self, restart=False):
        """Start or restart the metrics worker thread"""
        # Stop existing worker if restarting
        if restart and self.metrics_worker.running:
            self.stop_metrics_worker()
        
        # Ensure the interval is correct (between 0.1 and 5 seconds)
        interval = self.config["appearance"]["refresh_rate"]
        if interval < 0.1:
            interval = 0.1
        elif interval > 5.0:
            interval = 5.0
            
        print(f"Starting metrics collector with interval: {interval} seconds")
        
        # Start worker thread
        self.metrics_worker.start(interval=interval)
    
    def start_metrics_worker_alternate(self, restart=False):
        """Start or restart the metrics worker thread"""
        # Stop existing worker if restarting
        if restart and self.metrics_worker.running:
            self.stop_metrics_worker()
        
        # Ensure the interval is correct (between 0.1 and 5 seconds)
        interval = self.config["appearance"]["refresh_rate"]
        if interval < 0.1:
            interval = 0.1
        elif interval > 5.0:
            interval = 5.0
            
        print(f"Starting metrics collector with interval: {interval} seconds")
        
        # Start worker thread
        self.metrics_worker.start(interval=interval)
    
    def exit_app(self):
        """Exit the application"""
        # Stop the metrics worker thread
        self.stop_metrics_worker()
        
        # Save configuration before exit
        self.save_config()
        
        # Quit the application
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
            self.move(event.globalPosition().toPoint() - self.drag_position)
            # Update custom position in config
            pos = self.pos()
            self.config["appearance"]["custom_position"] = [pos.x(), pos.y()]
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging"""
        if event.button() == Qt.MouseButton.LeftButton and self.draggable:
            self.drag_position = None
            # Save the final position
            self.save_config()
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_settings()
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed
    
    widget = HardwareWidget()
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
