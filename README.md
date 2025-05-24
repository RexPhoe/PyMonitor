# PyMonitor

A lightweight desktop widget for real-time hardware monitoring, displaying CPU, GPU, RAM, and network metrics in a customizable, always-on-top interface.

## Project Structure

The project has been refactored into a modular, maintainable architecture:

```
PyMonitor/
├── src/                  # Main source code
│   ├── core/             # Core functionality
│   │   ├── config_manager.py    # Configuration handling
│   │   └── metrics_worker.py    # Background metrics collection
│   ├── ui/               # User interface components
│   │   ├── main_window.py       # Main application window
│   │   ├── metrics_display.py   # Widget for displaying metrics
│   │   ├── metrics_formatter.py # Formatting metrics for display
│   │   ├── position_manager.py  # Managing widget position
│   │   └── system_tray.py       # System tray functionality
│   └── utils/            # Utility functions
│       └── console_handler.py   # Console visibility management
├── monitor/              # Hardware monitoring modules
│   └── utils/            # Monitoring utilities
│       ├── cpu_metrics.py       # CPU metrics collection
│       ├── gpu_metrics.py       # GPU metrics collection
│       ├── hardware_monitor.py  # Main hardware monitoring
│       ├── network_metrics.py   # Network metrics collection
│       └── ram_metrics.py       # RAM metrics collection
├── desktop_widget.pyw    # Main entry point (Windows)
├── settings_dialog.py    # Settings configuration dialog
├── config.json           # User configuration
└── requirements.txt      # Project dependencies
```

![PyMonitor Screenshot](docs/screenshot.png)

## Features

- **Real-time Hardware Metrics**: Monitor CPU, GPU, RAM, and network usage
- **Always-on-top Display**: Keep metrics visible while using other applications
- **Customizable Layout**: Choose vertical, horizontal, or grid layouts
- **Detailed Metrics**: View detailed metrics for each hardware component
- **Customizable Appearance**: Adjust font, colors, opacity, and position
- **Reorderable Metrics**: Drag and drop to customize the order of metrics
- **Multi-monitor Support**: Position the widget on any connected display
- **System Tray Integration**: Control the widget from the system tray

## Metrics Collection

PyMonitor uses different methods to collect hardware metrics depending on the operating system:

### Windows

On Windows, PyMonitor uses a combination of:

- **psutil**: For basic CPU and RAM metrics
- **wmi**: For Windows Management Instrumentation queries
- **pynvml**: For NVIDIA GPU metrics
- **LibreHardwareMonitor**: For enhanced hardware metrics (temperature, frequency, etc.)

**Important**: For optimal metrics collection on Windows, it is strongly recommended to install and run [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) in the background. This provides access to detailed metrics like:

- CPU and GPU temperatures
- CPU and GPU clock frequencies
- GPU memory temperature
- Fan speeds
- Voltage information

Without LibreHardwareMonitor, some detailed metrics may show as "N/A" or have limited accuracy.

### Linux

On Linux, PyMonitor uses:

- **psutil**: For CPU, RAM, and network metrics
- **py3nvml**: For NVIDIA GPU metrics
- **sensors**: For temperature readings (requires `lm-sensors` package)

### macOS

On macOS, PyMonitor uses:

- **psutil**: For CPU, RAM, and network metrics
- Limited GPU support (basic information only)

## Installation

### Windows

1. Install Python 3.8 or later from [python.org](https://www.python.org/downloads/)
2. Clone or download this repository
3. Open a command prompt in the project directory
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python desktop_widget.pyw`

#### Windows-specific Setup for Enhanced Metrics

For optimal metrics collection on Windows:

1. Download and install [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. Run LibreHardwareMonitor before starting PyMonitor
3. Ensure "Run as Administrator" is enabled for LibreHardwareMonitor

### Linux

1. Install Python 3.8 or later and required packages:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-pyqt6 lm-sensors
   ```
2. Clone or download this repository
3. Open a terminal in the project directory
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python desktop_widget.pyw`

## Usage

### Widget Controls

- **Drag**: Click and drag to move the widget
- **Double-click**: Open settings dialog
- **System Tray**: Right-click the system tray icon for additional options:
  - Show/Hide Widget
  - Settings
  - Show/Hide Console
  - Exit

### Settings

- **Appearance**: Customize font, colors, opacity, and position
- **Display**: Choose which hardware components and metrics to show
- **Layout**: Select vertical, horizontal, or grid layout
- **Metrics Order**: Arrange the order of displayed metrics
- Use the **Metrics Order** tab to reorder metrics within each category

## Configuration

All settings are saved automatically and persisted between sessions. The configuration includes:

- Appearance settings (font, colors, opacity)
- Position and monitor selection
- Displayed metrics selection
- Layout preferences
- Custom metrics ordering

## Dependencies

- PyQt6: For the GUI components
- psutil: For cross-platform system metrics
- pynvml/py3nvml: For NVIDIA GPU metrics
- wmi: For Windows Management Instrumentation (Windows only)
- qtawesome: For icons in the user interface

## License

This project is licensed under the MIT License - see the LICENSE file for details.
