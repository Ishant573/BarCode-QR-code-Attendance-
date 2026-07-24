"""
Smart Barcode Attendance System
Main entry point for the application.

This application provides a complete barcode/QR code attendance management
system with webcam scanning, student registration, and reporting features.

Usage:
    python main.py

Requirements:
    - Python 3.x
    - OpenCV (opencv-python)
    - Tkinter
    - SQLite3
    - Pandas
    - Pyzbar
    - Pillow
"""

import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")

import tkinter as tk
from ui.main_window import SmartBarcodeAttendanceSystem


def main():
    """
    Main function to launch the Smart Barcode Attendance System.
    Sets up the Tkinter root window and initializes the application.
    """
    try:
        # Create root window
        root = tk.Tk()

        # Set geometry BEFORE initializing to ensure window has proper size on macOS
        root.geometry("1280x800")
        root.minsize(1024, 600)

        # Initialize application
        app = SmartBarcodeAttendanceSystem(root)

        # Center the window on screen after a short delay to ensure proper window mapping
        root.after(100, lambda: _center_window(root))

        # Start the main loop
        print("[App] Smart Barcode Attendance System is running...")
        root.mainloop()

    except KeyboardInterrupt:
        print("\n[App] Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"[App] Fatal error: {e}")
        sys.exit(1)


def _center_window(root):
    """Center the window on screen after it has been properly sized."""
    try:
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        # Fallback if width/height are still incorrectly small
        if width < 100 or height < 100:
            width, height = 1280, 800
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
    except Exception as e:
        print(f"[App] Warning: Could not center window: {e}")


if __name__ == "__main__":
    main()

