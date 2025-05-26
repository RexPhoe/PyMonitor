import psutil
import platform
import time
import subprocess
import re
from typing import Dict, Optional
from .logging_utils import get_logger

# Try to import wmi for Windows-specific LHM access (only on Windows)
wmi = None
if platform.system() == "Windows":
    try:
        import wmi
    except ImportError:
        logger.info("Python WMI module not found. Some Windows-specific features may be unavailable.")

# Configure logger
logger = get_logger(__name__)

class RAMMetricsCollector:
    """A class to handle RAM metrics collection across different platforms"""

    def __init__(self):
        self.platform_system = platform.system()

    _lhm_ram_temp_cache = None
    _lhm_ram_cache_time = 0
    _lhm_ram_cache_ttl = 5 
    
    def _get_lhm_ram_metrics(self) -> Optional[Dict[str, float]]:
        """Get RAM metrics from LibreHardwareMonitor through WMI"""
        if not wmi or self.platform_system != "Windows": # WMI not available or not on Windows
            logger.debug("LHM WMI not available for RAM metrics.")
            return None
        
        # Verify cache validity
        current_time = time.time()
        if (RAMMetricsCollector._lhm_ram_temp_cache is not None and 
            current_time - RAMMetricsCollector._lhm_ram_cache_time < RAMMetricsCollector._lhm_ram_cache_ttl):
            return {"ram_temperature": RAMMetricsCollector._lhm_ram_temp_cache}
        
        ram_temp = None
        
        try:
            # Configure WMI timeout to avoid UI blocking
            lhm_wmi_connection = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
            
            wql = "SELECT Value FROM Sensor WHERE SensorType='Temperature' AND Name LIKE '%RAM%' OR Name LIKE '%Memory%'"
            results = lhm_wmi_connection.query(wql)
            
            if results and len(results) > 0:
                for result in results:
                    if hasattr(result, 'Value') and result.Value is not None:
                        ram_temp = result.Value
                        break
            
            # Update cache
            RAMMetricsCollector._lhm_ram_temp_cache = ram_temp
            RAMMetricsCollector._lhm_ram_cache_time = current_time
                    
            return {"ram_temperature": ram_temp} if ram_temp is not None else None
            
        except Exception as e:
            logger.error(f"Error getting RAM metrics from LHM: {e}")
            return None
            
    def _get_macos_ram_metrics(self) -> Optional[Dict[str, float]]:
        """Get RAM metrics from macOS"""
        # Unfortunately, there's no reliable way to get RAM temperature in macOS without root privileges
        # Instead of trying to use sudo, we'll just return None for RAM temperature
        # The application will still work, just without this specific metric
        logger.debug("RAM temperature not available on macOS without root privileges")
        return None
        
    def _get_linux_ram_metrics(self) -> Optional[Dict[str, float]]:
        """Get RAM metrics from Linux"""
        ram_temp = None
        
        # Try to get RAM temperature using sensors command
        try:
            output = subprocess.check_output(["sensors"], timeout=2).decode()
            # Look for patterns like "DIMM0: +45.0°C" or "SODIMM: +45.0°C"
            temp_match = re.search(r'(DIMM|SODIMM)\d*:\s+\+(\d+\.\d+)°C', output)
            if temp_match:
                ram_temp = float(temp_match.group(2))
                return {"ram_temperature": ram_temp}
        except FileNotFoundError:
            logger.debug("sensors command not found. Install lm-sensors for RAM temperature monitoring.")
        except Exception as e:
            logger.debug(f"Could not get RAM temperature on Linux: {e}")
            
        return None

    def get_metrics(self) -> Dict[str, Optional[float]]:
        """Get RAM metrics

        Returns:
            Dict with the following keys:
            - total: Total RAM in GB
            - used: Used RAM in GB
            - available: Available RAM in GB
            - percent: RAM usage percentage
            - ram_temperature: RAM temperature in Celsius (if available)
        """
        metrics = {
            "total": None, 
            "used": None, 
            "available": None, 
            "percent": None,
            "ram_temperature": None # Initialize temperature metric
        }
        
        try:
            memory = psutil.virtual_memory()
            metrics.update({
                "total": memory.total / (1024**3),  # Convert to GB
                "used": memory.used / (1024**3),
                "available": memory.available / (1024**3),
                "percent": memory.percent,
            })
        except Exception as e:
            logger.error(f"Error getting psutil RAM metrics: {e}")
            # metrics will retain None for these keys

        # Platform-specific metric collection for RAM temperature
        if self.platform_system == "Windows":
            lhm_ram_metrics = self._get_lhm_ram_metrics()
            if lhm_ram_metrics and lhm_ram_metrics.get("ram_temperature") is not None:
                metrics["ram_temperature"] = lhm_ram_metrics["ram_temperature"]
        elif self.platform_system == "Darwin":  # macOS
            macos_ram_metrics = self._get_macos_ram_metrics()
            if macos_ram_metrics and macos_ram_metrics.get("ram_temperature") is not None:
                metrics["ram_temperature"] = macos_ram_metrics["ram_temperature"]
        elif self.platform_system == "Linux":
            linux_ram_metrics = self._get_linux_ram_metrics()
            if linux_ram_metrics and linux_ram_metrics.get("ram_temperature") is not None:
                metrics["ram_temperature"] = linux_ram_metrics["ram_temperature"]

        logger.debug(f"RAM Metrics: {metrics}")
        return metrics
