#!/usr/bin/env python
"""
Hardware Metrics Monitor

This script displays metrics from various hardware components 
(CPU, GPU, RAM, and Network) in a continuously updating console interface.
"""

from monitor.utils.hardware_monitor import HardwareMonitor
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor hardware metrics')
    parser.add_argument('--interval', '-i', type=float, default=1.0,
                        help='Update interval in seconds (default: 1.0)')
    parser.add_argument('--duration', '-d', type=float, default=None,
                        help='Total duration to run in seconds (default: indefinitely)')
    parser.add_argument('--snapshot', '-s', action='store_true',
                        help='Take a single snapshot instead of continuous monitoring')
    
    args = parser.parse_args()
    
    # Create hardware monitor instance
    monitor = HardwareMonitor()
    
    # Either take a snapshot or monitor continuously
    if args.snapshot:
        monitor.display_metrics()
    else:
        try:
            print(f"Starting hardware monitoring (Press Ctrl+C to stop)")
            print(f"Update interval: {args.interval} seconds")
            if args.duration:
                print(f"Duration: {args.duration} seconds")
            else:
                print(f"Duration: indefinite (until Ctrl+C)")
                
            monitor.monitor_continuously(interval=args.interval, duration=args.duration)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

if __name__ == "__main__":
    main()
