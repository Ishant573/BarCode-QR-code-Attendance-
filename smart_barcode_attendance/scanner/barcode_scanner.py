"""
Barcode Scanner Module
Handles webcam access, barcode/QR code detection and decoding using OpenCV and zbar-py.
"""

import cv2
import numpy as np
import zbar
import threading
import time


class BarcodeScanner:
    """
    Real-time barcode and QR code scanner using webcam.
    Features:
    - Webcam feed display
    - Barcode/QR code detection and decoding
    - Green box around detected codes
    - Threaded operation for non-blocking UI
    """

    def __init__(self, camera_id=0):
        """
        Initialize the barcode scanner.

        Args:
            camera_id (int): Camera device ID (default: 0 for built-in webcam).
        """
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False
        self.callback = None
        self.thread = None
        self.frame = None
        self.zbar_scanner = zbar.Scanner()
        self.last_detected_data = None
        self.last_detected_time = 0
        self.cooldown_period = 2  # Seconds between repeated scans

    def set_callback(self, callback_func):
        """
        Set the callback function for when a barcode is detected.

        Args:
            callback_func: Function to call with decoded barcode data.
        """
        self.callback = callback_func

    def start(self):
        """Start the camera and begin scanning in a separate thread."""
        if self.is_running:
            print("[Scanner] Already running.")
            return

        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                raise Exception("Could not open webcam. Please check camera connection.")

            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.is_running = True
            self.thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.thread.start()
            print("[Scanner] Camera started successfully.")
        except Exception as e:
            print(f"[Scanner Error] {e}")
            raise

    def stop(self):
        """Stop the camera and scanning process."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.frame = None
        print("[Scanner] Camera stopped.")

    def _scan_loop(self):
        """Main scanning loop running in a separate thread."""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                # Store the current frame for UI display
                self.frame = frame.copy()

                # Convert frame to grayscale for zbar scanning
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Detect and decode barcodes/QR codes using zbar-py
                symbols = self.zbar_scanner.scan(gray)

                for symbol in symbols:
                    # Decode the barcode data
                    barcode_data = symbol.data.decode("utf-8")
                    barcode_type = symbol.type

                    # Get position points (list of (x, y) tuples)
                    position = symbol.position
                    if len(position) >= 4:
                        # Calculate bounding rectangle from position points
                        xs = [p[0] for p in position]
                        ys = [p[1] for p in position]
                        x, y = min(xs), min(ys)
                        w, h = max(xs) - x, max(ys) - y
                    else:
                        continue

                    # Draw green rectangle around the barcode
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

                    # Display barcode data on frame
                    text = f"{barcode_type}: {barcode_data}"
                    cv2.putText(frame, text, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # Check cooldown to avoid repeated scans
                    current_time = time.time()
                    if (current_time - self.last_detected_time) > self.cooldown_period:
                        if barcode_data != self.last_detected_data:
                            self.last_detected_data = barcode_data
                            self.last_detected_time = current_time
                            print(f"[Scanner] Detected: {barcode_type} -> {barcode_data}")

                            # Trigger callback
                            if self.callback:
                                self.callback(barcode_data)

                # Update the frame with annotations for GUI display
                self.frame = frame

            except Exception as e:
                print(f"[Scanner Loop Error] {e}")
                time.sleep(0.1)

        # Cleanup
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_current_frame(self):
        """
        Get the current frame with annotations.

        Returns:
            numpy.ndarray: Current frame or None if not available.
        """
        return self.frame

    def generate_test_barcode(self):
        """
        Generate a test barcode/QR code image for testing without a webcam.
        This creates a simple QR code-like pattern using numpy.

        Returns:
            numpy.ndarray: Test image with a simulated QR code.
        """
        # Create a blank image
        img = np.ones((400, 400, 3), dtype=np.uint8) * 255

        # Draw a simplified QR code pattern (visual only, not functional)
        cv2.rectangle(img, (50, 50), (350, 350), (0, 0, 0), 2)
        cv2.putText(img, "TEST_BARCODE", (80, 200),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        cv2.putText(img, "Place QR/Barcode", (80, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        cv2.putText(img, "Here", (150, 290),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

        return img

