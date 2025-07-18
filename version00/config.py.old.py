#!/usr/bin/env python3
"""
Configuration module for Selfie Booth application - WITH SECURITY ENHANCEMENTS
Handles application configuration and environment setup
"""

import os
import secrets
from flask import Flask


class Config:
    """Application configuration class"""
    
    # Flask configuration
    SECRET_KEY = secrets.token_hex(16)
    UPLOAD_FOLDER = 'photos'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database configuration
    DATABASE_PATH = 'selfie_booth.db'
    
    # Messaging configuration
    MESSAGING_SERVICE = os.getenv('MESSAGING_SERVICE', 'local')  # local, twilio, email
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
    
    # Email configuration
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    
    # Application settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5001'))
    
    @classmethod
    def validate_configuration(cls):
        """Validate configuration and print warnings for missing settings"""
        messages = []
        
        # Check messaging service configuration
        if cls.MESSAGING_SERVICE == 'twilio':
            if not cls.TWILIO_ACCOUNT_SID:
                messages.append("⚠️ TWILIO_ACCOUNT_SID not set")
            if not cls.TWILIO_AUTH_TOKEN:
                messages.append("⚠️ TWILIO_AUTH_TOKEN not set")
            if not cls.TWILIO_FROM_NUMBER:
                messages.append("⚠️ TWILIO_FROM_NUMBER not set")
        
        elif cls.MESSAGING_SERVICE == 'email':
            if not cls.EMAIL_ADDRESS:
                messages.append("⚠️ EMAIL_ADDRESS not set")
            if not cls.EMAIL_PASSWORD:
                messages.append("⚠️ EMAIL_PASSWORD not set")
        
        if messages:
            print("Configuration warnings:")
            for msg in messages:
                print(f"  {msg}")
            print()
        
        return len(messages) == 0


def add_security_headers(app):
    """Add basic security headers"""
    @app.after_request
    def security_headers(response):
        if not app.debug:  # Only in production
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:;"
        return response
    return app


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Apply configuration
    app.secret_key = Config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Add security headers
    app = add_security_headers(app)
    
    return app


def print_startup_info():
    """Print application startup information"""
    print("🚀 Selfie Booth Starting...")
    
    if not Config.DEBUG:
        print("🔒 Running in PRODUCTION mode")
        print("🔐 Security headers enabled")
        print("⚡ Rate limiting active")
        print("🛡️ Input validation enabled")
    else:
        print("🔧 Running in DEBUG mode")
    
    print("📱 Set MESSAGING_SERVICE environment variable to switch platforms:")
    print("   - local (default) - saves photos locally")
    print("   - twilio - sends via SMS (requires Twilio credentials)")
    print("   - email - sends via email (requires email credentials)")
    print("\n🌐 URLs:")
    print(f"   - Kiosk Display: http://localhost:{Config.PORT}/ (connect monitor/TV here)")
    print(f"   - Mobile Registration: http://localhost:{Config.PORT}/mobile (for QR code)")
    print(f"   - Admin Config: http://localhost:{Config.PORT}/admin/config")
    print(f"\n📋 Create QR code pointing to: http://localhost:{Config.PORT}/mobile")
    print("\n🔧 Debug: Check admin panel for session status")
    print()


def get_config():
    """Get configuration object"""
    return Config