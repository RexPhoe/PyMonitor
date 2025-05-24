"""
Metrics Display Module

This module contains the widget for displaying hardware metrics.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

class MetricsDisplay(QWidget):
    """Widget responsible for displaying formatted hardware metrics"""
    
    def __init__(self, config):
        """
        Initialize the metrics display widget.
        
        Args:
            config: Application configuration dictionary
        """
        super().__init__()
        
        self.config = config
        
        # Dictionaries to store label references
        self.component_titles = {}
        self.component_labels = {
            "cpu": [], 
            "gpu": [], 
            "ram": [], 
            "network": []
        }
        
        # Set sizing policies for proper rendering - use MinimumExpanding to ensure content gets full space
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        
        # Set up UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components for displaying metrics"""
        # Create layout for metrics with minimal spacing to ensure full-width usage
        self.main_layout = QVBoxLayout(self)
        
        # Minimize padding to match original behavior
        padding = 0
        self.main_layout.setContentsMargins(padding, padding, padding, padding)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Create main container that will automatically adapt to the content size
        self.main_container = QWidget()
        self.main_container.setMinimumWidth(self.config["appearance"]["max_width"])
        
        # Create layout based on configuration
        if self.config["layout"]["type"] == "horizontal":
            self.content_layout = QHBoxLayout(self.main_container)
        elif self.config["layout"]["type"] == "grid":
            self.content_layout = QGridLayout(self.main_container)
        else:  # Default to vertical
            self.content_layout = QVBoxLayout(self.main_container)
        
        # Set spacing and margins - minimal to maximize usable space
        spacing = self.config["layout"]["spacing"]
        self.content_layout.setSpacing(spacing)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add container directly to the main layout
        self.main_layout.addWidget(self.main_container)
        
        # Ensure container has no border and proper sizing policy
        self.main_container.setStyleSheet("border: none; background-color: transparent;")
        self.main_container.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        
        # Setup metric sections
        self.setup_metric_sections()
        
        # Set widget attributes for transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        # Apply style (border and opacity)
        self.update_style()
    
    def setup_metric_sections(self):
        """Create sections for each hardware component using flexible layout"""
        # Clear existing widgets if any
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Also clear sublayouts
                while item.layout().count():
                    subitem = item.layout().takeAt(0)
                    if subitem.widget():
                        subitem.widget().deleteLater()
        
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
        
        # Grid layout positioning helpers
        grid_row, grid_col = 0, 0
        num_columns = self.config["layout"].get("columns", 2)
        
        # Create sections for each component
        for component_name, _ in components:
            # Create container for this component with proper sizing
            component_container = QWidget()
            component_container.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
            component_layout = QVBoxLayout(component_container)
            component_layout.setContentsMargins(5, 5, 5, 5)
            component_layout.setSpacing(2)
            
            # Add title if enabled
            if self.config["display"]["show_titles"]:
                title_text = component_name.upper()
                title_label = QLabel(title_text)
                title_font = QFont(font)
                title_font.setBold(True)
                title_label.setFont(title_font)
                title_label.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
                title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                title_label.setMinimumWidth(self.config["appearance"]["max_width"] - 20)
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
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                label.setMinimumWidth(self.config["appearance"]["max_width"] - 20)
                label.setMinimumHeight(self.config["appearance"]["font_size"] + 10)  # Ensure height based on font size
                label.setWordWrap(False)  # Prevent text wrapping
                label.setVisible(False)  # Hidden by default until populated
                component_layout.addWidget(label)
                labels.append(label)
            
            # Store labels in the appropriate dictionary
            self.component_labels[component_name] = labels
            
            # Apply styles to component container - add border support
            if self.config["appearance"].get("show_border", False):
                border_color = self.config["appearance"].get("border_color", "#000000")
                component_container.setStyleSheet(f"background-color: transparent; border: 2px solid {border_color}; min-width: {self.config['appearance']['max_width']-10}px;")
            else:
                component_container.setStyleSheet(f"background-color: transparent; border: none; min-width: {self.config['appearance']['max_width']-10}px;")
            
            # Add the component container to the layout based on type
            if self.config["layout"]["type"] == "grid":
                self.content_layout.addWidget(component_container, grid_row, grid_col)
                grid_col += 1
                if grid_col >= num_columns:
                    grid_col = 0
                    grid_row += 1
            else:
                self.content_layout.addWidget(component_container)
                
        # Add a stretch at the end if not using grid layout
        if self.config["layout"]["type"] != "grid":
            self.content_layout.addStretch()
    
    def update_style(self):
        """Update the widget style based on configuration"""
        # Apply border if enabled
        if self.config["appearance"].get("show_border", False):
            border_color = self.config["appearance"]["border_color"]
            border_style = f"border: 2px solid {border_color};"
        else:
            border_style = "border: none;"
            
        # Apply styles to the widget
        self.setStyleSheet(f"""
            background-color: transparent;
            {border_style}
        """)
        
        # Update font for labels
        font = QFont(
            self.config["appearance"]["font_family"],
            self.config["appearance"]["font_size"]
        )
        
        color = QColor(self.config["appearance"]["font_color"])
        
        # Update component titles and labels
        for component_name, title_label in self.component_titles.items():
            if title_label:
                title_font = QFont(font)
                title_font.setBold(True)
                title_label.setFont(title_font)
                title_label.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
        
        # Update component labels
        for component_name, labels in self.component_labels.items():
            for label in labels:
                label.setFont(font)
                label.setStyleSheet(f"color: {color.name()};")
    
    def update_metrics(self, formatted_metrics):
        """
        Update the displayed metrics.
        
        Args:
            formatted_metrics: Dictionary of formatted metrics for each component
        """
        try:
            # Update each component section
            for component_name in ["cpu", "gpu", "ram", "network"]:
                if component_name in formatted_metrics:
                    self._update_component_display(component_name, formatted_metrics[component_name])
        except Exception as e:
            print(f"Error updating metrics display: {e}")
    
    def _update_component_display(self, component_name, metrics_dict):
        """
        Update a specific component's display with formatted metrics.
        
        Args:
            component_name: Name of the component (cpu, gpu, ram, network)
            metrics_dict: Dictionary of formatted metrics for this component
        """
        if not self.config["display"][f"show_{component_name}"]:
            return
            
        # Collect all metrics for this component in the correct order
        metrics_to_display = []
        for metric_key, text in metrics_dict.items():
            display_key = f"show_{metric_key}"
            if display_key in self.config["display"] and self.config["display"][display_key]:
                # Get order for this metric
                order = self.config["layout"]["metric_order"].get(metric_key, 999)
                # Store tuple of (order, text)
                metrics_to_display.append((order, text))
        
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
    
    def sizeHint(self):
        """
        Get the suggested size for the widget.
        
        Returns:
            QSize: The suggested size
        """
        # Use the maximum allowed size from configuration
        return QSize(
            self.config["appearance"]["max_width"],
            self.config["appearance"]["max_height"]
        )
