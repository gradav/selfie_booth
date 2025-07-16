#!/usr/bin/env python3
"""
WSGI entry point for InMotion Hosting - Fixed for modular structure
"""

import os
import sys

# Add current directory to Python path for web hosting
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Import the modular app directly
    from app import app as application
    
    print("✅ Modular Selfie Booth WSGI Application Loaded Successfully")
    print(f"📁 Working Directory: {os.getcwd()}")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    
    # Fallback to simple Flask app for debugging
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>Selfie Booth - Import Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Working Directory:</strong> {os.getcwd()}</p>
        <p><strong>Python Path:</strong> {sys.path[0]}</p>
        <p><strong>Available Files:</strong> {', '.join(os.listdir('.'))}</p>
        <p>Check that all required modules are present and properly configured.</p>
        """

except Exception as e:
    print(f"❌ Application Error: {e}")
    
    # Fallback error application
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>Selfie Booth - Application Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>Type:</strong> {type(e).__name__}</p>
        <p>Check your environment variables and database configuration.</p>
        <pre>{str(e)}</pre>
        """

if __name__ == '__main__':
    print("⚠️ Running WSGI file directly - this should not happen in production")
    application.run(debug=True, port=5000)