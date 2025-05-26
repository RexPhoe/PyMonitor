"""
Metrics Formatter Module

This module handles formatting of metrics for display in the UI.
"""

class MetricsFormatter:
    """Class responsible for formatting hardware metrics for display"""
    
    @staticmethod
    def format_cpu_metrics(data):
        """
        Format CPU metrics for display.
        
        Args:
            data: Dictionary containing CPU metrics
            
        Returns:
            dict: Dictionary of formatted CPU metric strings
        """
        formatted = {}
        
        # CPU Usage
        usage = data.get("usage")
        formatted["cpu_usage"] = f"Usage: {usage:.1f}%" if usage is not None else "Usage: N/A"
        
        # CPU Temperature
        temp = data.get("temperature")
        formatted["cpu_temperature"] = f"Temp: {temp:.1f}°C" if temp is not None else "Temp: N/A"
        
        # CPU Frequency or Model
        freq = data.get("frequency")
        cpu_model = data.get("cpu_model")
        
        if freq is not None:
            # Convert MHz to GHz if needed
            if freq > 1000:  # If value is in MHz
                freq = freq / 1000
            formatted["cpu_frequency"] = f"Freq: {freq:.2f} GHz"
        elif cpu_model is not None:
            # Use CPU model when frequency is unavailable (especially for Apple Silicon)
            formatted["cpu_frequency"] = f"CPU: {cpu_model}"
        else:
            formatted["cpu_frequency"] = "Freq: N/A"
        
        # CPU Voltage
        voltage = data.get("voltage")
        formatted["cpu_voltage"] = f"Voltage: {voltage:.3f}V" if voltage is not None else "Voltage: N/A"
        
        return formatted
    
    @staticmethod
    def format_gpu_metrics(data):
        """
        Format GPU metrics for display.
        
        Args:
            data: Dictionary containing GPU metrics
            
        Returns:
            dict: Dictionary of formatted GPU metric strings
        """
        formatted = {}
        
        # GPU Core Usage
        usage = data.get("core_usage")
        formatted["gpu_core_usage"] = f"Core Usage: {usage:.1f}%" if usage is not None else "Core Usage: N/A"
        
        # GPU Core Temperature
        temp = data.get("core_temperature")
        formatted["gpu_core_temperature"] = f"Core Temp: {temp:.1f}°C" if temp is not None else "Core Temp: N/A"
        
        # GPU Core Frequency
        freq = data.get("core_frequency")
        formatted["gpu_core_frequency"] = f"Core Freq: {freq:.0f} MHz" if freq is not None else "Core Freq: N/A"
        
        # GPU Memory Frequency
        freq = data.get("memory_frequency")
        formatted["gpu_memory_frequency"] = f"Mem Freq: {freq:.0f} MHz" if freq is not None else "Mem Freq: N/A"
        
        # GPU Memory Temperature
        temp = data.get("memory_temperature")
        formatted["gpu_memory_temperature"] = f"Mem Temp: {temp:.1f}°C" if temp is not None else "Mem Temp: N/A"
        
        # GPU Hotspot Temperature
        temp = data.get("hotspot_temperature")
        formatted["gpu_hotspot_temperature"] = f"Hotspot: {temp:.1f}°C" if temp is not None else "Hotspot: N/A"
        
        # GPU VRAM Usage
        usage = data.get("vram_usage_percent")
        formatted["gpu_vram_usage"] = f"VRAM usage: {usage:.1f}%" if usage is not None else "VRAM usage: N/A"
        
        # GPU VRAM Memory
        used = data.get("vram_used_gb")
        total = data.get("vram_total_gb")
        if used is not None and total is not None and total > 0:
            formatted["gpu_vram_memory"] = f"VRAM: {used:.1f}/{total:.1f} GB"
        else:
            formatted["gpu_vram_memory"] = "VRAM: N/A"
        
        # GPU Fan Speed
        speed = data.get("fan_speed")
        formatted["gpu_fan_speed"] = f"Fan: {speed:.0f}%" if speed is not None else "Fan: N/A"
        
        return formatted
    
    @staticmethod
    def format_ram_metrics(data):
        """
        Format RAM metrics for display.
        
        Args:
            data: Dictionary containing RAM metrics
            
        Returns:
            dict: Dictionary of formatted RAM metric strings
        """
        formatted = {}
        
        # RAM Usage Percent
        percent = data.get("percent")
        formatted["ram_percent"] = f"Usage: {percent:.1f}%" if percent is not None else "Usage: N/A"
        
        # RAM Used/Total
        used = data.get("used")
        total = data.get("total")
        if used is not None and total is not None:
            formatted["ram_used_total"] = f"Used: {used:.1f}/{total:.1f} GB"
        else:
            formatted["ram_used_total"] = "Used: N/A"
        
        # RAM Available
        available = data.get("available")
        formatted["ram_available"] = f"Available: {available:.1f} GB" if available is not None else "Available: N/A"
        
        # RAM Temperature
        temp = data.get("ram_temperature")
        formatted["ram_temperature"] = f"Temp: {temp:.1f}°C" if temp is not None else "Temp: N/A"
        
        return formatted
    
    @staticmethod
    def format_network_metrics(data):
        """
        Format network metrics for display.
        
        Args:
            data: Dictionary containing network metrics
            
        Returns:
            dict: Dictionary of formatted network metric strings
        """
        formatted = {}
        
        # Network Upload Speed
        upload = data.get("upload_speed")
        formatted["network_upload_speed"] = f"Upload: {upload:.2f} MB/s" if upload is not None else "Upload: N/A"
        
        # Network Download Speed
        download = data.get("download_speed")
        formatted["network_download_speed"] = f"Download: {download:.2f} MB/s" if download is not None else "Download: N/A"
        
        # Network Total Sent
        sent = data.get("total_sent")
        formatted["network_total_sent"] = f"Total Sent: {sent:.1f} GB" if sent is not None else "Total Sent: N/A"
        
        # Network Total Received
        received = data.get("total_received")
        formatted["network_total_received"] = f"Total Recv: {received:.1f} GB" if received is not None else "Total Recv: N/A"
        
        return formatted
