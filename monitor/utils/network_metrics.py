import psutil
import time
import platform
from typing import Dict, Optional, Tuple
from .logging_utils import get_logger

# WMI for LibreHardwareMonitor
LHM_WMI_AVAILABLE = False
WMIService = None
try:
    if platform.system() == "Windows": # Only attempt WMI import on Windows
        import wmi
        WMIService = wmi
        LHM_WMI_AVAILABLE = True
except ImportError:
    logger.info("Python WMI module not found. LibreHardwareMonitor metrics for network will be unavailable.")
except Exception as e:
    logger.error(f"Error initializing WMI for LHM network metrics: {e}")

# Configure logger
logger = get_logger(__name__)


class NetworkMetricsCollector:
    """A class to handle network metrics collection across different platforms"""

    def __init__(self):
        """Initialize the network metrics collector"""
        self.platform = platform.system()
        initial_counters = self._get_initial_psutil_counters()
        self.last_bytes_sent = initial_counters[0]
        self.last_bytes_recv = initial_counters[1]
        self.last_time = time.time()
        # Heuristic: If initial counters are zero, last_time should be slightly in the past
        # to allow the first get_metrics call to establish a baseline without a tiny time_elapsed.
        # However, a more robust way is to handle the first valid delta in get_metrics.
        # For now, if initial counters are 0, the first speed calc might be total/small_time.
        # This is often acceptable for a brief moment.

    def _get_initial_psutil_counters(self) -> Tuple[int, int]:
        """Helper to get initial byte counters from psutil."""
        try:
            counters = psutil.net_io_counters()
            return counters.bytes_sent, counters.bytes_recv
        except Exception as e:
            logger.warning(f"Could not get initial psutil network counters: {e}")
            return 0, 0

    def get_metrics(self) -> Dict[str, Optional[float]]:
        """Get network metrics

        Returns:
            Dict with the following keys:
            - upload_speed: Current upload speed in MB/s
            - download_speed: Current download speed in MB/s
            - total_sent: Total bytes sent in GB
            - total_received: Total bytes received in GB
        """
        try:
            net_counters = psutil.net_io_counters()
            current_time = time.time()

            # Calculate speeds
            time_elapsed = current_time - self.last_time
            bytes_sent = net_counters.bytes_sent
            bytes_recv = net_counters.bytes_recv

            upload_speed = (bytes_sent - self.last_bytes_sent) / (
                time_elapsed * 1024 * 1024
            )  # MB/s
            download_speed = (bytes_recv - self.last_bytes_recv) / (
                time_elapsed * 1024 * 1024
            )  # MB/s

            metrics = {
                "upload_speed": upload_speed,
                "download_speed": download_speed,
                "total_sent": bytes_sent / (1024**3),  # Convert to GB
                "total_received": bytes_recv / (1024**3),  # Convert to GB
            }

            # Update last values
            self.last_bytes_sent = bytes_sent
            self.last_bytes_recv = bytes_recv
            self.last_time = current_time

            logger.debug(f"Network Metrics: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Error getting network metrics from psutil: {e}")
            # psutil failed, clear psutil-based values and try LHM for totals.
            metrics = {
                "upload_speed": None,
                "download_speed": None,
                "total_sent": None,
                "total_received": None,
            }
            # Reset last_bytes for psutil, so if it recovers, it doesn't use stale data for speed.
            self.last_bytes_sent = 0 
            self.last_bytes_recv = 0
            # self.last_time is not reset here, it reflects the last known good time or init time.

            if self.platform == "Windows" and LHM_WMI_AVAILABLE:
                logger.info("Attempting to get network totals from LHM as psutil failed.")
                lhm_totals = self._get_lhm_network_totals()
                if lhm_totals:
                    if lhm_totals.get("lhm_total_sent") is not None:
                        metrics["total_sent"] = lhm_totals["lhm_total_sent"] / (1024**3) # GB
                    if lhm_totals.get("lhm_total_recv") is not None:
                        metrics["total_received"] = lhm_totals["lhm_total_recv"] / (1024**3) # GB
            
            logger.debug(f"Network Metrics (psutil failed, LHM fallback attempted): {metrics}")
            return metrics

    def _get_lhm_network_totals(self) -> Optional[Dict[str, float]]:
        """Get total network data sent/received from LHM sensors."""
        if not LHM_WMI_AVAILABLE or WMIService is None:
            logger.debug("LHM WMI not available for Network metrics.")
            return None

        lhm_total_sent_bytes = 0.0
        lhm_total_recv_bytes = 0.0
        found_data = False

        try:
            conn = WMIService.WMI(namespace=r"root\LibreHardwareMonitor")
            sensors = conn.Sensor() # This might be time-consuming if many sensors

            for sensor in sensors:
                if not hasattr(sensor, 'Value') or sensor.Value is None or \
                   not hasattr(sensor, 'SensorType') or not hasattr(sensor, 'Name') or \
                   not hasattr(sensor, 'Identifier') or not sensor.Identifier:
                    continue
                
                # Filter for network adapter sensors first using Identifier
                # Common identifiers: /lhmplugincommsnetworkadapter/{guid}/... or /lhmnetworkadapter/{guid}/...
                # We are interested in hardware sensors, not per-process if LHM provides that.
                sensor_id_lower = sensor.Identifier.lower()
                if not ('/networkadapter/' in sensor_id_lower or '/lhmnetworkadapter/' in sensor_id_lower or '/lhmplugincommsnetworkadapter/' in sensor_id_lower):
                    if not ('network' in sensor_id_lower or 'ethernet' in sensor_id_lower or 'wi-fi' in sensor_id_lower or 'wlan' in sensor_id_lower):
                         continue # Skip non-network adapter related sensors based on identifier

                s_type = sensor.SensorType.lower()
                s_name = sensor.Name.lower()
                
                if s_type == "data": # LHM uses "Data" for byte counters
                    # Example LHM Names: "Ethernet - Data Uploaded", "Wi-Fi - Data Downloaded"
                    # Summing up all could be problematic if LHM reports virtual/loopback adapters.
                    # A more robust way would be to identify the primary active adapter(s), but that's complex.
                    # For now, sum all found "Data Uploaded/Downloaded" type sensors associated with network adapters.
                    if "upload" in s_name or "sent" in s_name: 
                        lhm_total_sent_bytes += float(sensor.Value)
                        found_data = True
                    elif "download" in s_name or "recv" in s_name or "received" in s_name: 
                        lhm_total_recv_bytes += float(sensor.Value)
                        found_data = True
            
            if found_data:
                logger.debug(f"LHM Network Totals: Sent={lhm_total_sent_bytes}, Recv={lhm_total_recv_bytes}")
                return {"lhm_total_sent": lhm_total_sent_bytes, "lhm_total_recv": lhm_total_recv_bytes}
            else:
                logger.debug("No suitable LHM network total data sensors found.")
                return None

        except AttributeError as ae: # Catch specific error if WMI object is not as expected (e.g. during shutdown)
            logger.warning(f"AttributeError while querying LHM Network sensors (possibly WMI issue): {ae}")
            return None
        except Exception as e:
            # Using a general exception type for WMI specific errors like pythoncom.com_error or wmi.x_wmi
            logger.error(f"Error querying LHM Network sensors: {e} (Type: {type(e).__name__})")
            return None
