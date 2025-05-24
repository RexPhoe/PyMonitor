"""
Console Handler Module

This module provides functionality to show/hide the console window on Windows.
"""

import os
import platform
import ctypes

class ConsoleHandler:
    """Class for handling console window visibility"""
    
    # Windows-specific constants
    SW_HIDE = 0
    SW_SHOW = 5
    
    # Store console visibility state
    _console_visible = True
    
    @classmethod
    def is_windows(cls):
        """
        Check if the current platform is Windows.
        
        Returns:
            bool: True if running on Windows, False otherwise
        """
        return platform.system() == "Windows"
    
    @classmethod
    def hide_console(cls):
        """
        Hide the console window on Windows.
        
        Returns:
            bool: True if the console was hidden, False otherwise
        """
        if not cls.is_windows():
            return False
            
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, cls.SW_HIDE)
                cls._console_visible = False
                return True
        except Exception as e:
            print(f"Error hiding console: {e}")
        
        return False
    
    @classmethod
    def show_console(cls):
        """
        Show the console window on Windows.
        
        Returns:
            bool: True if the console was shown, False otherwise
        """
        if not cls.is_windows():
            return False
            
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, cls.SW_SHOW)
                cls._console_visible = True
                return True
        except Exception as e:
            print(f"Error showing console: {e}")
        
        return False
    
    @classmethod
    def toggle_console(cls):
        """
        Toggle console window visibility on Windows.
        
        Returns:
            bool: The new console visibility state
        """
        if cls._console_visible:
            cls.hide_console()
        else:
            cls.show_console()
        
        return cls._console_visible
    
    @classmethod
    def is_console_visible(cls):
        """
        Get the current console visibility state.
        
        Returns:
            bool: True if the console is visible, False otherwise
        """
        return cls._console_visible
