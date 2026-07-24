"""
Smart Barcode Attendance System - Flask Web Server
Host the application locally at http://localhost:5000
"""

import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file
from database.db_manager import DatabaseManager
from utils.csv_exporter import CSVExporter
from datetime import datetime
import csv
import io
import qrcode
import base64
import uuid

app = Flask(__name__)
db = DatabaseManager()

# Directory to save generated QR codes
QR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "qrcodes")
os.makedirs(QR_DIR, exist_ok=True)


def generate_barcode_id():
    """Generate a unique barcode/QR code ID for a student."""
    unique_id = uuid.uuid4().hex[:12].upper()
    return f"STU-{unique_id}"


def generate_qr_code(barcode_id, student_name=""):
    """Generate a QR code image for the given barcode ID and return base64 string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(barcode_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to file
    filename = f"{barcode_id}.png"
    filepath = os.path.join(QR_DIR, filename)
    img.save(filepath)

    # Also return as base64 for inline display
    from PIL import Image
    import io as io_module
    buffer = io_module.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_base64, filename


# ==================== ROUTES ====================

@app.route("/")
def index():
    """Dashboard page."""
    students = db.get_all_students()
    today_attendance = db.get_today_attendance()
    all_records = db.get_attendance_records()
    return render_template("index.html",
                           students_count=len(students),
                           today_count=len(today_attendance),
                           total_records=len(all_records),
                           today_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/students")
def students_page():
    """Students management page."""
    search = request.args.get("search", "").strip()
    if search:
        students = db.search_students(search)
    else:
        students = db.get_all_students()
    # Calculate attendance percentage for each
    for s in students:
        s["attendance_pct"] = db.get_attendance_percentage(s["student_id"])
    return render_template("students.html", students=students, search=search)


@app.route("/attendance")
def attendance_page():
    """Attendance records page."""
    date_filter = request.args.get("date", "").strip()
    if not date_filter:
        date_filter = None
    records = db.get_attendance_records(date_filter=date_filter)
    return render_template("attendance.html",
                           records=records,
                           filter_date=date_filter or datetime.now().strftime("%Y-%m-%d"),
                           today_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/register")
def register_page():
    """Registration page."""
    return render_template("register.html")


# ==================== API ENDPOINTS ====================

@app.route("/api/register", methods=["POST"])
def api_register():
    """API: Register a new student with auto-generated barcode ID and QR code."""
    data = request.get_json()
    name = data.get("name", "").strip()
    department = data.get("department", "").strip()
    barcode_id = data.get("barcode_id", "").strip()

    # Auto-generate barcode ID if not provided
    if not barcode_id:
        barcode_id = generate_barcode_id()

    if not name or not department:
        return jsonify({"success": False, "message": "Student name and department are required."})

    success, message = db.add_student(name, department, barcode_id)
    if success:
        # Generate QR code for the student
        qr_base64, qr_filename = generate_qr_code(barcode_id, name)
        return jsonify({
            "success": True,
            "message": message,
            "barcode_id": barcode_id,
            "qr_code": qr_base64,
            "qr_filename": qr_filename
        })
    return jsonify({"success": False, "message": message})


@app.route("/api/mark_attendance", methods=["POST"])
def api_mark_attendance():
    """API: Mark attendance by barcode ID."""
    data = request.get_json()
    barcode_id = data.get("barcode_id", "").strip()

    if not barcode_id:
        return jsonify({"success": False, "message": "Barcode ID is required."})

    student = db.get_student_by_barcode(barcode_id)
    if not student:
        return jsonify({"success": False, "message": "Unknown barcode. Student not found.", "student": None})

    success, message = db.mark_attendance(student["student_id"])
    now = datetime.now()
    return jsonify({
        "success": success,
        "message": message,
        "student": {
            "name": student["student_name"],
            "department": student["department"],
            "barcode_id": student["barcode_id"],
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S")
        }
    })


@app.route("/api/students", methods=["GET"])
def api_students():
    """API: Get all students."""
    search = request.args.get("search", "").strip()
    if search:
        students = db.search_students(search)
    else:
        students = db.get_all_students()
    for s in students:
        s["attendance_pct"] = db.get_attendance_percentage(s["student_id"])
    return jsonify({"students": students})


@app.route("/api/delete_student", methods=["POST"])
def api_delete_student():
    """API: Delete a student."""
    data = request.get_json()
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"success": False, "message": "Student ID required."})
    success, message = db.delete_student(student_id)
    return jsonify({"success": success, "message": message})


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """API: Get dashboard stats."""
    students = db.get_all_students()
    today_attendance = db.get_today_attendance()
    all_records = db.get_attendance_records()
    return jsonify({
        "students_count": len(students),
        "today_count": len(today_attendance),
        "total_records": len(all_records)
    })


@app.route("/api/export_attendance", methods=["GET"])
def api_export_attendance():
    """API: Export attendance records as CSV."""
    date_filter = request.args.get("date", "").strip()
    if not date_filter:
        date_filter = None
    records = db.get_attendance_records(date_filter=date_filter)

    if not records:
        return jsonify({"success": False, "message": "No records to export."})

    si = io.StringIO()
    fieldnames = ["attendance_id", "student_id", "student_name", "department", "barcode_id", "date", "time", "status"]
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        writer.writerow(record)

    output = io.BytesIO()
    output.write(si.getvalue().encode("utf-8"))
    output.seek(0)

    filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("=" * 60)
    print("  Smart Barcode Attendance System - Web Server")
    print("=" * 60)
    print(f"  Running at: http://localhost:{port}")
    print(f"  Dashboard:  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop the server")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)

