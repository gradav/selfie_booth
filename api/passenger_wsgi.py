#!/usr/bin/env python3
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app_minimal import app as application
    print("✅ WSGI: Minimal Flask application imported successfully")
except ImportError as e:
    print(f"❌ WSGI: Failed to import minimal Flask application: {e}")
    
    # Fallback for debugging
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)
        return [f'<h1>Import Error:</h1><p>{str(e)}</p>'.encode()]