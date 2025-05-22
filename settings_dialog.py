"""
Settings Dialog for Hardware Monitor Desktop Widget

This module provides the settings dialog for configuring the appearance and behavior
of the hardware monitor desktop widget.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QLabel, QSlider, QComboBox, QCheckBox, QSpinBox,
                           QPushButton, QColorDialog, QFontDialog, QGroupBox,
                           QFormLayout, QFrame, QListWidget, QListWidgetItem,
                           QRadioButton, QApplication, QWidget)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QFont, QPalette
import copy


class SettingsDialog(QDialog):
    """Dialog for configuring the hardware monitor widget"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hardware Monitor Settings")
        self.setMinimumWidth(500)
        
        # Store original config and create a working copy
        self.original_config = config
        self.config = copy.deepcopy(config)
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the settings dialog UI"""
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Create tabs
        appearance_tab = self.create_appearance_tab()
        display_tab = self.create_display_tab()
        layout_tab = self.create_layout_tab()
        
        # Add tabs
        tabs.addTab(appearance_tab, "Appearance")
        tabs.addTab(display_tab, "Display")
        tabs.addTab(layout_tab, "Layout")
        metrics_order_tab = self.create_metrics_order_tab()
        tabs.addTab(metrics_order_tab, "Metrics Order")
        
        # Add tab widget to layout
        main_layout.addWidget(tabs)
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_defaults)
        button_layout.addWidget(reset_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)
    
    def create_appearance_tab(self):
        """Create the appearance settings tab"""
        tab = QFrame()
        layout = QVBoxLayout(tab)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        # Font picker button
        self.font_button = QPushButton("Change Font...")
        self.font_button.clicked.connect(self.pick_font)
        
        # Show current font
        current_font = QFont(
            self.config["appearance"]["font_family"],
            self.config["appearance"]["font_size"]
        )
        self.font_button.setFont(current_font)
        self.font_button.setText(f"{current_font.family()}, {current_font.pointSize()}pt")
        
        font_layout.addRow("Font:", self.font_button)
        layout.addWidget(font_group)
        
        # Color settings
        color_group = QGroupBox("Colors")
        color_layout = QFormLayout(color_group)
        
        # Text color button
        self.text_color_button = QPushButton()
        self.text_color_button.setAutoFillBackground(True)
        self.set_button_color(self.text_color_button, self.config["appearance"]["font_color"])
        self.text_color_button.clicked.connect(self.pick_text_color)
        color_layout.addRow("Text Color:", self.text_color_button)
        
        # Background color button
        self.bg_color_button = QPushButton()
        self.bg_color_button.setAutoFillBackground(True)
        self.set_button_color(self.bg_color_button, self.config["appearance"]["background_color"])
        self.bg_color_button.clicked.connect(self.pick_bg_color)
        color_layout.addRow("Background Color:", self.bg_color_button)
        
        layout.addWidget(color_group)
        
        # Opacity settings
        opacity_group = QGroupBox("Opacity")
        opacity_layout = QFormLayout(opacity_group)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(10)  # 10% opacity minimum
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self.config["appearance"]["opacity"] * 100))
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        self.opacity_slider.valueChanged.connect(
            lambda value: self.opacity_label.setText(f"{value}%")
        )
        
        opacity_layout.addRow("Font Opacity:", self.opacity_slider)
        opacity_layout.addRow("", self.opacity_label)
        
        layout.addWidget(opacity_group)
        
        # Position settings
        position_group = QGroupBox("Position")
        position_layout = QFormLayout(position_group)
        
        # Create position combo box
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center", "Custom"])
        
        # Set current position
        position_map = {"top-left": 0, "top-right": 1, "bottom-left": 2, "bottom-right": 3, "center": 4, "custom": 5}
        current_position = self.config["appearance"]["position"]
        self.position_combo.setCurrentIndex(position_map.get(current_position, 3))  # Default to bottom-right
        position_layout.addRow("Position:", self.position_combo)
        
        # Monitor selection
        self.monitor_combo = QComboBox()
        # Get available screens from the application
        screens = QApplication.screens()
        self.monitor_combo.addItems([f"Monitor {i+1}: {screen.name()}" for i, screen in enumerate(screens)])
        
        # Set current monitor
        current_monitor = self.config["appearance"].get("monitor_index", 0)
        if current_monitor < self.monitor_combo.count():
            self.monitor_combo.setCurrentIndex(current_monitor)
        position_layout.addRow("Monitor:", self.monitor_combo)
        
        # Padding setting
        self.padding_spin = QSpinBox()
        self.padding_spin.setMinimum(0)
        self.padding_spin.setMaximum(50)
        self.padding_spin.setValue(self.config["appearance"]["padding"])
        position_layout.addRow("Padding:", self.padding_spin)
        
        # Fine-tuning position with offset X and Y (without limits)
        self.offset_x_spin = QSpinBox()
        self.offset_x_spin.setMinimum(-10000)  # Very large negative value
        self.offset_x_spin.setMaximum(10000)   # Very large positive value
        self.offset_x_spin.setValue(self.config["appearance"].get("offset_x", 0))
        position_layout.addRow("X Offset:", self.offset_x_spin)
        
        self.offset_y_spin = QSpinBox()
        self.offset_y_spin.setMinimum(-10000)  # Very large negative value
        self.offset_y_spin.setMaximum(10000)   # Very large positive value
        self.offset_y_spin.setValue(self.config["appearance"].get("offset_y", 0))
        position_layout.addRow("Y Offset:", self.offset_y_spin)
        
        layout.addWidget(position_group)
        
        # Refresh rate
        refresh_group = QGroupBox("Refresh Rate")
        refresh_layout = QFormLayout(refresh_group)
        
        self.refresh_combo = QComboBox()
        refresh_rates = [0.5, 1.0, 2.0, 5.0]
        self.refresh_combo.addItems([f"{rate} seconds" for rate in refresh_rates])
        
        # Set current refresh rate
        current_rate = self.config["appearance"]["refresh_rate"]
        index = refresh_rates.index(current_rate) if current_rate in refresh_rates else 1  # Default to 1.0
        self.refresh_combo.setCurrentIndex(index)
        
        refresh_layout.addRow("Update Interval:", self.refresh_combo)
        layout.addWidget(refresh_group)
        
        layout.addStretch()
        return tab
    
    def create_display_tab(self):
        """Create the display settings tab"""
        tab = QFrame()
        layout = QVBoxLayout(tab)
        
        # Component visibility
        components_group = QGroupBox("Show Components")
        components_layout = QVBoxLayout(components_group)
        
        # Main components checkboxes
        self.show_cpu = QCheckBox("CPU")
        self.show_cpu.setChecked(self.config["display"]["show_cpu"])
        self.show_cpu.stateChanged.connect(self._on_main_component_toggled)
        components_layout.addWidget(self.show_cpu)
        
        self.show_gpu = QCheckBox("GPU")
        self.show_gpu.setChecked(self.config["display"]["show_gpu"])
        self.show_gpu.stateChanged.connect(self._on_main_component_toggled)
        components_layout.addWidget(self.show_gpu)
        
        self.show_ram = QCheckBox("RAM")
        self.show_ram.setChecked(self.config["display"]["show_ram"])
        self.show_ram.stateChanged.connect(self._on_main_component_toggled)
        components_layout.addWidget(self.show_ram)
        
        self.show_network = QCheckBox("Network")
        self.show_network.setChecked(self.config["display"]["show_network"])
        self.show_network.stateChanged.connect(self._on_main_component_toggled)
        components_layout.addWidget(self.show_network)
        
        layout.addWidget(components_group)
        
        # Display options
        options_group = QGroupBox("Display Options")
        options_layout = QVBoxLayout(options_group)
        
        self.show_titles = QCheckBox("Show Section Titles")
        self.show_titles.setChecked(self.config["display"]["show_titles"])
        options_layout.addWidget(self.show_titles)
        
        self.compact_mode = QCheckBox("Compact Mode")
        self.compact_mode.setChecked(self.config["display"]["compact_mode"])
        options_layout.addWidget(self.compact_mode)
        
        layout.addWidget(options_group)
        
        # Create detailed metric options for each component
        self.tabs_detailed = QTabWidget()
        
        # CPU metrics tab
        cpu_tab = QFrame()
        cpu_layout = QVBoxLayout(cpu_tab)
        
        cpu_layout.addWidget(QLabel("<b>CPU Metrics</b>"))
        
        self.show_cpu_usage = QCheckBox("Show CPU Usage")
        self.show_cpu_usage.setChecked(self.config["display"]["show_cpu_usage"])
        cpu_layout.addWidget(self.show_cpu_usage)
        
        self.show_cpu_temperature = QCheckBox("Show CPU Temperature")
        self.show_cpu_temperature.setChecked(self.config["display"]["show_cpu_temperature"])
        cpu_layout.addWidget(self.show_cpu_temperature)
        
        self.show_cpu_frequency = QCheckBox("Show CPU Frequency")
        self.show_cpu_frequency.setChecked(self.config["display"]["show_cpu_frequency"])
        cpu_layout.addWidget(self.show_cpu_frequency)
        
        self.show_cpu_voltage = QCheckBox("Show CPU Voltage")
        self.show_cpu_voltage.setChecked(self.config["display"]["show_cpu_voltage"])
        cpu_layout.addWidget(self.show_cpu_voltage)
        
        cpu_tab.setEnabled(self.config["display"]["show_cpu"])
        self.tabs_detailed.addTab(cpu_tab, "CPU Metrics")
        
        # GPU metrics tab
        gpu_tab = QFrame()
        gpu_layout = QVBoxLayout(gpu_tab)
        
        gpu_layout.addWidget(QLabel("<b>GPU Core Metrics</b>"))
        
        self.show_gpu_core_usage = QCheckBox("Show GPU Core Usage")
        self.show_gpu_core_usage.setChecked(self.config["display"]["show_gpu_core_usage"])
        gpu_layout.addWidget(self.show_gpu_core_usage)
        
        self.show_gpu_core_temperature = QCheckBox("Show GPU Core Temperature")
        self.show_gpu_core_temperature.setChecked(self.config["display"]["show_gpu_core_temperature"])
        gpu_layout.addWidget(self.show_gpu_core_temperature)
        
        self.show_gpu_core_frequency = QCheckBox("Show GPU Core Frequency")
        self.show_gpu_core_frequency.setChecked(self.config["display"]["show_gpu_core_frequency"])
        gpu_layout.addWidget(self.show_gpu_core_frequency)
        
        self.show_gpu_hotspot_temperature = QCheckBox("Show GPU Hotspot Temperature")
        self.show_gpu_hotspot_temperature.setChecked(self.config["display"]["show_gpu_hotspot_temperature"])
        gpu_layout.addWidget(self.show_gpu_hotspot_temperature)
        
        gpu_layout.addWidget(QLabel("<b>GPU Memory Metrics</b>"))
        
        self.show_gpu_memory_frequency = QCheckBox("Show GPU Memory Frequency")
        self.show_gpu_memory_frequency.setChecked(self.config["display"]["show_gpu_memory_frequency"])
        gpu_layout.addWidget(self.show_gpu_memory_frequency)
        
        self.show_gpu_memory_temperature = QCheckBox("Show GPU Memory Temperature")
        self.show_gpu_memory_temperature.setChecked(self.config["display"]["show_gpu_memory_temperature"])
        gpu_layout.addWidget(self.show_gpu_memory_temperature)
        
        self.show_gpu_vram_usage = QCheckBox("Show GPU VRAM usage Percentage")
        self.show_gpu_vram_usage.setChecked(self.config["display"]["show_gpu_vram_usage"])
        gpu_layout.addWidget(self.show_gpu_vram_usage)
        
        self.show_gpu_vram_memory = QCheckBox("Show GPU VRAM Used/Total")
        self.show_gpu_vram_memory.setChecked(self.config["display"]["show_gpu_vram_memory"])
        gpu_layout.addWidget(self.show_gpu_vram_memory)
        
        gpu_layout.addWidget(QLabel("<b>GPU Other Metrics</b>"))
        
        self.show_gpu_fan_speed = QCheckBox("Show GPU Fan Speed")
        self.show_gpu_fan_speed.setChecked(self.config["display"]["show_gpu_fan_speed"])
        gpu_layout.addWidget(self.show_gpu_fan_speed)
        
        gpu_tab.setEnabled(self.config["display"]["show_gpu"])
        self.tabs_detailed.addTab(gpu_tab, "GPU Metrics")
        
        # RAM metrics tab
        ram_tab = QFrame()
        ram_layout = QVBoxLayout(ram_tab)
        
        ram_layout.addWidget(QLabel("<b>RAM Metrics</b>"))
        
        self.show_ram_percent = QCheckBox("Show RAM Usage Percent")
        self.show_ram_percent.setChecked(self.config["display"]["show_ram_percent"])
        ram_layout.addWidget(self.show_ram_percent)
        
        self.show_ram_used_total = QCheckBox("Show RAM Used/Total")
        self.show_ram_used_total.setChecked(self.config["display"]["show_ram_used_total"])
        ram_layout.addWidget(self.show_ram_used_total)
        
        self.show_ram_available = QCheckBox("Show RAM Available")
        self.show_ram_available.setChecked(self.config["display"]["show_ram_available"])
        ram_layout.addWidget(self.show_ram_available)
        
        self.show_ram_temperature = QCheckBox("Show RAM Temperature")
        self.show_ram_temperature.setChecked(self.config["display"]["show_ram_temperature"])
        ram_layout.addWidget(self.show_ram_temperature)
        
        ram_tab.setEnabled(self.config["display"]["show_ram"])
        self.tabs_detailed.addTab(ram_tab, "RAM Metrics")
        
        # Network metrics tab
        network_tab = QFrame()
        network_layout = QVBoxLayout(network_tab)
        
        network_layout.addWidget(QLabel("<b>Network Speed Metrics</b>"))
        
        self.show_network_upload_speed = QCheckBox("Show Upload Speed")
        self.show_network_upload_speed.setChecked(self.config["display"]["show_network_upload_speed"])
        network_layout.addWidget(self.show_network_upload_speed)
        
        self.show_network_download_speed = QCheckBox("Show Download Speed")
        self.show_network_download_speed.setChecked(self.config["display"]["show_network_download_speed"])
        network_layout.addWidget(self.show_network_download_speed)
        
        network_layout.addWidget(QLabel("<b>Network Total Metrics</b>"))
        
        self.show_network_total_sent = QCheckBox("Show Total Sent")
        self.show_network_total_sent.setChecked(self.config["display"]["show_network_total_sent"])
        network_layout.addWidget(self.show_network_total_sent)
        
        self.show_network_total_received = QCheckBox("Show Total Received")
        self.show_network_total_received.setChecked(self.config["display"]["show_network_total_received"])
        network_layout.addWidget(self.show_network_total_received)
        
        network_tab.setEnabled(self.config["display"]["show_network"])
        self.tabs_detailed.addTab(network_tab, "Network Metrics")
        
        layout.addWidget(self.tabs_detailed)
        
        layout.addStretch()
        return tab
    
    def create_layout_tab(self):
        """Create the layout settings tab"""
        tab = QFrame()
        layout = QVBoxLayout(tab)
        
        # Layout type selection
        type_group = QGroupBox("Layout Type")
        type_layout = QVBoxLayout(type_group)
        
        self.layout_vertical = QRadioButton("Vertical")
        self.layout_vertical.setChecked(self.config.get("layout", {}).get("type", "vertical") == "vertical")
        type_layout.addWidget(self.layout_vertical)
        
        self.layout_horizontal = QRadioButton("Horizontal")
        self.layout_horizontal.setChecked(self.config.get("layout", {}).get("type", "horizontal") == "horizontal")
        type_layout.addWidget(self.layout_horizontal)
        
        self.layout_grid = QRadioButton("Grid")
        self.layout_grid.setChecked(self.config.get("layout", {}).get("type", "grid") == "grid")
        type_layout.addWidget(self.layout_grid)
        
        # Grid columns (only active when grid layout is selected)
        grid_columns_layout = QHBoxLayout()
        grid_columns_layout.addWidget(QLabel("Grid Columns:"))
        self.grid_columns = QSpinBox()
        self.grid_columns.setMinimum(1)
        self.grid_columns.setMaximum(4)
        self.grid_columns.setValue(self.config.get("layout", {}).get("columns", 2))
        self.grid_columns.setEnabled(self.config.get("layout", {}).get("type", "grid") == "grid")
        grid_columns_layout.addWidget(self.grid_columns)
        type_layout.addLayout(grid_columns_layout)
        
        # Connect signals for enabling/disabling grid columns
        self.layout_grid.toggled.connect(self.grid_columns.setEnabled)
        
        layout.addWidget(type_group)
        
        # Layout options
        options_group = QGroupBox("Layout Options")
        options_layout = QFormLayout(options_group)
        
        # Spacing between elements
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setMinimum(0)
        self.spacing_spin.setMaximum(20)
        self.spacing_spin.setValue(self.config.get("layout", {}).get("spacing", 5))
        options_layout.addRow("Spacing:", self.spacing_spin)
        
        # Nota: Eliminamos las opciones de scrollbar y dimensiones máximas por petición del usuario
        
        layout.addWidget(options_group)
        
        # Component order configuration
        order_group = QGroupBox("Component Order")
        order_layout = QVBoxLayout(order_group)
        
        order_layout.addWidget(QLabel("Drag to reorder components (top = first):"))
        
        # Create a list widget for dragging and dropping components
        self.component_list = QListWidget()
        self.component_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Add components in their current order
        component_items = [
            ("CPU", "cpu", self.config.get("layout", {}).get("component_order", {}).get("cpu", 0)),
            ("GPU", "gpu", self.config.get("layout", {}).get("component_order", {}).get("gpu", 1)),
            ("RAM", "ram", self.config.get("layout", {}).get("component_order", {}).get("ram", 2)),
            ("Network", "network", self.config.get("layout", {}).get("component_order", {}).get("network", 3))
        ]
        component_items.sort(key=lambda x: x[2])  # Sort by current order
        
        for display_name, key, _ in component_items:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, key)  # Store the component key
            self.component_list.addItem(item)
        
        order_layout.addWidget(self.component_list)
        layout.addWidget(order_group)
        
        # Fine-tune positioning group (X/Y offset)
        position_group = QGroupBox("Fine-tune Positioning")
        position_layout = QFormLayout(position_group)
        
        # X offset
        self.x_offset = QSpinBox()
        self.x_offset.setMinimum(-100)
        self.x_offset.setMaximum(100)
        self.x_offset.setValue(self.config.get("appearance", {}).get("offset_x", 0))
        position_layout.addRow("X Offset:", self.x_offset)
        
        # Y offset
        self.y_offset = QSpinBox()
        self.y_offset.setMinimum(-100)
        self.y_offset.setMaximum(100)
        self.y_offset.setValue(self.config.get("appearance", {}).get("offset_y", 0))
        position_layout.addRow("Y Offset:", self.y_offset)
        
        layout.addWidget(position_group)
        
        layout.addStretch()
        return tab
    
    def create_metrics_order_tab(self):
        """Create tab for ordering individual metrics within each component"""
        tab = QFrame()
        layout = QVBoxLayout(tab)
        
        # Create a tab widget for different metric categories
        metrics_tabs = QTabWidget()
        
        # CPU metrics ordering
        cpu_tab = self.create_metrics_ordering_widget("cpu", [
            ("CPU Usage", "cpu_usage"),
            ("CPU Temperature", "cpu_temperature"),
            ("CPU Frequency", "cpu_frequency"),
            ("CPU Voltage", "cpu_voltage")
        ])
        metrics_tabs.addTab(cpu_tab, "CPU Metrics")
        
        # GPU metrics ordering
        gpu_tab = self.create_metrics_ordering_widget("gpu", [
            ("GPU Core Usage", "gpu_core_usage"),
            ("GPU Core Temperature", "gpu_core_temperature"),
            ("GPU Core Frequency", "gpu_core_frequency"),
            ("GPU Memory Frequency", "gpu_memory_frequency"),
            ("GPU Memory Temperature", "gpu_memory_temperature"),
            ("GPU Hotspot Temperature", "gpu_hotspot_temperature"),
            ("GPU VRAM usage", "gpu_vram_usage"),
            ("GPU VRAM Memory", "gpu_vram_memory"),
            ("GPU Fan Speed", "gpu_fan_speed")
        ])
        metrics_tabs.addTab(gpu_tab, "GPU Metrics")
        
        # RAM metrics ordering
        ram_tab = self.create_metrics_ordering_widget("ram", [
            ("RAM Usage Percent", "ram_percent"),
            ("RAM Used/Total", "ram_used_total"),
            ("RAM Available", "ram_available"),
            ("RAM Temperature", "ram_temperature")
        ])
        metrics_tabs.addTab(ram_tab, "RAM Metrics")
        
        # Network metrics ordering
        network_tab = self.create_metrics_ordering_widget("network", [
            ("Upload Speed", "network_upload_speed"),
            ("Download Speed", "network_download_speed"),
            ("Total Sent", "network_total_sent"),
            ("Total Received", "network_total_received")
        ])
        metrics_tabs.addTab(network_tab, "Network Metrics")
        
        layout.addWidget(metrics_tabs)
        layout.addStretch()
        return tab
    
    def create_metrics_ordering_widget(self, component, metrics):
        """Create a widget for ordering metrics of a specific component"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions
        layout.addWidget(QLabel("Drag to reorder metrics (top = first):"))
        
        # Create a list widget with drag and drop capability
        metrics_list = QListWidget()
        metrics_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Add metrics to the list in their current order
        metrics_to_display = []
        for display_name, metric_key in metrics:
            # Get current order or use default if not set
            order = self.config.get("layout", {}).get("metric_order", {}).get(metric_key, 999)
            # Only include metrics that are enabled
            if self.config["display"].get(f"show_{metric_key}", True):
                metrics_to_display.append((display_name, metric_key, order))
        
        # Sort by current order
        metrics_to_display.sort(key=lambda x: x[2])
        
        # Populate the list widget
        for display_name, metric_key, _ in metrics_to_display:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, metric_key)  # Store the metric key
            metrics_list.addItem(item)
        
        # Store reference to list widget
        setattr(self, f"{component}_metrics_list", metrics_list)
        
        layout.addWidget(metrics_list)
        return widget
        
    def _on_main_component_toggled(self, state):
        """Enable/disable detailed tabs when main component is toggled"""
        sender = self.sender()
        
        if sender == self.show_cpu:
            self.tabs_detailed.widget(0).setEnabled(state == Qt.CheckState.Checked)
        elif sender == self.show_gpu:
            self.tabs_detailed.widget(1).setEnabled(state == Qt.CheckState.Checked)
        elif sender == self.show_ram:
            self.tabs_detailed.widget(2).setEnabled(state == Qt.CheckState.Checked)
        elif sender == self.show_network:
            self.tabs_detailed.widget(3).setEnabled(state == Qt.CheckState.Checked)
    
    def set_button_color(self, button, color_str):
        """Set the background color of a button"""
        color = QColor(color_str)
        palette = button.palette()
        palette.setColor(QPalette.ColorRole.Button, color)
        button.setPalette(palette)
        
        # Set text to be visible against the background
        text_color = QColor(255, 255, 255) if color.lightness() < 128 else QColor(0, 0, 0)
        palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        button.setPalette(palette)
        
        # Show color hex code
        button.setText(color_str)
    
    def pick_font(self):
        """Open font dialog to pick a font"""
        current_font = QFont(
            self.config["appearance"]["font_family"],
            self.config["appearance"]["font_size"]
        )
        
        font, ok = QFontDialog.getFont(current_font, self, "Select Font")
        if ok:
            self.config["appearance"]["font_family"] = font.family()
            self.config["appearance"]["font_size"] = font.pointSize()
            self.font_button.setFont(font)
            self.font_button.setText(f"{font.family()}, {font.pointSize()}pt")
    
    def pick_text_color(self):
        """Open color dialog to pick text color"""
        current_color = QColor(self.config["appearance"]["font_color"])
        color = QColorDialog.getColor(current_color, self, "Select Text Color")
        
        if color.isValid():
            self.config["appearance"]["font_color"] = color.name()
            self.set_button_color(self.text_color_button, color.name())
    
    def pick_bg_color(self):
        """Open color dialog to pick background color"""
        current_color = QColor(self.config["appearance"]["background_color"])
        color = QColorDialog.getColor(current_color, self, "Select Background Color")
        
        if color.isValid():
            self.config["appearance"]["background_color"] = color.name()
            self.set_button_color(self.bg_color_button, color.name())
    
    def reset_defaults(self):
        """Reset all settings to default values"""
        # Define defaults
        defaults = {
            "appearance": {
                "font_family": "Consolas",
                "font_size": 10,
                "font_color": "#FFFFFF",
                "background_color": "#000000",
                "opacity": 0.7,
                "refresh_rate": 1.0,
                "position": "bottom-right",
                "padding": 10,
                "custom_position": [100, 100],
                "max_width": 800,
                "max_height": 600,
                "offset_x": 0,
                "offset_y": 0
            },
            "display": {
                "show_cpu": True,
                "show_gpu": True,
                "show_ram": True,
                "show_network": True,
                "show_titles": True,
                "compact_mode": False,
                
                # CPU detailed metrics
                "show_cpu_usage": True,
                "show_cpu_temperature": True,
                "show_cpu_frequency": True,
                "show_cpu_voltage": True,
                
                # GPU detailed metrics
                "show_gpu_core_usage": True,
                "show_gpu_core_temperature": True,
                "show_gpu_core_frequency": True,
                "show_gpu_memory_frequency": True,
                "show_gpu_memory_temperature": True,
                "show_gpu_hotspot_temperature": True,
                "show_gpu_vram_usage": True,
                "show_gpu_vram_memory": True,
                "show_gpu_fan_speed": True,
                
                # RAM detailed metrics
                "show_ram_percent": True,
                "show_ram_used_total": True,
                "show_ram_available": True,
                "show_ram_temperature": True,
                
                # Network detailed metrics
                "show_network_upload_speed": True,
                "show_network_download_speed": True,
                "show_network_total_sent": True,
                "show_network_total_received": True
            },
            "layout": {
                "type": "vertical",
                "columns": 2,
                "spacing": 5,
                "use_scroll": True,
                "component_order": {
                    "cpu": 0,
                    "gpu": 1,
                    "ram": 2,
                    "network": 3
                }
            }
        }
        
        # Update config
        self.config = copy.deepcopy(defaults)
        
        # Update UI to reflect defaults
        self.reject()  # Close dialog
        
        # Create a new dialog with default settings
        new_dialog = SettingsDialog(defaults, self.parent())
        new_dialog.exec()
    
    def get_config(self):
        """Get the current configuration from UI elements"""
        # Update config from UI elements
        
        # Appearance tab
        self.config["appearance"]["opacity"] = self.opacity_slider.value() / 100.0
        self.config["appearance"]["padding"] = self.padding_spin.value()
        
        # Position offset values
        self.config["appearance"]["offset_x"] = self.offset_x_spin.value()
        self.config["appearance"]["offset_y"] = self.offset_y_spin.value()
        
        # Position
        position_index = self.position_combo.currentIndex()
        positions = ["top-left", "top-right", "bottom-left", "bottom-right", "center", "custom"]
        self.config["appearance"]["position"] = positions[position_index]
        
        # Monitor selection
        self.config["appearance"]["monitor_index"] = self.monitor_combo.currentIndex()
        
        # Refresh rate
        refresh_index = self.refresh_combo.currentIndex()
        refresh_rates = [0.5, 1.0, 2.0, 5.0]
        self.config["appearance"]["refresh_rate"] = refresh_rates[refresh_index]
        
        # Display tab - Main components
        self.config["display"]["show_cpu"] = self.show_cpu.isChecked()
        self.config["display"]["show_gpu"] = self.show_gpu.isChecked()
        self.config["display"]["show_ram"] = self.show_ram.isChecked()
        self.config["display"]["show_network"] = self.show_network.isChecked()
        self.config["display"]["show_titles"] = self.show_titles.isChecked()
        self.config["display"]["compact_mode"] = self.compact_mode.isChecked()
        
        # CPU detailed metrics
        self.config["display"]["show_cpu_usage"] = self.show_cpu_usage.isChecked()
        self.config["display"]["show_cpu_temperature"] = self.show_cpu_temperature.isChecked()
        self.config["display"]["show_cpu_frequency"] = self.show_cpu_frequency.isChecked()
        self.config["display"]["show_cpu_voltage"] = self.show_cpu_voltage.isChecked()
        
        # GPU detailed metrics
        self.config["display"]["show_gpu_core_usage"] = self.show_gpu_core_usage.isChecked()
        self.config["display"]["show_gpu_core_temperature"] = self.show_gpu_core_temperature.isChecked()
        self.config["display"]["show_gpu_core_frequency"] = self.show_gpu_core_frequency.isChecked()
        self.config["display"]["show_gpu_memory_frequency"] = self.show_gpu_memory_frequency.isChecked()
        self.config["display"]["show_gpu_memory_temperature"] = self.show_gpu_memory_temperature.isChecked()
        self.config["display"]["show_gpu_hotspot_temperature"] = self.show_gpu_hotspot_temperature.isChecked()
        self.config["display"]["show_gpu_vram_usage"] = self.show_gpu_vram_usage.isChecked()
        self.config["display"]["show_gpu_vram_memory"] = self.show_gpu_vram_memory.isChecked()
        self.config["display"]["show_gpu_fan_speed"] = self.show_gpu_fan_speed.isChecked()
        
        # RAM detailed metrics
        self.config["display"]["show_ram_percent"] = self.show_ram_percent.isChecked()
        self.config["display"]["show_ram_used_total"] = self.show_ram_used_total.isChecked()
        self.config["display"]["show_ram_available"] = self.show_ram_available.isChecked()
        self.config["display"]["show_ram_temperature"] = self.show_ram_temperature.isChecked()
        
        # Network detailed metrics
        self.config["display"]["show_network_upload_speed"] = self.show_network_upload_speed.isChecked()
        self.config["display"]["show_network_download_speed"] = self.show_network_download_speed.isChecked()
        self.config["display"]["show_network_total_sent"] = self.show_network_total_sent.isChecked()
        self.config["display"]["show_network_total_received"] = self.show_network_total_received.isChecked()
        
        # Layout settings
        if "layout" not in self.config:
            self.config["layout"] = {}
            
        # Layout type
        if self.layout_vertical.isChecked():
            self.config["layout"]["type"] = "vertical"
        elif self.layout_horizontal.isChecked():
            self.config["layout"]["type"] = "horizontal"
        elif self.layout_grid.isChecked():
            self.config["layout"]["type"] = "grid"
            
        # Grid columns
        self.config["layout"]["columns"] = self.grid_columns.value()
        
        # Spacing
        self.config["layout"]["spacing"] = self.spacing_spin.value()
        
        # Always use auto-size and no scrollbar (eliminamos opciones de usuario)
        self.config["layout"]["use_scroll"] = False
        
        # Component order
        if "component_order" not in self.config["layout"]:
            self.config["layout"]["component_order"] = {}
            
        # Get order from list widget
        for i in range(self.component_list.count()):
            item = self.component_list.item(i)
            component_key = item.data(Qt.ItemDataRole.UserRole)
            self.config["layout"]["component_order"][component_key] = i
        
        # Individual metrics order
        if "metric_order" not in self.config["layout"]:
            self.config["layout"]["metric_order"] = {}
        
        # Save order for CPU metrics
        for i in range(self.cpu_metrics_list.count()):
            item = self.cpu_metrics_list.item(i)
            metric_key = item.data(Qt.ItemDataRole.UserRole)
            self.config["layout"]["metric_order"][metric_key] = i
        
        # Save order for GPU metrics
        for i in range(self.gpu_metrics_list.count()):
            item = self.gpu_metrics_list.item(i)
            metric_key = item.data(Qt.ItemDataRole.UserRole)
            self.config["layout"]["metric_order"][metric_key] = i
        
        # Save order for RAM metrics
        for i in range(self.ram_metrics_list.count()):
            item = self.ram_metrics_list.item(i)
            metric_key = item.data(Qt.ItemDataRole.UserRole)
            self.config["layout"]["metric_order"][metric_key] = i
        
        # Save order for Network metrics
        for i in range(self.network_metrics_list.count()):
            item = self.network_metrics_list.item(i)
            metric_key = item.data(Qt.ItemDataRole.UserRole)
            self.config["layout"]["metric_order"][metric_key] = i
        
        # Fine-tune positioning (X/Y offset)
        self.config["appearance"]["offset_x"] = self.x_offset.value()
        self.config["appearance"]["offset_y"] = self.y_offset.value()
        
        return self.config
