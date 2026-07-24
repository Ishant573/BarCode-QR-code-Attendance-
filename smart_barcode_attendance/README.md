# Smart Barcode Attendance System

A professional Python-based attendance management system that uses a webcam to scan barcodes and QR codes to automatically mark student attendance.

## Features

- **Real-time Barcode/QR Code Scanning** - Uses webcam to detect and decode barcodes
- **Automatic Attendance Marking** - Identifies registered students and marks attendance
- **Duplicate Detection** - Prevents multiple attendance entries for the same student per day
- **Student Registration** - Register new students with their barcode/QR code IDs
- **Search Functionality** - Search students by name, department, or barcode ID
- **Attendance Reports** - View and export attendance records by date
- **CSV Export** - Export attendance records and student lists to CSV
- **Dashboard** - Statistics overview with total students, today's attendance, and total records
- **Green Box Detection** - Visual feedback with green bounding box around detected barcodes

## Requirements

- Python 3.7+
- Webcam
- Libraries: OpenCV, Tkinter, SQLite3, Pandas, Pyzbar, Pillow

## Installation

1. Clone or download this repository.

2. Install the required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install opencv-python pandas pyzbar Pillow numpy
```

## Usage

Launch the application:

```bash
python3 main.py
```

Or use the launcher:

```bash
./start.sh
```

If you are using a macOS terminal, this also works:

```bash
export TK_SILENCE_DEPRECATION=1
python3 main.py
```

### Steps to Use

1. **Register Students**: Go to the "Registration" tab and add students with their barcode/QR code IDs.
2. **Start Scanner**: Go to the "Scanner" tab and click "Start Scanner" to activate the webcam.
3. **Scan Barcodes**: Hold a barcode or QR code up to the camera. The system will automatically detect and mark attendance.
4. **View Records**: Check the "Attendance" tab to see all attendance records.
5. **Export Reports**: Use the "Export CSV" buttons to download attendance reports.

## Project Structure

```
smart_barcode_attendance/
├── main.py                 # Main entry point
├── run.py                  # Launcher script
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── database/
│   ├── __init__.py
│   └── db_manager.py       # SQLite database operations
├── scanner/
│   ├── __init__.py
│   └── barcode_scanner.py  # Webcam barcode scanning
├── ui/
│   ├── __init__.py
│   └── main_window.py      # Tkinter GUI
└── utils/
    ├── __init__.py
    └── csv_exporter.py     # CSV export functionality
```

## Database

The system uses SQLite with two main tables:

- **students**: Stores student information (ID, name, department, barcode ID)
- **attendance**: Stores attendance records (student ID, date, time, status)

## Troubleshooting

- **Camera not working**: Ensure your webcam is connected and not being used by another application.
- **Barcode not detected**: Ensure adequate lighting and hold the barcode steady and flat to the camera.
- **pyzbar errors on Windows**: You may need to install the ZBar library separately.

## License

This project is open source and available for educational and professional use.

