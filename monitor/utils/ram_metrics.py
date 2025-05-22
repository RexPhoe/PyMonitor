import psutil
import platform
import time
from typing import Dict, Optional
from .logging_utils import get_logger

# Try to import wmi for Windows-specific LHM access
try:
    import wmi
except ImportError:
    wmi = None # WMI not available on non-Windows or if not installed

# Configure logger
logger = get_logger(__name__)

class RAMMetricsCollector:
    """A class to handle RAM metrics collection across different platforms"""

    def __init__(self):
        self.platform_system = platform.system()

    # Cache para evitar llamadas repetidas a WMI que son costosas
    _lhm_ram_temp_cache = None
    _lhm_ram_cache_time = 0
    _lhm_ram_cache_ttl = 5  # segundos
    
    def _get_lhm_ram_metrics(self) -> Optional[Dict[str, float]]:
        """Get RAM metrics from LibreHardwareMonitor through WMI"""
        if not wmi: # WMI not available
            logger.debug("LHM WMI not available for RAM metrics.")
            return None
        
        # Verificar si la caché es válida
        current_time = time.time()
        if (RAMMetricsCollector._lhm_ram_temp_cache is not None and 
            current_time - RAMMetricsCollector._lhm_ram_cache_time < RAMMetricsCollector._lhm_ram_cache_ttl):
            return {"ram_temperature": RAMMetricsCollector._lhm_ram_temp_cache}
        
        ram_temp = None
        
        try:
            # Configurar timeout para operaciones WMI para evitar bloqueos en la UI
            lhm_wmi_connection = wmi.WMI(namespace=r"root\LibreHardwareMonitor")
            
            # Usar una consulta más específica en lugar de obtener todos los sensores
            wql = "SELECT Value FROM Sensor WHERE SensorType='Temperature' AND Name LIKE '%RAM%' OR Name LIKE '%Memory%'"
            results = lhm_wmi_connection.query(wql)
            
            if results and len(results) > 0:
                for result in results:
                    if hasattr(result, 'Value') and result.Value is not None:
                        ram_temp = result.Value
                        break
            
            # Actualizar caché
            RAMMetricsCollector._lhm_ram_temp_cache = ram_temp
            RAMMetricsCollector._lhm_ram_cache_time = current_time
                    
            return {"ram_temperature": ram_temp} if ram_temp is not None else None
            
        except Exception as e:
            logger.error(f"Error getting RAM metrics from LHM: {e}")
            return None

    def get_metrics(self) -> Dict[str, Optional[float]]:
        """Get RAM metrics

        Returns:
            Dict with the following keys:
            - total: Total RAM in GB
            - used: Used RAM in GB
            - available: Available RAM in GB
            - percent: RAM usage percentage
            - ram_temperature: RAM temperature in Celsius (from LHM, Windows only)
        """
        metrics = {
            "total": None, 
            "used": None, 
            "available": None, 
            "percent": None,
            "ram_temperature": None # Initialize LHM specific metric
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

        if self.platform_system == "Windows":
            lhm_ram_metrics = self._get_lhm_ram_metrics()
            if lhm_ram_metrics.get("ram_temperature") is not None:
                 metrics["ram_temperature"] = lhm_ram_metrics["ram_temperature"]
            # Update other LHM specific metrics if any were added and are valid

        logger.debug(f"RAM Metrics: {metrics}")
        return metrics
