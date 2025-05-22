import platform
from typing import Dict, Optional
from .logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize NVIDIA support
NVIDIA_AVAILABLE = False
try:
    import pynvml

    pynvml.nvmlInit()
    NVIDIA_AVAILABLE = True
    logger.info("NVIDIA GPU monitoring initialized successfully")
except:
    # Don't log error here, NVIDIA might not be present
    pass

# LHM_AVAILABLE global flag is removed, connection will be attempted on-demand

# WMI for LibreHardwareMonitor
LHM_WMI_AVAILABLE = False
WMIService = None
try:
    import wmi
    WMIService = wmi # Assign to a consistent name for use later
    LHM_WMI_AVAILABLE = True
except ImportError:
    logger.info("Python WMI module not found. LibreHardwareMonitor metrics may be unavailable for GPU.")
except Exception as e:
    logger.error(f"Error initializing WMI for LHM: {e}")

class GPUMetricsCollector:
    """A class to handle GPU metrics collection"""

    def __init__(self):
        """Initialize the GPU metrics collector"""
        global NVIDIA_AVAILABLE # Declare global at the beginning of the scope where it might be modified
        self.platform = platform.system()
        # self.wmi_connection for LHM is removed, will be created on-demand
        self.handle = None # For NVIDIA

        if NVIDIA_AVAILABLE: # Check the global status first
            try:
                # pynvml.nvmlInit() is already called at module level
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                # logger.info("NVIDIA GPU detected and initialized") # Logged by pynvml init already
            except pynvml.NVMLError_DriverNotLoaded:
                logger.warning("NVIDIA driver not loaded. NVML functions unavailable.")
                NVIDIA_AVAILABLE = False # Modify the global
            except pynvml.NVMLError_NoPermission:
                logger.warning("No permission to communicate with NVIDIA driver. NVML functions unavailable.")
                NVIDIA_AVAILABLE = False # Modify the global
            except Exception as e:
                logger.error(f"Failed to get NVIDIA GPU handle: {e}")
                NVIDIA_AVAILABLE = False # Modify the global

    def _get_nvidia_metrics(self) -> Dict[str, Optional[float]]:
        """Get metrics from NVIDIA GPU"""
        metrics = {
            "core_frequency": None,
            "core_usage": None,
            "core_temperature": None,
            "memory_frequency": None,
            "vram_usage_percent": None, # Standardized key
            "memory_temperature": None,
            "hotspot_temperature": None,
            "fan_speed": None,
            "vram_used_gb": None, # For NVIDIA, calculated
            "vram_total_gb": None # For NVIDIA, calculated
        }

        if not self.handle:
            return metrics

        try:
            # Get core metrics
            temp = pynvml.nvmlDeviceGetTemperature(
                self.handle, pynvml.NVML_TEMPERATURE_GPU
            )
            metrics["core_temperature"] = float(temp)

            utilization = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            metrics["core_usage"] = float(utilization.gpu)

            clock = pynvml.nvmlDeviceGetClockInfo(
                self.handle, pynvml.NVML_CLOCK_GRAPHICS
            )
            metrics["core_frequency"] = float(clock)

            # Get memory metrics
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            metrics["vram_usage_percent"] = (mem_info.used / mem_info.total) * 100
            metrics["vram_used_gb"] = mem_info.used / (1024**3)
            metrics["vram_total_gb"] = mem_info.total / (1024**3)

            mem_clock = pynvml.nvmlDeviceGetClockInfo(
                self.handle, pynvml.NVML_CLOCK_MEM
            )
            metrics["memory_frequency"] = float(mem_clock)

            # Try to get memory temperature and hotspot (not all GPUs support this)
            try:
                mem_temp = pynvml.nvmlDeviceGetTemperature(
                    self.handle, pynvml.NVML_TEMPERATURE_MEMORY
                )
                metrics["memory_temperature"] = float(mem_temp)
            except:
                pass

            try:
                hotspot = pynvml.nvmlDeviceGetTemperature(
                    self.handle, pynvml.NVML_TEMPERATURE_HOTSPOT
                )
                metrics["hotspot_temperature"] = float(hotspot)
            except:
                pass

            try:
                fan_speed_val = pynvml.nvmlDeviceGetFanSpeed(self.handle) # Default is first fan
                metrics["fan_speed"] = float(fan_speed_val)
            except pynvml.NVMLError_NotSupported:
                metrics["fan_speed"] = None # Not supported on this GPU
            except Exception:
                metrics["fan_speed"] = None # Other error

        except Exception as e:
            logger.error(f"Error getting NVIDIA metrics: {e}")

        return metrics

    def _get_lhm_metrics(self) -> Dict[str, Optional[float]]:
        """Get metrics using LibreHardwareMonitor on Windows"""
        if not LHM_WMI_AVAILABLE or WMIService is None:
            logger.debug("LHM WMI not available for GPU metrics.")
            return {
                "core_frequency": None,
                "core_usage": None,
                "core_temperature": None,
                "memory_frequency": None,
                "vram_usage_percent": None, 
                "memory_temperature": None,
                "hotspot_temperature": None,
                "fan_speed": None
            }
        metrics = {
            "core_frequency": None,
            "core_usage": None,
            "core_temperature": None,
            "memory_frequency": None,
            "vram_usage_percent": None, # Standardized key
            "memory_temperature": None,
            "hotspot_temperature": None,
            "fan_speed": None
            # LHM does not typically provide VRAM total/used in GB directly, relies on percentage.
        }

        lhm_wmi_connection = None
        try:
            lhm_wmi_connection = WMIService.WMI(namespace=r"root\LibreHardwareMonitor") # Use the imported WMIService
        except Exception as e:
            logger.debug(f"Failed to connect to LHM WMI for GPU metrics: {e}")
            return metrics # Return initialized metrics dict (all None)

        try:
            sensors = lhm_wmi_connection.Sensor()
            if not sensors:
                logger.debug("LHM WMI connected for GPU but no sensors found.")
                return metrics

            # Identify the correct GPU if multiple are present (e.g. by checking name against NVIDIA if possible)
            # For simplicity now, we assume LHM sensors for 'GPU' are for the primary one.
            # More robust would be to match sensor.Identifier with a known GPU path if LHM provides it.

            gpu_sensor_keywords = ["GPU", "NVIDIA", "AMD", "RADEON", "INTEL GRAPHICS"]
            gpu_instance_id_paths = ["/nvidiagpu/", "/amdgpu/", "/intelgpu/"]

            for sensor in sensors:
                sensor_name_upper = "" # Initialize here
                sensor_identifier_lower = "" # Initialize here
                s_type = "" # Initialize here

                if not hasattr(sensor, 'Value') or sensor.Value is None: # Skip sensors without a value
                    continue
                
                if hasattr(sensor, 'SensorType') and sensor.SensorType:
                    s_type = sensor.SensorType
                else:
                    continue # Skip if no SensorType

                is_relevant_gpu_sensor = False
                
                if hasattr(sensor, 'Identifier') and sensor.Identifier:
                    sensor_identifier_lower = sensor.Identifier.lower()
                    for path_part in gpu_instance_id_paths:
                        if path_part in sensor_identifier_lower:
                            is_relevant_gpu_sensor = True
                            break
                
                if hasattr(sensor, 'Name') and sensor.Name:
                    sensor_name_upper = sensor.Name.upper()
                    if not is_relevant_gpu_sensor: # Check name if identifier didn't match or wasn't present
                        for keyword in gpu_sensor_keywords:
                            if keyword in sensor_name_upper:
                                is_relevant_gpu_sensor = True
                                break
                
                if not is_relevant_gpu_sensor:
                    continue

                # At this point, sensor is likely a GPU-related sensor
                # Use sensor_name_upper which is already defined, and s_type
                s_type = sensor.SensorType
                # sensor_name_upper is already sensor.Name.upper() from above

                # More specific matching for LHM GPU sensors
                if s_type == "Temperature":
                    if "GPU CORE" in sensor_name_upper and metrics["core_temperature"] is None:
                        metrics["core_temperature"] = sensor.Value
                    elif "GPU MEMORY" in sensor_name_upper and metrics["memory_temperature"] is None:
                        metrics["memory_temperature"] = sensor.Value
                    elif "GPU HOT SPOT" in sensor_name_upper and metrics["hotspot_temperature"] is None:
                        metrics["hotspot_temperature"] = sensor.Value
                elif s_type == "Load":
                    if "GPU CORE" in sensor_name_upper and metrics["core_usage"] is None:
                        metrics["core_usage"] = sensor.Value
                    elif "GPU MEMORY CONTROLLER" in sensor_name_upper and metrics["vram_usage_percent"] is None: # LHM often reports this for VRAM usage usage
                        metrics["vram_usage_percent"] = sensor.Value
                    elif "GPU D3D 3D" in sensor_name_upper and metrics["core_usage"] is None: # Alternative for core usage
                        metrics["core_usage"] = sensor.Value
                elif s_type == "Clock":
                    if "GPU CORE" in sensor_name_upper and metrics["core_frequency"] is None:
                        metrics["core_frequency"] = sensor.Value
                    elif "GPU MEMORY" in sensor_name_upper and metrics["memory_frequency"] is None:
                        metrics["memory_frequency"] = sensor.Value
                elif s_type == "Fan":
                    if ("GPU" in sensor_name_upper or "FAN" in sensor_name_upper) and metrics["fan_speed"] is None:
                        metrics["fan_speed"] = sensor.Value
        
        except Exception as e:
            logger.error(f"Error querying LHM GPU sensors: {e}")

        return metrics

    def get_metrics(self) -> Dict[str, Optional[float]]:
        """Get GPU metrics from available sources

        Returns:
            Dict with the following keys (values may be None if unavailable):
            - core_frequency: Core clock frequency in MHz
            - core_usage: Core usage percentage
            - core_temperature: Core temperature in Celsius
            - memory_frequency: Memory clock frequency in MHz
            - vram_usage_percent: VRAM usage percentage
            - vram_used_gb: VRAM used in GB (primarily from NVIDIA)
            - vram_total_gb: Total VRAM in GB (primarily from NVIDIA)
            - memory_temperature: Memory temperature in Celsius
            - hotspot_temperature: GPU hotspot temperature in Celsius
            - fan_speed: GPU Fan speed percentage
        """
        # Try NVIDIA metrics first
        metrics = self._get_nvidia_metrics()

        # If we're on Windows, try to augment with LibreHardwareMonitor data
        # This is useful if NVIDIA pynvml isn't available/working or for non-NVIDIA cards.
        if self.platform == "Windows":
            # If NVIDIA metrics are complete, we might not need LHM for GPU, 
            # but LHM could provide data for AMD or Intel iGPUs.
            # For now, always try LHM if on Windows and see if it fills any gaps or provides primary data.
            lhm_gpu_metrics = self._get_lhm_metrics()
            for key, value in lhm_gpu_metrics.items():
                if metrics.get(key) is None and value is not None: # Fill gaps
                    metrics[key] = value
                elif key not in metrics and value is not None: # Add new metrics if LHM has them
                     metrics[key] = value
                     
        return metrics
