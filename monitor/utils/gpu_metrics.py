import platform
import subprocess
import re
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

# WMI for LibreHardwareMonitor (Windows only)
LHM_WMI_AVAILABLE = False
WMIService = None
if platform.system() == "Windows":
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

    def _get_macos_gpu_metrics(self) -> Dict[str, Optional[float]]:
        """Get GPU metrics on macOS"""
        metrics = {
            "core_frequency": None,
            "core_usage": None,
            "core_temperature": None,
            "memory_frequency": None,
            "vram_usage_percent": None,
            "memory_temperature": None,
            "hotspot_temperature": None,
            "fan_speed": None,
            "vram_used_gb": None,
            "vram_total_gb": None
        }
        
        # First try to get GPU name and model
        try:
            output = subprocess.check_output(["system_profiler", "SPDisplaysDataType"]).decode()
            # Parse the output to get GPU info
            # Look for lines like "Chipset Model: Intel UHD Graphics 630"
            gpu_model_match = re.search(r'Chipset Model:\s*(.+)', output)
            if gpu_model_match:
                gpu_model = gpu_model_match.group(1).strip()
                logger.info(f"Detected GPU: {gpu_model}")
                
            # Check for VRAM info
            vram_match = re.search(r'VRAM \(Total\):\s*(\d+)\s*([MG]B)', output)
            if vram_match:
                vram_amount = float(vram_match.group(1))
                vram_unit = vram_match.group(2)
                
                # Convert to GB if needed
                if vram_unit == "MB":
                    metrics["vram_total_gb"] = vram_amount / 1024
                else:  # GB
                    metrics["vram_total_gb"] = vram_amount
                    
            # Try to get GPU usage using ioreg if it's an AMD or NVIDIA GPU
            if gpu_model and ("AMD" in gpu_model or "Radeon" in gpu_model or "NVIDIA" in gpu_model or "GeForce" in gpu_model):
                try:
                    # This might not work on all Macs
                    ioreg_output = subprocess.check_output(["ioreg", "-l"]).decode()
                    # Look for GPU utilization percentage
                    util_match = re.search(r'"GPU Activity"\s*=\s*(\d+)', ioreg_output)
                    if util_match:
                        metrics["core_usage"] = float(util_match.group(1))
                except Exception as e:
                    logger.debug(f"Error getting GPU usage from ioreg: {e}")
                    
        except Exception as e:
            logger.error(f"Error getting macOS GPU info: {e}")
        
        return metrics
    
    def _get_linux_gpu_metrics(self) -> Dict[str, Optional[float]]:
        """Get GPU metrics on Linux"""
        metrics = {
            "core_frequency": None,
            "core_usage": None,
            "core_temperature": None,
            "memory_frequency": None,
            "vram_usage_percent": None,
            "memory_temperature": None,
            "hotspot_temperature": None,
            "fan_speed": None,
            "vram_used_gb": None,
            "vram_total_gb": None
        }
        
        # Try to detect GPU using lspci
        try:
            output = subprocess.check_output(["lspci", "-v"]).decode()
            # Check if NVIDIA is present
            if "NVIDIA" in output:
                logger.info("NVIDIA GPU detected in Linux")
                # If NVIDIA is present and pynvml is available, metrics should already be collected
                # by _get_nvidia_metrics() so we don't need to do anything here
                pass
                
            # Check if AMD is present
            elif "AMD" in output or "Radeon" in output:
                logger.info("AMD GPU detected in Linux")
                # Try to get AMD GPU info using rocm-smi
                try:
                    rocm_output = subprocess.check_output(["rocm-smi"], timeout=2).decode()
                    # Parse rocm-smi output
                    temp_match = re.search(r'(\d+)C\s+\|\s+Temperature', rocm_output)
                    if temp_match:
                        metrics["core_temperature"] = float(temp_match.group(1))
                        
                    # Try to get GPU usage
                    usage_match = re.search(r'(\d+)%\s+\|\s+GPU use', rocm_output)
                    if usage_match:
                        metrics["core_usage"] = float(usage_match.group(1))
                        
                    # Try to get VRAM info
                    vram_match = re.search(r'(\d+)/(\d+)\s*MB\s+\|\s+VRAM', rocm_output)
                    if vram_match:
                        used_mb = float(vram_match.group(1))
                        total_mb = float(vram_match.group(2))
                        metrics["vram_used_gb"] = used_mb / 1024
                        metrics["vram_total_gb"] = total_mb / 1024
                        metrics["vram_usage_percent"] = (used_mb / total_mb) * 100 if total_mb > 0 else None
                except FileNotFoundError:
                    logger.debug("rocm-smi not found. Install ROCm for AMD GPU monitoring.")
                except Exception as e:
                    logger.debug(f"Error getting AMD GPU metrics: {e}")
                    
                # If rocm-smi failed, try using sensors for temperature
                if metrics["core_temperature"] is None:
                    try:
                        sensors_output = subprocess.check_output(["sensors"], timeout=2).decode()
                        # Look for patterns like "edge: +45.0°C"
                        temp_match = re.search(r'edge:\s+\+(\d+\.\d+)°C', sensors_output)
                        if temp_match:
                            metrics["core_temperature"] = float(temp_match.group(1))
                    except Exception as e:
                        logger.debug(f"Error getting GPU temperature from sensors: {e}")
                
            # Check if Intel is present
            elif "Intel" in output and "Graphics" in output:
                logger.info("Intel GPU detected in Linux")
                # Try to get Intel GPU info (without requiring sudo)
                try:
                    # Try to get basic GPU info without requiring sudo
                    with open('/sys/class/drm/card0/device/gpu_busy_percent', 'r') as f:
                        gpu_busy = f.read().strip()
                        if gpu_busy.isdigit():
                            metrics["core_usage"] = float(gpu_busy)
                except FileNotFoundError:
                    # Alternative approach: try glxinfo
                    try:
                        glx_output = subprocess.check_output(["glxinfo"], timeout=2).decode()
                        # Just check if rendering is available
                        if "direct rendering: Yes" in glx_output:
                            logger.debug("Intel GPU detected with OpenGL support")
                    except FileNotFoundError:
                        logger.debug("No GPU monitoring tools found for Intel GPU on Linux")
                    except Exception as e:
                        logger.debug(f"Error getting Intel GPU metrics: {e}")
                except Exception as e:
                    logger.debug(f"Error getting Intel GPU metrics: {e}")
        
        except FileNotFoundError:
            logger.debug("lspci command not found. Install pciutils for hardware detection.")
        except Exception as e:
            logger.error(f"Error detecting GPU in Linux: {e}")
        
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
        # Try NVIDIA metrics first (works on all platforms if NVIDIA GPU and drivers are present)
        metrics = self._get_nvidia_metrics()

        # Platform-specific metric collection
        if self.platform == "Windows":
            # If NVIDIA metrics are incomplete, try to augment with LibreHardwareMonitor data
            # LHM could also provide data for AMD or Intel iGPUs
            lhm_gpu_metrics = self._get_lhm_metrics()
            for key, value in lhm_gpu_metrics.items():
                if metrics.get(key) is None and value is not None: # Fill gaps
                    metrics[key] = value
                elif key not in metrics and value is not None: # Add new metrics if LHM has them
                     metrics[key] = value
        elif self.platform == "Darwin":  # macOS
            macos_metrics = self._get_macos_gpu_metrics()
            for key, value in macos_metrics.items():
                if metrics.get(key) is None and value is not None: # Fill gaps
                    metrics[key] = value
                elif key not in metrics and value is not None: # Add new metrics if available
                     metrics[key] = value
        elif self.platform == "Linux":
            linux_metrics = self._get_linux_gpu_metrics()
            for key, value in linux_metrics.items():
                if metrics.get(key) is None and value is not None: # Fill gaps
                    metrics[key] = value
                elif key not in metrics and value is not None: # Add new metrics if available
                     metrics[key] = value
                     
        return metrics
