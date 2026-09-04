"""
Vercel Serverless Function Entrypoint
Routes all requests to the Flask application.
"""
import os
import sys

# Ensure both project root and smart_barcode_attendance are in Python sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMART_APP_DIR = os.path.join(BASE_DIR, "smart_barcode_attendance")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if SMART_APP_DIR not in sys.path:
    sys.path.insert(0, SMART_APP_DIR)

from smart_barcode_attendance.app import app

# Expose app for Vercel WSGI serverless runtime
# In Vercel, any Python file with an `app` or `handler` is executed as WSGI/ASGI
