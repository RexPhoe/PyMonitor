import psutil
import platform
from typing import Dict, Optional, Union
import os
import ctypes
from ctypes import byref, c_ulonglong
import subprocess
import re
from .logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)

# Import wmi only on Windows
wmi = None
if platform.system() == "Windows":
    try:
        import wmi
    except ImportError:
        logger.warning("WMI module not found. Some Windows-specific features may be unavailable.")


class CPUMetricsCollector:
    """A class to handle CPU metrics collection across different platforms"""

    def __init__(self):
        """Initialize the metrics collector based on the platform"""
        self.platform = platform.system()
        # self.wmi_connection for LHM is removed, will be created on-demand
        self.base_frequency = self._get_base_frequency()
        # self.lhm_available is removed, success will be determined on-demand
        self.basic_wmi = None

        if self.platform == "Windows" and wmi:
            # Initialize WMI connection for basic Windows metrics (non-LHM)
            try:
                self.basic_wmi = wmi.WMI() # For MSAcpi_ThermalZoneTemperature
            except Exception as e:
                logger.error(f"Failed to initialize basic WMI for MSAcpi: {e}")
                self.basic_wmi = None

    def _get_base_frequency(self) -> float:
        """Get CPU base frequency in MHz"""
        try:
            if platform.system() == "Windows" and wmi:
                # Try getting from WMI first
                w = wmi.WMI()
                cpu_info = w.Win32_Processor()[0]
                return float(cpu_info.MaxClockSpeed)
            elif platform.system() == "Darwin":  # macOS
                try:
                    # First try the traditional approach for Intel Macs
                    try:
                        output = subprocess.check_output(["sysctl", "-n", "hw.cpufrequency"]).decode().strip()
                        return float(output) / 1000000  # Convert Hz to MHz
                    except subprocess.CalledProcessError:
                        # This might be an Apple Silicon (M1/M2/M3) processor where hw.cpufrequency isn't available
                        # For Apple Silicon, we can't reliably get the frequency this way
                        # We'll have to rely on the reported nominal frequency from Apple's specs
                        # or use a different metric in _get_macos_metrics
                        logger.debug("hw.cpufrequency not available, might be Apple Silicon processor")
                        return None
                except Exception as e:
                    logger.error(f"Error getting CPU frequency on macOS: {e}")
                    return None
            elif platform.system() == "Linux":
                try:
                    # Try reading from /proc/cpuinfo
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if "cpu MHz" in line:
                                return float(line.split(":")[1].strip())
                            # Some CPUs report frequency in GHz
                            elif "cpu GHz" in line:
                                return float(line.split(":")[1].strip()) * 1000
                    return None
                except Exception as e:
                    logger.error(f"Error getting CPU frequency on Linux: {e}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error in _get_base_frequency: {e}")
            return None

    def _get_windows_basic_metrics(self) -> Dict[str, Optional[float]]:
        """Get basic CPU metrics on Windows without LibreHardwareMonitor"""
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
        }

        if self.platform != "Windows":
            return metrics

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

        if not (self.platform == "Windows" and wmi):
            return metrics

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

    def _get_macos_metrics(self) -> Dict[str, Optional[float]]:
        """Get CPU metrics on macOS"""
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
            "cpu_model": None,  # Added to store CPU model information
        }
        
        try:
            # Get CPU usage from psutil
            metrics["usage"] = psutil.cpu_percent(interval=0.1)
            
            # Get CPU model information for Apple Silicon processors
            try:
                # Get CPU model information
                output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
                metrics["cpu_model"] = output
            except subprocess.CalledProcessError:
                # This might be Apple Silicon where machdep.cpu.brand_string isn't available
                try:
                    # Use system_profiler to get more detailed hardware info
                    hw_output = subprocess.check_output(["system_profiler", "SPHardwareDataType"]).decode()
                    # Look for Chip or Processor information
                    chip_match = re.search(r'Chip:\s*(.+)', hw_output) or re.search(r'Processor Name:\s*(.+)', hw_output)
                    if chip_match:
                        metrics["cpu_model"] = chip_match.group(1).strip()
                        
                        # For Apple Silicon, try to estimate frequency based on the model
                        # These are approximations based on official Apple specs
                        if "M1" in metrics["cpu_model"]:
                            metrics["frequency"] = 3200.0  # M1 has up to 3.2 GHz
                        elif "M2" in metrics["cpu_model"]:
                            metrics["frequency"] = 3500.0  # M2 has up to 3.5 GHz
                        elif "M3" in metrics["cpu_model"]:
                            metrics["frequency"] = 4000.0  # M3 has up to 4.0 GHz
                except Exception as e:
                    logger.debug(f"Could not determine CPU model: {e}")
            
            # Get CPU frequency if not already determined from the model
            if metrics["frequency"] is None:
                freq = psutil.cpu_freq()
                if freq:
                    metrics["frequency"] = freq.current
                elif self.base_frequency:
                    metrics["frequency"] = self.base_frequency
                
            # Try multiple methods to get temperature on macOS
            try:
                    
                # Method 1: First try the IOKit approach - works well on Apple Silicon
                try:
                    output = subprocess.check_output(["ioreg", "-r", "-c", "IOPlatformDevice"], timeout=2).decode()
                    # Look for CPU die temperature - this is often available on Apple Silicon
                    temp_match = re.search(r'"CPU die temperature"\s*=\s*(\d+)', output)
                    if temp_match:
                        # The value is usually in 1/10 degrees Celsius
                        metrics["temperature"] = float(temp_match.group(1)) / 10.0
                        logger.debug(f"CPU Temperature from IOKit: {metrics['temperature']}°C")
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
                
                # Method 2: Try using the built-in thermal management
                if metrics["temperature"] is None:
                    try:
                        output = subprocess.check_output(["pmset", "-g", "therm"], timeout=2).decode()
                        # Look for CPU temperature if available
                        temp_match = re.search(r'CPU_Thermal_Level=(\d+)', output)
                        if temp_match:
                            thermal_level = int(temp_match.group(1))
                            # Convert thermal level to approximate temperature
                            # Level 0 = Normal (~45-60°C), Level 1 = Medium (~65-75°C), Level 2 = High (80+°C)
                            if thermal_level == 0:
                                metrics["temperature"] = 50.0
                            elif thermal_level == 1:
                                metrics["temperature"] = 70.0
                            elif thermal_level >= 2:
                                metrics["temperature"] = 85.0
                            logger.debug(f"CPU Temperature estimated from thermal level: {metrics['temperature']}°C")
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                
                # Method 3: As fallback, use system_profiler for thermal pressure (less accurate)
                if metrics["temperature"] is None:
                    output = subprocess.check_output(["system_profiler", "SPPowerDataType"], timeout=2).decode()
                    # Look for thermal pressure or other indicators
                    thermal_match = re.search(r'Thermal Pressure:\s*(\w+)', output)
                    if thermal_match:
                        thermal_pressure = thermal_match.group(1)
                        logger.debug(f"CPU Thermal Pressure: {thermal_pressure}")
                        # We can't get exact temperature, but we can estimate based on thermal pressure
                        # This is just an approximation
                        if thermal_pressure == "Nominal":
                            metrics["temperature"] = 45.0  # Estimate for nominal pressure
                        elif thermal_pressure == "Moderate":
                            metrics["temperature"] = 65.0  # Estimate for moderate pressure
                        elif thermal_pressure == "Heavy":
                            metrics["temperature"] = 80.0  # Estimate for heavy pressure
                        elif thermal_pressure == "Critical":
                            metrics["temperature"] = 90.0  # Estimate for critical pressure
                        logger.debug(f"CPU Temperature estimated from Thermal Pressure: {metrics['temperature']}°C")
                        
                # Method 4: Try using the sysctl hw.sensors if available (some Macs)
                if metrics["temperature"] is None:
                    try:
                        output = subprocess.check_output(["sysctl", "hw.sensors"], timeout=2).decode()
                        # Look for CPU temperature sensors
                        temp_match = re.search(r'hw\.sensors\.cpu0\.temp0=(\d+\.\d+)', output)
                        if temp_match:
                            metrics["temperature"] = float(temp_match.group(1))
                            logger.debug(f"CPU Temperature from sysctl: {metrics['temperature']}°C")
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                
                if metrics["temperature"] is None:
                    try:
                        output = subprocess.check_output(["osx-cpu-temp"], timeout=2).decode().strip()
                        # Output format: "CPU: 54.2°C"
                        temp_match = re.search(r'CPU:\s*(\d+\.\d+)°C', output)
                        if temp_match:
                            metrics["temperature"] = float(temp_match.group(1))
                            logger.debug(f"CPU Temperature from osx-cpu-temp: {metrics['temperature']}°C")
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass
                    
            except Exception as e:
                logger.debug(f"Could not get CPU thermal info on macOS: {e}")
                
        except Exception as e:
            logger.error(f"Error getting macOS CPU metrics: {e}")
            
        return metrics
        
    def _get_linux_metrics(self) -> Dict[str, Optional[float]]:
        """Get CPU metrics on Linux"""
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
        }
        
        try:
            # Get CPU usage from psutil
            metrics["usage"] = psutil.cpu_percent(interval=0.1)
            
            # Get CPU frequency
            freq = psutil.cpu_freq()
            if freq:
                metrics["frequency"] = freq.current
            elif self.base_frequency:
                metrics["frequency"] = self.base_frequency
                
            # Try to get temperature using sensors command
            try:
                output = subprocess.check_output(["sensors"], timeout=2).decode()
                # Look for patterns like "Package id 0:  +45.0°C" or "Core 0:        +45.0°C"
                # First try to find Package temperature
                package_match = re.search(r'Package id \d+:\s+\+(\d+\.\d+)°C', output)
                if package_match:
                    metrics["temperature"] = float(package_match.group(1))
                else:
                    # If no Package temp, look for the first Core temp
                    core_match = re.search(r'Core \d+:\s+\+(\d+\.\d+)°C', output)
                    if core_match:
                        metrics["temperature"] = float(core_match.group(1))
            except FileNotFoundError:
                logger.debug("sensors command not found. Install lm-sensors for CPU temperature monitoring.")
            except Exception as e:
                logger.debug(f"Could not get CPU temperature on Linux: {e}")
                
        except Exception as e:
            logger.error(f"Error getting Linux CPU metrics: {e}")
            
        return metrics

    def get_metrics(self) -> Dict[str, Optional[Union[float, str]]]:
        """Get CPU metrics for the current platform

        Returns:
            Dict with the following keys (values may be None if unavailable):
            - frequency: CPU frequency in MHz
            - usage: CPU usage percentage
            - temperature: CPU temperature in Celsius
            - voltage: CPU voltage in Volts
            - cpu_model: CPU model string (only available on some platforms, particularly macOS)
        """
        metrics = {
            "frequency": None,
            "usage": None,
            "temperature": None,
            "voltage": None,
            "cpu_model": None,
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

        elif self.platform == "Darwin":  # macOS
            macos_metrics = self._get_macos_metrics()
            for key, value in macos_metrics.items():
                if value is not None:
                    metrics[key] = value
                    
        elif self.platform == "Linux":
            linux_metrics = self._get_linux_metrics()
            for key, value in linux_metrics.items():
                if value is not None:
                    metrics[key] = value
        else:
            # Fallback to basic metrics for other platforms
            metrics["usage"] = psutil.cpu_percent(interval=0.1)

        return metrics
