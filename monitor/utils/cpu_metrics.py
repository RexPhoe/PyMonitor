import psutil
import platform
import wmi
from typing import Dict, Optional, Union
import os
import ctypes
from ctypes import byref, c_ulonglong
from .logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)


class CPUMetricsCollector:
    """A class to handle CPU metrics collection across different platforms"""

    def __init__(self):
        """Initialize the metrics collector based on the platform"""
        self.platform = platform.system()
        # self.wmi_connection for LHM is removed, will be created on-demand
        self.base_frequency = self._get_base_frequency()
        # self.lhm_available is removed, success will be determined on-demand

        if self.platform == "Windows":
            # Initialize WMI connection for basic Windows metrics (non-LHM)
            try:
                self.basic_wmi = wmi.WMI() # For MSAcpi_ThermalZoneTemperature
            except Exception as e:
                logger.error(f"Failed to initialize basic WMI for MSAcpi: {e}")
                self.basic_wmi = None

    def _get_base_frequency(self) -> float:
        """Get CPU base frequency in MHz"""
        try:
            if platform.system() == "Windows":
                # Try getting from WMI first
                w = wmi.WMI()
                cpu_info = w.Win32_Processor()[0]
                return float(cpu_info.MaxClockSpeed)
            return None
        except:
            return None

    def _get_windows_basic_metrics(self) -> Dict[str, Optional[float]]:
        """Get basic CPU metrics on Windows without LibreHardwareMonitor"""
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
        }

        try:
            # Get CPU usage from psutil with a very short interval
            metrics["usage"] = psutil.cpu_percent(interval=0.1)

            # Get CPU frequency
            freq = psutil.cpu_freq()
            if freq:
                metrics["frequency"] = freq.current
            elif self.base_frequency:
                metrics["frequency"] = self.base_frequency

            # Try to get temperature using MSAcpi if LHM didn't provide it or LHM is unavailable
            if metrics["temperature"] is None and self.basic_wmi:
                try:
                    for tmp in self.basic_wmi.MSAcpi_ThermalZoneTemperature():
                        # Convert from deciKelvin to Celsius
                        temp_celsius = (tmp.CurrentTemperature / 10) - 273.15
                        if (
                            metrics["temperature"] is None
                            or temp_celsius > metrics["temperature"]
                        ):
                            metrics["temperature"] = temp_celsius
                except:
                    pass

        except Exception as e:
            logger.error(f"Error getting basic Windows metrics: {e}")

        return metrics

    def _get_libre_hardware_metrics(self) -> Dict[str, Optional[float]]:
        """Get CPU metrics using LibreHardwareMonitor on Windows"""
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
        }

        lhm_wmi_connection = None
        try:
            lhm_wmi_connection = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
        except Exception as e:
            # Log only once or based on a timer if this becomes too noisy
            # For now, logging each time to see if connection itself is the issue
            logger.debug(f"Failed to connect to LibreHardwareMonitor WMI: {e}")
            return metrics # Return empty metrics, basic_metrics might fill some

        try:
            sensors = lhm_wmi_connection.Sensor()
            for sensor in sensors:
                if not hasattr(sensor, "Value"):
                    continue

                # Prioritize specific sensor names if available, fallback to generic 'CPU'
                if sensor.SensorType == "Temperature":
                    if "CPU Package" in sensor.Name or "Core (Tctl/Tdie)" in sensor.Name:
                        metrics["temperature"] = sensor.Value
                        break # Found a primary temperature sensor
                    elif "CPU" in sensor.Name and metrics["temperature"] is None: # Fallback
                        metrics["temperature"] = sensor.Value
                
                elif sensor.SensorType == "Voltage":
                    if "CPU Core" in sensor.Name or "CPU VCORE" in sensor.Name:
                         metrics["voltage"] = sensor.Value
                    elif "CPU" in sensor.Name and metrics["voltage"] is None:
                         metrics["voltage"] = sensor.Value

                elif sensor.SensorType == "Clock":
                    if "CPU Core #1" == sensor.Name: # Often more accurate than generic CPU clock
                        metrics["frequency"] = sensor.Value
                    elif "CPU" in sensor.Name and metrics["frequency"] is None:
                        metrics["frequency"] = sensor.Value
                
                elif sensor.SensorType == "Load" and "CPU Total" in sensor.Name:
                    metrics["usage"] = sensor.Value

        except Exception as e:
            logger.error(f"Error querying LibreHardwareMonitor sensors: {e}")
            # Do not set self.lhm_available = False, as we try fresh connection next time

        return metrics

    def get_metrics(self) -> Dict[str, Optional[float]]:
        """Get CPU metrics for the current platform

        Returns:
            Dict with the following keys (values may be None if unavailable):
            - frequency: CPU frequency in MHz
            - usage: CPU usage percentage
            - temperature: CPU temperature in Celsius
            - voltage: CPU voltage in Volts
        """
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
        }

        if self.platform == "Windows":
            # Try LibreHardwareMonitor first
            lhm_metrics = self._get_libre_hardware_metrics()
            # Update metrics, LHM values take precedence if not None
            for key, value in lhm_metrics.items():
                if value is not None:
                    metrics[key] = value

            # Get basic metrics for any missing values
            basic_metrics = self._get_windows_basic_metrics()
            for key, value in basic_metrics.items():
                if metrics[key] is None and value is not None:
                    metrics[key] = value

        else:
            # Fallback to basic metrics for other platforms
            metrics["usage"] = psutil.cpu_percent(interval=0.1)

        return metrics
