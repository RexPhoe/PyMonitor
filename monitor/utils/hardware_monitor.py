import time
from typing import Dict, Any, Optional
from .cpu_metrics import CPUMetricsCollector
from .gpu_metrics import GPUMetricsCollector
from .ram_metrics import RAMMetricsCollector
from .network_metrics import NetworkMetricsCollector
from .logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)

class HardwareMonitor:
    """A class to monitor all hardware metrics and display them in a user-friendly format."""
    
    def __init__(self):
        """Initialize all metric collectors."""
        self.cpu_collector = CPUMetricsCollector()
        self.gpu_collector = GPUMetricsCollector()
        self.ram_collector = RAMMetricsCollector()
        self.network_collector = NetworkMetricsCollector()
        logger.info("HardwareMonitor initialized with all collectors")
        
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all hardware metrics from all collectors.
        
        Returns:
            Dict with categories as keys (cpu, gpu, ram, network) and their respective metrics as values
        """
        try:
            cpu_metrics = self.cpu_collector.get_metrics()
            gpu_metrics = self.gpu_collector.get_metrics()
            ram_metrics = self.ram_collector.get_metrics()
            network_metrics = self.network_collector.get_metrics()
            
            all_metrics = {
                "cpu": cpu_metrics,
                "gpu": gpu_metrics,
                "ram": ram_metrics,
                "network": network_metrics
            }
            
            logger.debug(f"Collected all hardware metrics successfully")
            return all_metrics
            
        except Exception as e:
            logger.error(f"Error collecting all metrics: {e}")
            return {
                "cpu": {},
                "gpu": {},
                "ram": {},
                "network": {}
            }
    
    def display_metrics(self, metrics: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """
        Display all hardware metrics in a formatted manner.
        
        Args:
            metrics: Optional pre-collected metrics. If None, will collect metrics on the spot.
        """
        if metrics is None:
            metrics = self.get_all_metrics()
        
        print("\n" + "="*60)
        print(f"{' HARDWARE METRICS MONITOR ':=^60}")
        print("="*60)
        
        # CPU Section
        print("\n" + "-"*20 + " CPU METRICS " + "-"*20)
        if metrics["cpu"]:
            for key, value in metrics["cpu"].items():
                if value is not None:
                    # Format CPU usage and temperature values with specific precision
                    if "usage" in key.lower() or "utilization" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")
                    elif "temp" in key.lower() or "temperature" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.1f}°C")
                    elif "frequency" in key.lower() or "clock" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f} GHz")
                    else:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"  {key.replace('_', ' ').title()}: N/A")
        else:
            print("  No CPU metrics available")
        
        # GPU Section
        print("\n" + "-"*20 + " GPU METRICS " + "-"*20)
        if metrics["gpu"]:
            for key, value in metrics["gpu"].items():
                if value is not None:
                    # Format GPU values with specific precision
                    if "usage" in key.lower() or "utilization" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")
                    elif "temp" in key.lower() or "temperature" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.1f}°C")
                    elif "memory" in key.lower() and "used" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f} GB")
                    elif "memory" in key.lower() and "total" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f} GB")
                    elif "clock" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value} MHz")
                    else:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"  {key.replace('_', ' ').title()}: N/A")
        else:
            print("  No GPU metrics available")
        
        # RAM Section
        print("\n" + "-"*20 + " RAM METRICS " + "-"*20)
        if metrics["ram"]:
            for key, value in metrics["ram"].items():
                if value is not None:
                    # Format RAM values with specific precision
                    if "percent" in key.lower() or "usage" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f}%")
                    elif "gb" in key.lower() or "total" in key.lower() or "used" in key.lower() or "available" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f} GB")
                    elif "temp" in key.lower() or "temperature" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.1f}°C")
                    else:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"  {key.replace('_', ' ').title()}: N/A")
        else:
            print("  No RAM metrics available")
        
        # Network Section
        print("\n" + "-"*20 + " NETWORK METRICS " + "-"*20)
        if metrics["network"]:
            for key, value in metrics["network"].items():
                if value is not None:
                    # Format network values with specific precision
                    if "speed" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f} MB/s")
                    elif "total" in key.lower() or "sent" in key.lower() or "received" in key.lower():
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f} GB")
                    else:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"  {key.replace('_', ' ').title()}: N/A")
        else:
            print("  No Network metrics available")
            
        print("\n" + "="*60)
        print(f"{' End of Hardware Metrics ':=^60}")
        print("="*60 + "\n")

    def monitor_continuously(self, interval: float = 1.0, duration: Optional[float] = None) -> None:
        """
        Continuously monitor and display hardware metrics at specified intervals.
        
        Args:
            interval: Time in seconds between each metrics update (default: 1.0)
            duration: Optional total monitoring duration in seconds. If None, runs indefinitely.
        """
        start_time = time.time()
        iterations = 0
        
        try:
            while True:
                # Clear screen (for Windows)
                print("\033c", end="")  # ANSI escape sequence to clear screen
                
                # Get and display metrics
                metrics = self.get_all_metrics()
                self.display_metrics(metrics)
                
                # Show monitoring information
                iterations += 1
                elapsed_time = time.time() - start_time
                print(f"Monitoring: Iteration #{iterations} | Running for: {elapsed_time:.1f}s | Refresh: {interval}s")
                
                # Check if we've reached the duration limit
                if duration and elapsed_time >= duration:
                    print(f"\nMonitoring completed after {duration:.1f} seconds ({iterations} iterations)")
                    break
                    
                # Wait for the next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            elapsed_time = time.time() - start_time
            print(f"\nMonitoring stopped after {elapsed_time:.1f} seconds ({iterations} iterations)")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
            print(f"\nError occurred during monitoring: {e}")


if __name__ == "__main__":
    # Example usage
    monitor = HardwareMonitor()
    
    print("Single metrics snapshot:")
    monitor.display_metrics()
    
    print("\nStarting continuous monitoring for 10 seconds...")
    monitor.monitor_continuously(interval=2.0, duration=10.0)
