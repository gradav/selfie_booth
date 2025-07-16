#!/usr/bin/env python3
"""
Configuration module for Selfie Booth application
Handles application configuration and environment setup for both local and web hosting
"""

import os
import secrets
from flask import Flask


class Config:
    """Application configuration class - unified for local dev and web hosting"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database configuration (auto-detect SQLite vs MySQL)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'selfie_booth.db')  # SQLite file for local, DB name for MySQL
    DB_USER = os.environ.get('DB_USER', 'test')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'test')
    DB_PORT = int(os.environ.get('DB_PORT', '3306'))
    DB_TYPE = os.environ.get('DB_TYPE', 'auto')  # auto, sqlite, mysql
    
    # Legacy SQLite path for backwards compatibility
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'selfie_booth.db')
    
    # Messaging configuration
    MESSAGING_SERVICE = os.environ.get('MESSAGING_SERVICE', 'local')  # local, twilio, email
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
    
    # Email configuration
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', '587'))
    
    # Application settings
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5001'))
    
    @classmethod
    def detect_database_type(cls):
        """Auto-detect database type based on environment"""
        if cls.DB_TYPE != 'auto':
            return cls.DB_TYPE
        
        # If we have MySQL environment variables, use MySQL
        if cls.DB_HOST != 'localhost' or cls.DB_USER != 'test':
            return 'mysql'
        
        # Check if running in common web hosting environments
        hosting_indicators = [
            'CPANEL',
            'SHARED_HOSTING',
            '/home/',  # Common in shared hosting paths
            'inmotionhosting.com'
        ]
        
        for indicator in hosting_indicators:
            if indicator in os.environ.get('PWD', '') or indicator in os.environ.get('SERVER_NAME', ''):
                return 'mysql'
        
        # Default to SQLite for local development
        return 'sqlite'
    
    @classmethod
    def get_tablet_mapping(cls):
        """Get tablet ID to short URL mapping"""
        return {
            'TABLET1': '1',
            'TABLET2': '2', 
            'TABLET3': '3',
            'TABLET4': '4',
            'f4d1e4b5': '1',  # Test tablet
        }
    
    @classmethod
    def get_short_url_for_tablet(cls, tablet_id, base_url):
        """Map tablet IDs to short URLs"""
        tablet_mapping = cls.get_tablet_mapping()
        short_path = tablet_mapping.get(tablet_id, '1')  # Default to '1'
        return f"{base_url}/selfie_booth/{short_path}"
    
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
        
        # Check database configuration for MySQL
        db_type = cls.detect_database_type()
        if db_type == 'mysql':
            if not cls.DB_HOST or cls.DB_HOST == 'localhost':
                messages.append("⚠️ DB_HOST should be set for MySQL")
            if not cls.DB_NAME or cls.DB_NAME == 'selfie_booth.db':
                messages.append("⚠️ DB_NAME should be set for MySQL database")
            if cls.DB_USER == 'test':
                messages.append("⚠️ DB_USER should be set for MySQL")
            if cls.DB_PASSWORD == 'test':
                messages.append("⚠️ DB_PASSWORD should be set for MySQL")
        
        if messages:
            print("Configuration warnings:")
            for msg in messages:
                print(f"  {msg}")
            print()
        
        return len(messages) == 0


def add_security_headers(app):
    """Add security headers appropriate for web hosting"""
    @app.after_request
    def security_headers(response):
        # Always add basic security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add stricter headers in production
        if not app.debug:
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Changed from DENY for web hosting
            response.headers['Content-Security-Policy'] = (
                "default-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "media-src 'self' blob:; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "connect-src 'self';"
            )
        
        return response
    
    return app


def create_app():
    """Create and configure Flask application with proper settings for web hosting"""
    app = Flask(__name__)
    
    # Apply configuration
    config = Config()
    app.secret_key = config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # Ensure upload directory exists
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    
    # Add security headers
    app = add_security_headers(app)
    
    # Add configuration to app context
    app.config_class = config
    
    return app


def print_startup_info():
    """Print application startup information"""
    config = Config()
    db_type = config.detect_database_type()
    
    print("🚀 Selfie Booth Starting...")
    print(f"📊 Database: {db_type.upper()}")
    
    if db_type == 'mysql':
        print(f"🔗 MySQL Host: {config.DB_HOST}")
        print(f"🗄️ Database: {config.DB_NAME}")
    else:
        print(f"📁 SQLite File: {config.DATABASE_PATH}")
    
    if not config.DEBUG:
        print("🔒 Running in PRODUCTION mode")
        print("🔐 Security headers enabled")
        print("⚡ Rate limiting active")
        print("🛡️ Input validation enabled")
    else:
        print("🔧 Running in DEBUG mode")
    
    print("📱 Messaging Service Configuration:")
    print(f"   Current: {config.MESSAGING_SERVICE}")
    print("   Options:")
    print("   - local (default) - saves photos locally")
    print("   - twilio - sends via SMS (requires Twilio credentials)")
    print("   - email - sends via email (requires email credentials)")
    
    print("\n🌐 URLs:")
    print(f"   - Kiosk Display: http://localhost:{config.PORT}/")
    print(f"   - Mobile Registration: http://localhost:{config.PORT}/mobile")
    print(f"   - Admin Panel: http://localhost:{config.PORT}/admin")
    
    print("\n📋 Tablet Short URLs:")
    tablet_mapping = config.get_tablet_mapping()
    for tablet_id, short_path in tablet_mapping.items():
        print(f"   - {tablet_id}: /{short_path}")
    
    print(f"\n🔧 Environment: {os.environ.get('PWD', 'Unknown')}")
    print()


def get_config():
    """Get configuration object"""
    return Config