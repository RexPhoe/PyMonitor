"""
Metrics Worker Module

This module contains the worker class for collecting hardware metrics in a background thread.
"""

import threading
import time
from PyQt6.QtCore import QObject, pyqtSignal

class MetricsWorker(QObject):
    """Worker class for collecting hardware metrics in a background thread"""
    
    # Signal to emit when metrics are collected
    metrics_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, hardware_monitor):
        """
        Initialize the metrics worker.
        
        Args:
            hardware_monitor: The hardware monitor instance to collect metrics from
        """
        super().__init__()
        self.hardware_monitor = hardware_monitor
        self.running = False
        self.thread = None
        self.interval = 1.0  # Default update interval in seconds
        self.last_update_time = 0  # Track last update time
    
    def start(self, interval=1.0):
        """
        Start the worker thread.
        
        Args:
            interval: Update interval in seconds
        """
        print(f"MetricsWorker starting with interval: {interval} seconds")
        self.interval = float(interval)  # Ensure interval is float
        self.running = True
        self.last_update_time = 0  # Reset timer
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
    
    def _run(self):
        """Main worker loop - runs in a separate thread"""
        while self.running:
            # First, check the current time
            current_time = time.time()
            
            # Check if we need to collect metrics now
            if current_time - self.last_update_time >= self.interval:
                try:
                    # Record start time for diagnostics
                    start_time = time.time()
                    
                    # Collect metrics
                    metrics = self.hardware_monitor.get_all_metrics()
                    
                    # Calculate collection time for diagnostics
                    collection_time = time.time() - start_time
                    print(f"Metrics collection took {collection_time:.3f} seconds with interval {self.interval}s")
                    
                    # Emit signal with metrics
                    self.metrics_ready.emit(metrics)
                    
                    # Update the timestamp for when we last collected metrics
                    # We use current_time (before collection) to maintain proper timing
                    self.last_update_time = current_time
                except Exception as e:
                    # Emit error signal
                    self.error_occurred.emit(str(e))
            
            # Calculate how long to sleep until next update
            time_until_next_update = max(0.01, self.interval - (time.time() - self.last_update_time))
            
            # Cap the sleep time to avoid excessively long sleeps if something goes wrong
            sleep_time = min(0.1, time_until_next_update)  # Sleep max 100ms at a time for responsiveness
            
            # Short sleep to prevent CPU spinning while maintaining timing accuracy
            time.sleep(sleep_time)
