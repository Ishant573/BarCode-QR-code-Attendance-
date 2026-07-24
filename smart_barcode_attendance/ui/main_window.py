"""
Main Window Module
Provides the primary GUI for the Smart Barcode Attendance System using Tkinter.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
import threading
from datetime import datetime
import os
import cv2
from PIL import Image, ImageTk

from database.db_manager import DatabaseManager
from scanner.barcode_scanner import BarcodeScanner
from utils.csv_exporter import CSVExporter


class SmartBarcodeAttendanceSystem:
    """
    Main application class for the Smart Barcode Attendance System.
    Provides a professional GUI with dashboard, scanner, registration, and reporting.
    """

    # Color scheme
    COLORS = {
        "primary": "#2c3e50",
        "secondary": "#3498db",
        "success": "#27ae60",
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "light": "#ecf0f1",
        "dark": "#2c3e50",
        "white": "#ffffff",
        "bg": "#f5f6fa",
        "card": "#ffffff",
        "text": "#2c3e50",
        "text_light": "#7f8c8d",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Barcode Attendance System")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 600)
        self.root.configure(bg=self.COLORS["bg"])

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.db = DatabaseManager()
        self.scanner = BarcodeScanner()
        self.scanner.set_callback(self.on_barcode_detected)
        self.is_scanner_running = False
        self.video_thread = None
        self.video_running = False
        self.current_frame = None

        self.setup_styles()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        print("[App] Smart Barcode Attendance System initialized.")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        bg = self.COLORS["bg"]
        primary = self.COLORS["primary"]
        secondary = self.COLORS["secondary"]
        white = self.COLORS["white"]
        text_color = self.COLORS["text"]
        light = self.COLORS["light"]

        # Use system-appropriate fonts (macOS doesn't have Segoe UI)
        default_font_family = "Helvetica" if sys.platform == "darwin" else "Segoe UI"

        style.configure(".", background=bg, foreground=text_color, font=(default_font_family, 10))
        style.configure("Treeview", background=white, foreground=text_color, rowheight=30, fieldbackground=white, font=(default_font_family, 10))
        style.configure("Treeview.Heading", background=primary, foreground=white, font=(default_font_family, 10, "bold"), relief="flat")
        style.map("Treeview.Heading", background=[("active", secondary)])
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=light, foreground=text_color, padding=[15, 5], font=(default_font_family, 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", white)], foreground=[("selected", primary)])
        style.configure("Primary.TButton", background=secondary, foreground=white, font=(default_font_family, 10, "bold"), padding=[15, 8], borderwidth=0, focuscolor="none")
        style.map("Primary.TButton", background=[("active", "#2980b9")])
        style.configure("Success.TButton", background=self.COLORS["success"], foreground=white, font=(default_font_family, 10, "bold"), padding=[15, 8], borderwidth=0, focuscolor="none")
        style.map("Success.TButton", background=[("active", "#219a52")])
        style.configure("Danger.TButton", background=self.COLORS["danger"], foreground=white, font=(default_font_family, 10, "bold"), padding=[15, 8], borderwidth=0, focuscolor="none")
        style.map("Danger.TButton", background=[("active", "#c0392b")])
        style.configure("Header.TLabel", font=(default_font_family, 16, "bold"), foreground=primary)
        style.configure("Card.TLabel", background=white, foreground=text_color, font=(default_font_family, 10))
        style.configure("Card.TFrame", background=white, relief="solid", borderwidth=1)

    def create_widgets(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.create_header()
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.create_dashboard_tab()
        self.create_scanner_tab()
        self.create_registration_tab()
        self.create_records_tab()
        self.create_students_tab()

    def create_header(self):
        header_frame = tk.Frame(self.main_container, bg=self.COLORS["primary"], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="\U0001f4cb  Smart Barcode Attendance System", font=("Segoe UI", 16, "bold"), bg=self.COLORS["primary"], fg=self.COLORS["white"], anchor="w").pack(side=tk.LEFT, padx=20, pady=10)
        self.datetime_label = tk.Label(header_frame, text="", font=("Segoe UI", 11), bg=self.COLORS["primary"], fg=self.COLORS["light"], anchor="e")
        self.datetime_label.pack(side=tk.RIGHT, padx=20, pady=10)
        self.update_datetime()

    def update_datetime(self):
        now = datetime.now().strftime("%A, %Y-%m-%d  %H:%M:%S")
        self.datetime_label.config(text=now)
        self.root.after(1000, self.update_datetime)

    # ==================== DASHBOARD TAB ====================
    def create_dashboard_tab(self):
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="  \U0001f4ca Dashboard  ")
        welcome_frame = tk.Frame(dashboard_frame, bg=self.COLORS["white"], highlightbackground=self.COLORS["light"], highlightthickness=1)
        welcome_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Label(welcome_frame, text="Welcome to Smart Barcode Attendance System", font=("Segoe UI", 18, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(padx=20, pady=(15, 5))
        tk.Label(welcome_frame, text="Scan barcodes/QR codes to automatically mark attendance. Use the tabs below to manage the system.", font=("Segoe UI", 11), bg=self.COLORS["white"], fg=self.COLORS["text_light"]).pack(padx=20, pady=(0, 15))
        stats_frame = tk.Frame(dashboard_frame, bg=self.COLORS["bg"])
        stats_frame.pack(fill=tk.X, pady=5)
        card_width, card_height = 280, 120
        self.create_stat_card(stats_frame, "\U0001f465 Total Students", "students_count", "0", self.COLORS["secondary"], card_width, card_height).pack(side=tk.LEFT, padx=10, pady=10, expand=True)
        self.create_stat_card(stats_frame, "\U0001f4c5 Today's Attendance", "today_count", "0", self.COLORS["success"], card_width, card_height).pack(side=tk.LEFT, padx=10, pady=10, expand=True)
        self.create_stat_card(stats_frame, "\U0001f4c8 Total Records", "total_records", "0", self.COLORS["warning"], card_width, card_height).pack(side=tk.LEFT, padx=10, pady=10, expand=True)
        actions_frame = tk.Frame(dashboard_frame, bg=self.COLORS["white"], highlightbackground=self.COLORS["light"], highlightthickness=1)
        actions_frame.pack(fill=tk.X, pady=(15, 0))
        tk.Label(actions_frame, text="Quick Actions", font=("Segoe UI", 14, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(padx=20, pady=(15, 5))
        actions_buttons = tk.Frame(actions_frame, bg=self.COLORS["white"])
        actions_buttons.pack(padx=20, pady=(10, 15))
        ttk.Button(actions_buttons, text="\u25b6 Start Scanner", style="Success.TButton", command=self.start_scanner).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_buttons, text="\u25a0 Stop Scanner", style="Danger.TButton", command=self.stop_scanner).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_buttons, text="\u2795 Register Student", style="Primary.TButton", command=lambda: self.notebook.select(2)).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_buttons, text="\U0001f4c4 Export Today", style="Primary.TButton", command=self.export_today_attendance).pack(side=tk.LEFT, padx=5)
        self.refresh_dashboard()

    def create_stat_card(self, parent, title, attr_name, initial_value, color, width, height):
        card = tk.Frame(parent, bg=self.COLORS["white"], highlightbackground=color, highlightthickness=3, width=width, height=height)
        card.pack_propagate(False)
        tk.Label(card, text=title, font=("Segoe UI", 11), bg=self.COLORS["white"], fg=self.COLORS["text_light"]).pack(padx=15, pady=(15, 0), anchor="w")
        value_label = tk.Label(card, text=initial_value, font=("Segoe UI", 28, "bold"), bg=self.COLORS["white"], fg=color)
        value_label.pack(padx=15, pady=(0, 10), anchor="w")
        setattr(self, attr_name, value_label)
        return card

    def refresh_dashboard(self):
        try:
            students = self.db.get_all_students()
            today = self.db.get_today_attendance()
            all_records = self.db.get_attendance_records()
            if hasattr(self, 'students_count'):
                self.students_count.config(text=str(len(students)))
            if hasattr(self, 'today_count'):
                self.today_count.config(text=str(len(today)))
            if hasattr(self, 'total_records'):
                self.total_records.config(text=str(len(all_records)))
        except Exception as e:
            print(f"[Dashboard] Error refreshing: {e}")
        self.root.after(10000, self.refresh_dashboard)

    # ==================== ENHANCED SCANNER TAB ====================
    def create_scanner_tab(self):
        """Create the scanner tab with an enhanced, user-friendly barcode scanning interface."""
        self.scanner_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scanner_frame, text="  \U0001f4f7 Scanner  ")

        # ====== TOP CONTROLS BAR ======
        top_bar = tk.Frame(self.scanner_frame, bg=self.COLORS["primary"], height=50)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text="\U0001f4f7  Barcode / QR Code Scanner", font=("Segoe UI", 14, "bold"), bg=self.COLORS["primary"], fg=self.COLORS["white"]).pack(side=tk.LEFT, padx=20, pady=10)
        self.scanner_status_badge = tk.Label(top_bar, text="\U0001f534 STOPPED", font=("Segoe UI", 11, "bold"), bg="#c0392b", fg=self.COLORS["white"], padx=15, pady=5)
        self.scanner_status_badge.pack(side=tk.RIGHT, padx=20, pady=8)

        # ====== MAIN CONTENT ======
        scanner_content = tk.Frame(self.scanner_frame, bg=self.COLORS["bg"])
        scanner_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ====== LEFT SIDE - ENHANCED CAMERA FEED ======
        camera_section = tk.Frame(scanner_content, bg=self.COLORS["dark"], highlightbackground=self.COLORS["secondary"], highlightthickness=2)
        camera_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        cam_header = tk.Frame(camera_section, bg="#1a1a2e")
        cam_header.pack(fill=tk.X)
        tk.Label(cam_header, text="\U0001f4f9 Live Camera Feed", font=("Segoe UI", 11, "bold"), bg="#1a1a2e", fg=self.COLORS["white"]).pack(side=tk.LEFT, padx=15, pady=8)
        self.res_indicator = tk.Label(cam_header, text="640x480", font=("Segoe UI", 9), bg="#1a1a2e", fg=self.COLORS["text_light"])
        self.res_indicator.pack(side=tk.RIGHT, padx=15, pady=8)

        # Camera display
        self.camera_label = tk.Label(camera_section, bg="#0a0a1a", text="", font=("Segoe UI", 16), fg=self.COLORS["light"])
        self.camera_label.pack(fill=tk.BOTH, expand=True)

        # Scanner overlay instructions
        self.scanner_overlay = tk.Frame(self.camera_label, bg="#0a0a1a")
        self.scanner_overlay.place(relx=0.5, rely=0.5, anchor="center")
        self.overlay_icon = tk.Label(self.scanner_overlay, text="\U0001f4f7", font=("Segoe UI", 48), bg="#0a0a1a", fg=self.COLORS["text_light"])
        self.overlay_icon.pack()
        self.overlay_text = tk.Label(self.scanner_overlay, text="Camera Not Active", font=("Segoe UI", 18, "bold"), bg="#0a0a1a", fg=self.COLORS["text_light"])
        self.overlay_text.pack(pady=(5, 2))
        self.overlay_subtext = tk.Label(self.scanner_overlay, text="Click the Start Scanner button below to begin", font=("Segoe UI", 11), bg="#0a0a1a", fg=self.COLORS["text_light"])
        self.overlay_subtext.pack(pady=(0, 10))

        # Scan guide frame
        self.scan_guide = tk.Frame(self.camera_label, highlightbackground=self.COLORS["secondary"], highlightthickness=2, width=300, height=200, bg="")

        # Camera controls
        cam_controls = tk.Frame(camera_section, bg="#1a1a2e")
        cam_controls.pack(fill=tk.X, pady=0)
        btn_row = tk.Frame(cam_controls, bg="#1a1a2e")
        btn_row.pack(pady=10)

        self.start_btn = tk.Button(btn_row, text="\u25b6  START SCANNER", font=("Segoe UI", 11, "bold"), bg=self.COLORS["success"], fg=self.COLORS["white"], padx=25, pady=10, bd=0, cursor="hand2", activebackground="#219a52", activeforeground="white", command=self.start_scanner)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(btn_row, text="\u25a0  STOP SCANNER", font=("Segoe UI", 11, "bold"), bg=self.COLORS["danger"], fg=self.COLORS["white"], padx=25, pady=10, bd=0, cursor="hand2", activebackground="#c0392b", activeforeground="white", command=self.stop_scanner, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="\U0001f5bc  Show Scan Guide", font=("Segoe UI", 10), bg="#34495e", fg=self.COLORS["white"], padx=15, pady=10, bd=0, cursor="hand2", activebackground="#2c3e50", activeforeground="white", command=self.toggle_scan_guide).pack(side=tk.LEFT, padx=5)

        # ====== RIGHT SIDE - ENHANCED RESULTS PANEL ======
        results_panel = tk.Frame(scanner_content, bg=self.COLORS["white"], width=380, highlightbackground=self.COLORS["light"], highlightthickness=1)
        results_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        results_panel.pack_propagate(False)

        # Scrollable results
        results_canvas = tk.Canvas(results_panel, bg=self.COLORS["white"], highlightthickness=0)
        results_scrollbar = ttk.Scrollbar(results_panel, orient="vertical", command=results_canvas.yview)
        self.results_scrollable = tk.Frame(results_canvas, bg=self.COLORS["white"])
        self.results_scrollable.bind("<Configure>", lambda e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))
        results_canvas.create_window((0, 0), window=self.results_scrollable, anchor="nw")
        results_canvas.configure(yscrollcommand=results_scrollbar.set)
        results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Scan Result Section
        result_header = tk.Frame(self.results_scrollable, bg=self.COLORS["white"])
        result_header.pack(fill=tk.X, padx=15, pady=(15, 5))
        tk.Label(result_header, text="\U0001f4cb  Scan Result", font=("Segoe UI", 15, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(anchor="w")

        # Big status icon
        self.result_icon_frame = tk.Frame(self.results_scrollable, bg=self.COLORS["light"], width=80, height=80, highlightbackground=self.COLORS["secondary"], highlightthickness=2)
        self.result_icon_frame.pack(pady=(10, 5))
        self.result_icon_frame.pack_propagate(False)
        self.result_icon = tk.Label(self.result_icon_frame, text="\u23f3", font=("Segoe UI", 36), bg=self.COLORS["light"], fg=self.COLORS["text_light"])
        self.result_icon.place(relx=0.5, rely=0.5, anchor="center")

        # Result banner
        self.result_banner = tk.Label(self.results_scrollable, text="Waiting for scan...", font=("Segoe UI", 14, "bold"), bg=self.COLORS["light"], fg=self.COLORS["text_light"], padx=20, pady=12)
        self.result_banner.pack(fill=tk.X, padx=15, pady=5)

        # Student Details Card
        details_card = tk.Frame(self.results_scrollable, bg=self.COLORS["bg"], highlightbackground=self.COLORS["light"], highlightthickness=1)
        details_card.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(details_card, text="\U0001f464 Student Details", font=("Segoe UI", 12, "bold"), bg=self.COLORS["bg"], fg=self.COLORS["primary"]).pack(padx=15, pady=(10, 5), anchor="w")

        self.info_labels = {}
        info_fields = [
            ("barcode_id", "\U0001f511 Barcode ID", "---"),
            ("student_name", "\U0001f464 Name", "---"),
            ("department", "\U0001f3eb Department", "---"),
            ("date", "\U0001f4c5 Date", "---"),
            ("time", "\u23f0 Time", "---"),
            ("status", "\u2705 Status", "---"),
        ]
        for key, label, default in info_fields:
            field_row = tk.Frame(details_card, bg=self.COLORS["bg"])
            field_row.pack(fill=tk.X, padx=15, pady=3)
            tk.Label(field_row, text=label, font=("Segoe UI", 9, "bold"), bg=self.COLORS["bg"], fg=self.COLORS["text_light"], width=13, anchor="w").pack(side=tk.LEFT)
            value_lbl = tk.Label(field_row, text=default, font=("Segoe UI", 10), bg=self.COLORS["bg"], fg=self.COLORS["text"], anchor="w")
            value_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.info_labels[key] = value_lbl

        # Manual Barcode Entry
        manual_frame = tk.Frame(self.results_scrollable, bg=self.COLORS["white"])
        manual_frame.pack(fill=tk.X, padx=15, pady=(10, 5))
        tk.Label(manual_frame, text="\u2328\ufe0f  Manual Entry (if scan fails)", font=("Segoe UI", 11, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(anchor="w")
        manual_entry_row = tk.Frame(self.results_scrollable, bg=self.COLORS["white"])
        manual_entry_row.pack(fill=tk.X, padx=15, pady=(0, 10))
        self.manual_barcode_entry = tk.Entry(manual_entry_row, font=("Segoe UI", 12), relief="solid", borderwidth=1, bg=self.COLORS["light"])
        self.manual_barcode_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 5))
        self.manual_barcode_entry.bind("<Return>", lambda e: self.process_manual_barcode())
        tk.Button(manual_entry_row, text="Submit", font=("Segoe UI", 10, "bold"), bg=self.COLORS["secondary"], fg=self.COLORS["white"], padx=15, pady=6, bd=0, cursor="hand2", activebackground="#2980b9", activeforeground="white", command=self.process_manual_barcode).pack(side=tk.RIGHT)

        # Scan Log
        log_header = tk.Frame(self.results_scrollable, bg=self.COLORS["white"])
        log_header.pack(fill=tk.X, padx=15, pady=(10, 2))
        tk.Label(log_header, text="\U0001f4dd  Recent Scans", font=("Segoe UI", 11, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(anchor="w")
        log_container = tk.Frame(self.results_scrollable, bg=self.COLORS["white"])
        log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.scan_log = tk.Text(log_container, height=6, font=("Segoe UI", 9), bg=self.COLORS["bg"], fg=self.COLORS["text"], relief="flat", state=tk.DISABLED, bd=0)
        self.scan_log.pack(fill=tk.BOTH, expand=True)
        tk.Frame(self.results_scrollable, bg=self.COLORS["white"], height=20).pack(fill=tk.X)

    def toggle_scan_guide(self):
        """Toggle the scan guide overlay on the camera feed."""
        if hasattr(self, 'scan_guide_visible') and self.scan_guide_visible:
            self.scan_guide.place_forget()
            self.scan_guide_visible = False
        else:
            self.scan_guide.place(relx=0.5, rely=0.5, anchor="center")
            self.scan_guide_visible = True

    def process_manual_barcode(self):
        """Process a manually entered barcode ID."""
        barcode_data = self.manual_barcode_entry.get().strip()
        if barcode_data:
            self._process_detection(barcode_data)
            self.manual_barcode_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Empty Input", "Please enter a barcode ID.")

    def start_scanner(self):
        """Start the barcode scanner with enhanced UI feedback."""
        try:
            self.scanner.start()
            self.is_scanner_running = True
            self.scanner_status_badge.config(text="\U0001f7e2 RUNNING", bg=self.COLORS["success"])
            self.start_btn.config(state=tk.DISABLED, bg="#1a6b34")
            self.stop_btn.config(state=tk.NORMAL, bg=self.COLORS["danger"])
            self.scanner_overlay.place_forget()
            self.overlay_subtext.config(text="Point barcode/QR code at camera...")
            self.video_running = True
            self.video_thread = threading.Thread(target=self.update_video_feed, daemon=True)
            self.video_thread.start()
            self.result_banner.config(text="Scanner active - waiting for barcode...", bg=self.COLORS["light"], fg=self.COLORS["text_light"])
            self.result_icon.config(text="\u23f3")
            self.add_to_log("[System] Scanner started successfully.")
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to start camera:\n{e}\n\nPlease check your webcam connection.")
            self.add_to_log(f"[Error] {e}")

    def stop_scanner(self):
        """Stop the barcode scanner with enhanced UI feedback."""
        self.video_running = False
        self.scanner.stop()
        self.is_scanner_running = False
        self.scanner_status_badge.config(text="\U0001f534 STOPPED", bg="#c0392b")
        self.start_btn.config(state=tk.NORMAL, bg=self.COLORS["success"])
        self.stop_btn.config(state=tk.DISABLED, bg="#7b241c")
        self.scanner_overlay.place(relx=0.5, rely=0.5, anchor="center")
        self.overlay_subtext.config(text="Click the Start Scanner button below to begin")
        self.result_banner.config(text="Scanner stopped", bg=self.COLORS["light"], fg=self.COLORS["text_light"])
        self._clear_camera_image()
        self.add_to_log("[System] Scanner stopped.")

    def update_video_feed(self):
        """Update the video feed in the GUI (runs in a separate thread)."""
        while self.video_running and self.is_scanner_running:
            try:
                frame = self.scanner.get_current_frame()
                if frame is not None:
                    h, w = frame.shape[:2]
                    display_w, display_h = 640, 480
                    scale = min(display_w / w, display_h / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    if new_w > 0 and new_h > 0:
                        frame = cv2.resize(frame, (new_w, new_h))
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.root.after(0, self._update_camera_image, imgtk)
            except Exception as e:
                print(f"[Video Feed] Error: {e}")
        self.root.after(0, self._clear_camera_image)

    def _update_camera_image(self, imgtk):
        self.camera_label.config(image=imgtk, text="")
        self.camera_label.image = imgtk

    def _clear_camera_image(self):
        self.camera_label.config(image="")
        self.camera_label.image = None

    def on_barcode_detected(self, barcode_data):
        self.root.after(0, self._process_detection, barcode_data)

    def _process_detection(self, barcode_data):
        """Process detected barcode with enhanced visual feedback."""
        self.info_labels["barcode_id"].config(text=barcode_data)
        student = self.db.get_student_by_barcode(barcode_data)

        if student:
            self.info_labels["student_name"].config(text=student["student_name"])
            self.info_labels["department"].config(text=student["department"])
            success, message = self.db.mark_attendance(student["student_id"])
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            self.info_labels["date"].config(text=date_str)
            self.info_labels["time"].config(text=time_str)

            if success:
                self.info_labels["status"].config(text="\u2705 Present", fg=self.COLORS["success"])
                self.result_banner.config(text=f"\u2705 {student['student_name']} - PRESENT", bg="#1a6b34", fg=self.COLORS["white"])
                self.result_icon.config(text="\u2705")
                self.result_icon_frame.config(highlightbackground=self.COLORS["success"])
                self.add_to_log(f"[Present] {student['student_name']} - {time_str}")
                self.camera_label.config(bg="#1a6b34")
                self.root.after(300, lambda: self.camera_label.config(bg="#0a0a1a"))
            else:
                self.info_labels["status"].config(text="\u26a0 Duplicate", fg=self.COLORS["warning"])
                self.result_banner.config(text=f"\u26a0 {student['student_name']} - Already Marked Today", bg="#7d6608", fg=self.COLORS["white"])
                self.result_icon.config(text="\u26a0\ufe0f")
                self.result_icon_frame.config(highlightbackground=self.COLORS["warning"])
                self.add_to_log(f"[Duplicate] {student['student_name']} - Already marked today")
                self.camera_label.config(bg="#7d6608")
                self.root.after(300, lambda: self.camera_label.config(bg="#0a0a1a"))
        else:
            self.info_labels["student_name"].config(text="\u26a0 UNREGISTERED")
            self.info_labels["department"].config(text="Not in database")
            self.info_labels["status"].config(text="\u274c Unknown", fg=self.COLORS["danger"])
            now = datetime.now()
            self.info_labels["date"].config(text=now.strftime("%Y-%m-%d"))
            self.info_labels["time"].config(text=now.strftime("%H:%M:%S"))
            self.result_banner.config(text=f"\u274c Unknown Barcode: {barcode_data}", bg="#7b241c", fg=self.COLORS["white"])
            self.result_icon.config(text="\u274c")
            self.result_icon_frame.config(highlightbackground=self.COLORS["danger"])
            self.add_to_log(f"[Unknown] Barcode: {barcode_data}")
            self.camera_label.config(bg="#7b241c")
            self.root.after(300, lambda: self.camera_label.config(bg="#0a0a1a"))

        self.refresh_records_table()
        self.refresh_dashboard()

    def add_to_log(self, message):
        self.scan_log.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.scan_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.scan_log.see(tk.END)
        self.scan_log.config(state=tk.DISABLED)

    # ==================== REGISTRATION TAB ====================
    def create_registration_tab(self):
        reg_frame = ttk.Frame(self.notebook)
        self.notebook.add(reg_frame, text="  \U0001f4dd Registration  ")
        center_frame = tk.Frame(reg_frame, bg=self.COLORS["bg"])
        center_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=30)
        form_card = tk.Frame(center_frame, bg=self.COLORS["white"], highlightbackground=self.COLORS["light"], highlightthickness=1, width=600)
        form_card.pack(padx=20, pady=20)
        form_card.pack_propagate(False)
        tk.Label(form_card, text="\U0001f4dd Register New Student", font=("Segoe UI", 16, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(padx=30, pady=(25, 5))
        tk.Label(form_card, text="Fill in the details below to register a new student", font=("Segoe UI", 10), bg=self.COLORS["white"], fg=self.COLORS["text_light"]).pack(padx=30, pady=(0, 20))
        form_fields = tk.Frame(form_card, bg=self.COLORS["white"])
        form_fields.pack(padx=40, pady=10, fill=tk.X)
        tk.Label(form_fields, text="Student Name *", font=("Segoe UI", 10, "bold"), bg=self.COLORS["white"], fg=self.COLORS["text"], anchor="w").pack(fill=tk.X, pady=(5, 2))
        self.name_entry = tk.Entry(form_fields, font=("Segoe UI", 11), relief="solid", borderwidth=1)
        self.name_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)
        tk.Label(form_fields, text="Department / Course *", font=("Segoe UI", 10, "bold"), bg=self.COLORS["white"], fg=self.COLORS["text"], anchor="w").pack(fill=tk.X, pady=(5, 2))
        self.dept_entry = tk.Entry(form_fields, font=("Segoe UI", 11), relief="solid", borderwidth=1)
        self.dept_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)
        tk.Label(form_fields, text="Barcode/QR Code ID *", font=("Segoe UI", 10, "bold"), bg=self.COLORS["white"], fg=self.COLORS["text"], anchor="w").pack(fill=tk.X, pady=(5, 2))
        barcode_frame = tk.Frame(form_fields, bg=self.COLORS["white"])
        barcode_frame.pack(fill=tk.X, pady=(0, 10))
        self.barcode_entry = tk.Entry(barcode_frame, font=("Segoe UI", 11), relief="solid", borderwidth=1)
        self.barcode_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        button_frame = tk.Frame(form_fields, bg=self.COLORS["white"])
        button_frame.pack(fill=tk.X, pady=(15, 10))
        ttk.Button(button_frame, text="\U0001f4e5 Register Student", style="Success.TButton", command=self.register_student).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="\U0001f5d1 Clear Form", style="Primary.TButton", command=self.clear_registration_form).pack(side=tk.LEFT)
        self.reg_status = tk.Label(form_card, text="", font=("Segoe UI", 11), bg=self.COLORS["white"], fg=self.COLORS["success"], wraplength=500)
        self.reg_status.pack(padx=30, pady=(5, 20))

    def register_student(self):
        name = self.name_entry.get().strip()
        department = self.dept_entry.get().strip()
        barcode_id = self.barcode_entry.get().strip()
        if not name:
            messagebox.showerror("Validation Error", "Please enter student name.")
            return
        if not department:
            messagebox.showerror("Validation Error", "Please enter department/course.")
            return
        if not barcode_id:
            messagebox.showerror("Validation Error", "Please enter barcode/QR code ID.")
            return
        success, message = self.db.add_student(name, department, barcode_id)
        if success:
            self.reg_status.config(text="\u2705 " + message, fg=self.COLORS["success"])
            self.clear_registration_form()
            self.refresh_dashboard()
            self.refresh_students_table()
            messagebox.showinfo("Success", message)
        else:
            self.reg_status.config(text="\u274c " + message, fg=self.COLORS["danger"])
            messagebox.showerror("Registration Error", message)

    def clear_registration_form(self):
        self.name_entry.delete(0, tk.END)
        self.dept_entry.delete(0, tk.END)
        self.barcode_entry.delete(0, tk.END)
        self.reg_status.config(text="")

    # ==================== RECORDS TAB ====================
    def create_records_tab(self):
        records_frame = ttk.Frame(self.notebook)
        self.notebook.add(records_frame, text="  \U0001f4c4 Attendance  ")
        controls_frame = tk.Frame(records_frame, bg=self.COLORS["white"], highlightbackground=self.COLORS["light"], highlightthickness=1)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(controls_frame, text="\U0001f4cb Attendance Records", font=("Segoe UI", 14, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(side=tk.LEFT, padx=20, pady=15)
        filter_frame = tk.Frame(controls_frame, bg=self.COLORS["white"])
        filter_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        tk.Label(filter_frame, text="Filter by Date:", font=("Segoe UI", 10), bg=self.COLORS["white"], fg=self.COLORS["text"]).pack(side=tk.LEFT, padx=5)
        self.date_filter_entry = tk.Entry(filter_frame, width=12, font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.date_filter_entry.pack(side=tk.LEFT, padx=5, ipady=3)
        self.date_filter_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        ttk.Button(filter_frame, text="\U0001f50d Filter", style="Primary.TButton", command=self.refresh_records_table, padding=[10, 5]).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="\U0001f4e4 Export CSV", style="Success.TButton", command=self.export_attendance, padding=[10, 5]).pack(side=tk.LEFT, padx=5)
        table_frame = tk.Frame(records_frame, bg=self.COLORS["white"])
        table_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("#", "Student ID", "Student Name", "Department", "Barcode ID", "Date", "Time", "Status")
        self.records_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.records_tree.heading(col, text=col)
            if col == "#":
                self.records_tree.column(col, width=40, anchor="center")
            elif col in ("Date", "Time", "Status"):
                self.records_tree.column(col, width=100, anchor="center")
            elif col in ("Student ID",):
                self.records_tree.column(col, width=80, anchor="center")
            elif col == "Barcode ID":
                self.records_tree.column(col, width=150, anchor="center")
            elif col == "Department":
                self.records_tree.column(col, width=150)
            else:
                self.records_tree.column(col, width=180)
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.records_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.records_tree.xview)
        self.records_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.records_tree.tag_configure("present", foreground=self.COLORS["success"])
        self.records_tree.tag_configure("duplicate", foreground=self.COLORS["warning"])
        self.refresh_records_table()

    def refresh_records_table(self):
        try:
            for item in self.records_tree.get_children():
                self.records_tree.delete(item)
            date_filter = self.date_filter_entry.get().strip()
            if not date_filter:
                date_filter = None
            records = self.db.get_attendance_records(date_filter=date_filter)
            for i, record in enumerate(records, 1):
                tags = ()
                if record["status"] == "Present":
                    tags = ("present",)
                else:
                    tags = ("duplicate",)
                self.records_tree.insert("", tk.END, values=(i, record["student_id"], record["student_name"], record["department"], record["barcode_id"], record["date"], record["time"], "\u2705 Present" if record["status"] == "Present" else record["status"]), tags=tags)
        except Exception as e:
            print(f"[Records] Error refreshing: {e}")

    # ==================== STUDENTS TAB ====================
    def create_students_tab(self):
        students_frame = ttk.Frame(self.notebook)
        self.notebook.add(students_frame, text="  \U0001f465 Students  ")
        controls_frame = tk.Frame(students_frame, bg=self.COLORS["white"], highlightbackground=self.COLORS["light"], highlightthickness=1)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(controls_frame, text="\U0001f465 Registered Students", font=("Segoe UI", 14, "bold"), bg=self.COLORS["white"], fg=self.COLORS["primary"]).pack(side=tk.LEFT, padx=20, pady=15)
        search_frame = tk.Frame(controls_frame, bg=self.COLORS["white"])
        search_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        tk.Label(search_frame, text="\U0001f50d Search:", font=("Segoe UI", 10), bg=self.COLORS["white"], fg=self.COLORS["text"]).pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=20, font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.search_entry.pack(side=tk.LEFT, padx=5, ipady=3)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_students_table())
        ttk.Button(search_frame, text="\U0001f4e4 Export CSV", style="Success.TButton", command=self.export_students_csv, padding=[10, 5]).pack(side=tk.LEFT, padx=5)
        table_frame = tk.Frame(students_frame, bg=self.COLORS["white"])
        table_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("Student ID", "Student Name", "Department", "Barcode ID", "Attendance %")
        self.students_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.students_tree.heading(col, text=col)
            if col == "Student ID":
                self.students_tree.column(col, width=80, anchor="center")
            elif col == "Attendance %":
                self.students_tree.column(col, width=100, anchor="center")
            elif col == "Barcode ID":
                self.students_tree.column(col, width=150, anchor="center")
            elif col == "Department":
                self.students_tree.column(col, width=200)
            else:
                self.students_tree.column(col, width=200)
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.students_tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.students_tree.xview)
        self.students_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(students_frame, text="\U0001f5d1 Delete Selected Student", style="Danger.TButton", command=self.delete_selected_student).pack(pady=10)
        self.refresh_students_table()

    def refresh_students_table(self):
        try:
            for item in self.students_tree.get_children():
                self.students_tree.delete(item)
            search_term = self.search_entry.get().strip()
            if search_term:
                students = self.db.search_students(search_term)
            else:
                students = self.db.get_all_students()
            for student in students:
                percentage = self.db.get_attendance_percentage(student["student_id"])
                self.students_tree.insert("", tk.END, values=(student["student_id"], student["student_name"], student["department"], student["barcode_id"], f"{percentage:.1f}%"))
        except Exception as e:
            print(f"[Students] Error refreshing: {e}")

    def delete_selected_student(self):
        selected = self.students_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a student to delete.")
            return
        values = self.students_tree.item(selected[0])["values"]
        student_id = values[0]
        student_name = values[1]
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{student_name}'?\nThis will also delete all their attendance records.")
        if confirm:
            success, message = self.db.delete_student(student_id)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
            self.refresh_students_table()
            self.refresh_dashboard()

    # ==================== EXPORT FUNCTIONS ====================
    def export_attendance(self):
        date_filter = self.date_filter_entry.get().strip()
        if not date_filter:
            date_filter = None
        records = self.db.get_attendance_records(date_filter=date_filter)
        success, message, path = CSVExporter.export_attendance(records)
        if success:
            messagebox.showinfo("Export Success", message)
            self.add_to_log(f"[Export] Attendance exported: {path}")
        else:
            messagebox.showerror("Export Error", message)

    def export_today_attendance(self):
        records = self.db.get_today_attendance()
        success, message, path = CSVExporter.export_attendance(records)
        if success:
            messagebox.showinfo("Export Success", message)
        else:
            if "No records" in message:
                messagebox.showinfo("Info", "No attendance records for today to export.")
            else:
                messagebox.showerror("Export Error", message)

    def export_students_csv(self):
        search_term = self.search_entry.get().strip()
        if search_term:
            students = self.db.search_students(search_term)
        else:
            students = self.db.get_all_students()
        success, message, path = CSVExporter.export_students(students)
        if success:
            messagebox.showinfo("Export Success", message)
        else:
            if "No records" in message:
                messagebox.showinfo("Info", "No students to export.")
            else:
                messagebox.showerror("Export Error", message)

    # ==================== CLEANUP ====================
    def on_closing(self):
        if self.is_scanner_running:
            self.stop_scanner()
        self.db.close()
        self.root.destroy()
        print("[App] Application closed.")

