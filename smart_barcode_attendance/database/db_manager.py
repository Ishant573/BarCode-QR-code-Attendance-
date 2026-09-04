"""
Database Manager Module
Handles all SQLite database operations for the Smart Barcode Attendance System.
"""

import sqlite3
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DB_PATH = os.path.join(BASE_DIR, "attendance.db")


def resolve_db_path(custom_path=None):
    """Resolve database path, using /tmp in serverless / read-only environments."""
    if custom_path:
        return custom_path

    # Check if running in Vercel or AWS Lambda serverless runtime
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    if is_serverless:
        tmp_db = "/tmp/attendance.db"
        if not os.path.exists(tmp_db) and os.path.exists(LOCAL_DB_PATH):
            try:
                import shutil
                shutil.copyfile(LOCAL_DB_PATH, tmp_db)
            except Exception:
                pass
        return tmp_db

    # In local environment, verify write access; fallback to /tmp if read-only
    try:
        test_file = os.path.join(BASE_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return LOCAL_DB_PATH
    except OSError:
        tmp_db = "/tmp/attendance.db"
        if not os.path.exists(tmp_db) and os.path.exists(LOCAL_DB_PATH):
            try:
                import shutil
                shutil.copyfile(LOCAL_DB_PATH, tmp_db)
            except Exception:
                pass
        return tmp_db


class DatabaseManager:
    """
    Manages SQLite database operations including:
    - Creating tables
    - Student CRUD operations
    - Attendance recording and retrieval
    """

    def __init__(self, db_path=None):
        """
        Initialize the database manager.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = resolve_db_path(db_path)
        self.connection = None
        self.connect()
        self.create_tables()
        self.seed_initial_data_if_empty()

    def connect(self):
        """Establish connection to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            print(f"[DB] Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"[DB ERROR] Failed to connect: {e}")
            raise

    def create_tables(self):
        """
        Create the required tables if they don't exist.
        Tables: students, attendance
        """
        cursor = self.connection.cursor()

        # Students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                department TEXT NOT NULL,
                barcode_id TEXT NOT NULL UNIQUE
            )
        """)

        # Attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'Present',
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        """)

        # Create index for faster duplicate checking
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_student_date
            ON attendance(student_id, date)
        """)

        self.connection.commit()
        print("[DB] Tables created successfully.")

    def seed_initial_data_if_empty(self):
        """Seed initial demo students if the database has no student records."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM students")
            count = cursor.fetchone()[0]
            if count == 0:
                demo_students = [
                    ("Test Student", "Computer Science", "STU-0FC50AEABF83"),
                    ("John Doe", "Computer Science", "STU-0171727A0C93"),
                    ("Jane Smith", "Mathematics", "STU-5279F4D4E2D9"),
                    ("Bhushan", "BCA", "STU-99932E01453B"),
                    ("Ishant", "BCA", "STU-FB9CA6F3D0A2"),
                    ("Rashmita", "BCA", "STU-94E885B578F0"),
                ]
                cursor.executemany(
                    "INSERT INTO students (student_name, department, barcode_id) VALUES (?, ?, ?)",
                    demo_students,
                )
                self.connection.commit()
                print(f"[DB] Seeded {len(demo_students)} initial student records.")
        except Exception as e:
            print(f"[DB] Error checking/seeding initial data: {e}")

    # ==================== STUDENT OPERATIONS ====================

    def add_student(self, name, department, barcode_id):
        """
        Add a new student to the database.

        Args:
            name (str): Student name.
            department (str): Department/Course.
            barcode_id (str): Unique barcode/QR code identifier.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO students (student_name, department, barcode_id) VALUES (?, ?, ?)",
                (name, department, barcode_id)
            )
            self.connection.commit()
            return (True, f"Student '{name}' registered successfully with Barcode ID: {barcode_id}")
        except sqlite3.IntegrityError:
            return (False, f"Error: Barcode ID '{barcode_id}' already exists in the system.")
        except sqlite3.Error as e:
            return (False, f"Database error: {e}")

    def get_student_by_barcode(self, barcode_id):
        """
        Retrieve a student record by their barcode ID.

        Args:
            barcode_id (str): The barcode/QR code identifier.

        Returns:
            dict: Student details or None if not found.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM students WHERE barcode_id = ?",
            (barcode_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_all_students(self):
        """
        Retrieve all registered students.

        Returns:
            list: List of student dictionaries.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM students ORDER BY student_name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_students(self, search_term):
        """
        Search for students by name, department, or barcode ID.

        Args:
            search_term (str): Search keyword.

        Returns:
            list: List of matching student dictionaries.
        """
        cursor = self.connection.cursor()
        query = """
            SELECT * FROM students
            WHERE student_name LIKE ? OR department LIKE ? OR barcode_id LIKE ?
            ORDER BY student_name
        """
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_student(self, student_id):
        """
        Delete a student and their attendance records.

        Args:
            student_id (int): The student ID to delete.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            cursor = self.connection.cursor()
            # Delete attendance records first
            cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
            # Delete student
            cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            self.connection.commit()
            return (True, "Student deleted successfully.")
        except sqlite3.Error as e:
            return (False, f"Error deleting student: {e}")

    # ==================== ATTENDANCE OPERATIONS ====================

    def has_attendance_today(self, student_id):
        """
        Check if attendance has already been marked for a student today.

        Args:
            student_id (int): The student ID.

        Returns:
            bool: True if attendance already recorded today.
        """
        cursor = self.connection.cursor()
        today_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, today_date)
        )
        count = cursor.fetchone()[0]
        return count > 0

    def mark_attendance(self, student_id):
        """
        Mark attendance for a student.

        Args:
            student_id (int): The student ID.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check for duplicate
            if self.has_attendance_today(student_id):
                return (False, "Attendance already marked for today.")

            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")

            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, 'Present')",
                (student_id, date_str, time_str)
            )
            self.connection.commit()
            return (True, f"Attendance marked successfully at {time_str}")
        except sqlite3.Error as e:
            return (False, f"Error marking attendance: {e}")

    def get_attendance_for_student(self, student_id):
        """
        Get all attendance records for a specific student.

        Args:
            student_id (int): The student ID.

        Returns:
            list: List of attendance record dictionaries.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC",
            (student_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_attendance_records(self, date_filter=None):
        """
        Get all attendance records with student details.

        Args:
            date_filter (str, optional): Filter by date (YYYY-MM-DD).

        Returns:
            list: List of attendance records with student info.
        """
        cursor = self.connection.cursor()
        if date_filter:
            query = """
                SELECT a.attendance_id, a.date, a.time, a.status,
                       s.student_id, s.student_name, s.department, s.barcode_id
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE a.date = ?
                ORDER BY a.date DESC, a.time DESC
            """
            cursor.execute(query, (date_filter,))
        else:
            query = """
                SELECT a.attendance_id, a.date, a.time, a.status,
                       s.student_id, s.student_name, s.department, s.barcode_id
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                ORDER BY a.date DESC, a.time DESC
            """
            cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_today_attendance(self):
        """Get today's attendance records."""
        today_date = datetime.now().strftime("%Y-%m-%d")
        return self.get_attendance_records(date_filter=today_date)

    def get_attendance_percentage(self, student_id):
        """
        Calculate attendance percentage for a student.
        Based on total days since first attendance or a defined period.

        Args:
            student_id (int): The student ID.

        Returns:
            float: Attendance percentage.
        """
        cursor = self.connection.cursor()

        # Get total distinct days the student has attended
        cursor.execute(
            "SELECT COUNT(DISTINCT date) FROM attendance WHERE student_id = ?",
            (student_id,)
        )
        attended_days = cursor.fetchone()[0]

        # For a simple calculation, use a 30-day window
        total_days = 30
        percentage = (attended_days / total_days) * 100 if total_days > 0 else 0
        return round(percentage, 2)

    def get_daily_attendance_report(self, date=None):
        """
        Generate a daily attendance report.

        Args:
            date (str, optional): Date string (YYYY-MM-DD). Defaults to today.

        Returns:
            list: List of attendance records for the day.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.get_attendance_records(date_filter=date)

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("[DB] Database connection closed.")

