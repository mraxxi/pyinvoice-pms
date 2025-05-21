#!/usr/bin/env python3
# main.py
"""
Invoice Generator Application - Main Entry Point

A PyQt-based invoice generation application with PDF export functionality.
Organized in a modular structure for better maintainability and scalability.

Author: Invoice Generator Team
Version: 1.0.0
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import application modules
from main_window import MainWindow
import config
import utils

# Set the attribute before creating the app
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def setup_application():
    """Configure the QApplication with appropriate settings."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("Invoice Generator")

    # Enable high DPI support (moved up to before setup)
    # app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    return app


def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []

    try:
        import PyQt5
    except ImportError:
        missing_deps.append("PyQt5")

    try:
        import reportlab
    except ImportError:
        missing_deps.append("reportlab")

    if missing_deps:
        print("Error: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install the missing dependencies using:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False

    return True


def main():
    """Main entry point of the application."""
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)

    try:
        # Create and configure the application
        app = setup_application()

        # Create and show the main window
        main_window = MainWindow()
        main_window.show()

        # Log startup
        print(f"Started {config.APP_NAME} v{config.APP_VERSION}")

        # Run the application event loop
        sys.exit(app.exec_())

    except Exception as e:
        utils.log_error("Application startup failed", e)
        print(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()