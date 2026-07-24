"""
CSV Export Utility
Handles exporting attendance records to CSV files.
"""

import csv
import os
from datetime import datetime


class CSVExporter:
    """
    Utility class for exporting attendance data to CSV format.
    """

    @staticmethod
    def export_attendance(records, filepath=None):
        """
        Export attendance records to a CSV file.

        Args:
            records (list): List of attendance record dictionaries.
            filepath (str, optional): Output file path. Auto-generated if None.

        Returns:
            tuple: (success: bool, message: str, path: str)
        """
        if not records:
            return (False, "No records to export.", "")

        # Generate default filename if not provided
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"attendance_report_{timestamp}.csv"

        try:
            # Define CSV columns
            fieldnames = [
                "attendance_id", "student_id", "student_name",
                "department", "barcode_id", "date", "time", "status"
            ]

            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for record in records:
                    writer.writerow(record)

            abs_path = os.path.abspath(filepath)
            return (True, f"Report exported successfully: {abs_path}", abs_path)

        except Exception as e:
            return (False, f"Error exporting CSV: {e}", "")

    @staticmethod
    def export_students(students, filepath=None):
        """
        Export student records to a CSV file.

        Args:
            students (list): List of student record dictionaries.
            filepath (str, optional): Output file path.

        Returns:
            tuple: (success: bool, message: str, path: str)
        """
        if not students:
            return (False, "No student records to export.", "")

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"students_list_{timestamp}.csv"

        try:
            fieldnames = ["student_id", "student_name", "department", "barcode_id"]

            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for student in students:
                    writer.writerow(student)

            abs_path = os.path.abspath(filepath)
            return (True, f"Student list exported: {abs_path}", abs_path)

        except Exception as e:
            return (False, f"Error exporting student CSV: {e}", "")

