#!/usr/bin/env python3
"""
Smart Barcode Attendance System - Launcher Script

This script can be used to quickly launch the application.
On macOS/Linux, you can make it executable with:
    chmod +x run.py
    ./run.py

Or simply run:
    python run.py
"""

import subprocess
import sys
import os


def main():
    """Launch the main application."""
    script_path = os.path.join(os.path.dirname(__file__), "main.py")

    try:
        subprocess.run([sys.executable, script_path], check=True)
    except KeyboardInterrupt:
        print("\n[Launcher] Application closed.")
    except Exception as e:
        print(f"[Launcher] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

