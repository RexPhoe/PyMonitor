# PyMonitor

A lightweight desktop widget for real-time hardware monitoring, displaying CPU, GPU, RAM, and network metrics in a customizable, always-on-top interface.

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

### Prerequisites

- Python 3.8 or higher
- PyQt6
- Required Python packages (see requirements.txt)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/username/PyMonitor.git
   cd PyMonitor
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run PyMonitor:
   ```
   python desktop_widget.py
   ```

### Windows-specific Setup

For optimal metrics collection on Windows:

1. Download and install [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. Run LibreHardwareMonitor before starting PyMonitor
3. Ensure "Run as Administrator" is enabled for LibreHardwareMonitor

## Usage

- **Right-click** on the widget to access the context menu
- **Drag** the widget to reposition it
- Open **Settings** to customize appearance and displayed metrics
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
