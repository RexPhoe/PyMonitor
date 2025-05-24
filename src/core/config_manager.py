"""
Configuration Manager Module

This module handles loading, saving, and managing application configuration.
"""

import os
import json

# Default configuration
DEFAULT_CONFIG = {
    "appearance": {
        "font_family": "Consolas",
        "font_size": 10,
        "font_color": "#FFFFFF",
        "border_color": "#000000",
        "show_border": False,
        "opacity": 0.7,
        "refresh_rate": 1.0,  # seconds
        "position": "bottom-right",
        "padding": 10,
        "custom_position": [100, 100],  # [x, y]
        "max_width": 400,
        "max_height": 800,
        "monitor_index": 0,
        "offset_x": 0,
        "offset_y": 0
    },
    "layout": {
        "type": "vertical",  # "vertical", "horizontal", or "grid"
        "columns": 2,
        "spacing": 5,
        "use_scroll": True,
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
        
        # CPU metrics
        "show_cpu_usage": True,
        "show_cpu_temperature": True,
        "show_cpu_frequency": True,
        "show_cpu_voltage": True,
        
        # GPU metrics
        "show_gpu_core_usage": True,
        "show_gpu_core_temperature": True,
        "show_gpu_core_frequency": True,
        "show_gpu_memory_frequency": True,
        "show_gpu_memory_temperature": True,
        "show_gpu_hotspot_temperature": True,
        "show_gpu_vram_usage": True,
        "show_gpu_vram_memory": True,
        "show_gpu_fan_speed": True,
        
        # RAM metrics
        "show_ram_percent": True,
        "show_ram_used_total": True,
        "show_ram_available": True,
        "show_ram_temperature": True,
        
        # Network metrics
        "show_network_upload_speed": True,
        "show_network_download_speed": True,
        "show_network_total_sent": True,
        "show_network_total_received": True
    }
}

class ConfigManager:
    """Manages application configuration loading and saving"""
    
    def __init__(self, config_path=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses the default location.
        """
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')
        else:
            self.config_path = config_path
        
        self.config = self.load_config()
    
    def load_config(self):
        """
        Load configuration from file or use defaults.
        
        Returns:
            dict: The loaded configuration
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
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
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save. If None, uses the current configuration.
        """
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_config(self):
        """
        Get the current configuration.
        
        Returns:
            dict: The current configuration
        """
        return self.config
    
    def update_config(self, config):
        """
        Update the current configuration.
        
        Args:
            config: New configuration to use
        """
        self.config = config
        self.save_config()
