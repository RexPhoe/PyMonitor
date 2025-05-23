"""
Console Handler for PyMonitor

This module provides functionality to manage the console window on Windows,
allowing it to be hidden, shown, or minimized to the system tray.
"""

import os
import sys
import ctypes
from ctypes import wintypes, Structure, byref, sizeof
import platform

# Windows API constants
SW_HIDE = 0
SW_SHOW = 5
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_RESTORE = 9

# Define the WINDOWPLACEMENT structure since it's not in wintypes
class WINDOWPLACEMENT(Structure):
    _fields_ = [
        ('length', ctypes.c_uint),
        ('flags', ctypes.c_uint),
        ('showCmd', ctypes.c_uint),
        ('ptMinPosition', wintypes.POINT),
        ('ptMaxPosition', wintypes.POINT),
        ('rcNormalPosition', wintypes.RECT)
    ]

# Get handle to the console window
GetConsoleWindow = ctypes.windll.kernel32.GetConsoleWindow
ShowWindow = ctypes.windll.user32.ShowWindow

# For monitoring console window state
GetWindowPlacement = ctypes.windll.user32.GetWindowPlacement

class ConsoleHandler:
    """Handles the console window in Windows environments"""
    
    @staticmethod
    def is_windows():
        """Check if running on Windows"""
        return platform.system() == "Windows"
    
    @staticmethod
    def hide_console():
        """Hide the console window"""
        if ConsoleHandler.is_windows():
            console_window = GetConsoleWindow()
            if console_window:
                # Hide window from taskbar and screen
                ShowWindow(console_window, SW_HIDE)
                return True
        return False
    
    @staticmethod
    def show_console():
        """Show the console window"""
        if ConsoleHandler.is_windows():
            console_window = GetConsoleWindow()
            if console_window:
                # Restore window to normal state
                ShowWindow(console_window, SW_RESTORE)
                return True
        return False
    
    @staticmethod
    def minimize_console():
        """Minimize the console window"""
        if ConsoleHandler.is_windows():
            console_window = GetConsoleWindow()
            if console_window:
                # Minimize the window
                ShowWindow(console_window, SW_MINIMIZE)
                return True
        return False
    
    @staticmethod
    def is_console_visible():
        """Check if the console window is visible"""
        if not ConsoleHandler.is_windows():
            return True
            
        console_window = GetConsoleWindow()
        if not console_window:
            return False
            
        placement = WINDOWPLACEMENT()
        placement.length = sizeof(placement)
        GetWindowPlacement(console_window, byref(placement))
        
        # SW_HIDE means the window is hidden
        return placement.showCmd != SW_HIDE
    
    @staticmethod
    def toggle_console():
        """Toggle console visibility"""
        if ConsoleHandler.is_console_visible():
            return ConsoleHandler.hide_console()
        else:
            return ConsoleHandler.show_console()
