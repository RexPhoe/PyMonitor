#!/usr/bin/env python3
"""
Script to fix 'cocoa' plugin in macOS for PyQt6
This script must be run from the same directory as requirements.txt
"""

import os
import sys
import subprocess
import platform
import importlib.util


def run_command(cmd, check=True):
    """Run a command and show output"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    if check and result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        sys.exit(1)
    return result


def is_package_installed(package_name):
    """Check if a package is installed using importlib"""
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except (ImportError, AttributeError):
        # Try to import directly as an alternative
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False


def main():
    """Main function to fix PyQt6 installation on macOS"""
    if platform.system() != "Darwin":
        print("This script is only for macOS")
        sys.exit(1)

    print("=== Fixing PyQt6 installation on macOS ===")

    # 1. Uninstall PyQt6 if installed for a clean reinstallation
    if is_package_installed("PyQt6"):
        print("Uninstalling PyQt6 for a clean reinstallation...")
        run_command(
            [
                sys.executable,
                "-m",
                "pip",
                "uninstall",
                "-y",
                "PyQt6",
                "PyQt6-Qt6",
                "PyQt6-sip",
            ]
        )

    # 2. Make sure pip is updated
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

    # 3. Install basic packages for macOS
    print("Installing basic packages for macOS...")
    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "setuptools==68.2.2",
            "wheel==0.41.2",
            "packaging==23.1",
            "pyparsing==3.1.1",
        ]
    )

    # 4. Install PyQt6 with its necessary components
    print("Installing PyQt6 with the cocoa plugin...")
    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--prefer-binary",
            "PyQt6==6.4.2",
            "PyQt6-Qt6==6.4.2",
            "PyQt6-sip==13.4.1",
        ]
    )

    # 5. Install other packages from requirements.txt except the ones already installed
    print("Installing other required packages...")
    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--prefer-binary",
            "psutil==5.9.5",
            "pynvml==11.5.0",
            "qtawesome==1.2.3",
            "virtualenv==20.24.5",
        ]
    )

    # 6. Verify PyQt6 installation
    try:
        print("Verifying PyQt6 installation...")
        import PyQt6
        import PyQt6.QtCore

        print(f"PyQt6 installed correctly. Version: {PyQt6.QtCore.PYQT_VERSION_STR}")
        print(f"Qt version: {PyQt6.QtCore.QT_VERSION_STR}")

        # Verify that the cocoa plugin is available
        from PyQt6.QtWidgets import QApplication

        print(
            "Creating a test application to verify that the cocoa plugin is available..."
        )
        app = QApplication([])
        print("Success! The test application was created successfully.")

    except ImportError as e:
        print(f"Error importing PyQt6: {e}")
        print("The installation did not complete successfully.")
        sys.exit(1)
    except Exception as e:
        print(f"Error initializing the application: {e}")
        print("It is possible that the cocoa plugin is still not available.")
        sys.exit(1)

    print("\n=== Installation completed successfully ===")
    print("Now you can run your PyQt6 application on macOS.")


if __name__ == "__main__":
    main()
