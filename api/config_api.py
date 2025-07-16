#!/usr/bin/env python3
"""
API Configuration for Selfie Booth
Optimized for static frontend + minimal API backend
"""

import os
import secrets


class APIConfig:
    """API-only configuration - no template rendering needed"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    MAX_PHOTO_SIZE = 16 * 1024 * 1024  # 16MB
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'selfie_booth.db')
    DB_USER = os.environ.get('DB_USER', 'test')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'test')
    DB_PORT = int(os.environ.get('DB_PORT', '3306'))
    DB_TYPE = os.environ.get('DB_TYPE', 'auto')
    
    # Messaging configuration
    MESSAGING_SERVICE = os.environ.get('MESSAGING_SERVICE', 'local')
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
    
    # Email configuration
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
    EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', '587'))
    
    # API settings
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5001'))
    
    # CORS settings for static frontend
    ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:8000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8000',
        # Add your production domain here
        # 'https://yourdomain.com'
    ]
    
    # Rate limiting
    ENABLE_RATE_LIMITING = not DEBUG  # Disable in debug mode
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = 30
    VERIFICATION_TIMEOUT_MINUTES = 2
    
    @classmethod
    def detect_database_type(cls):
        """Auto-detect database type"""
        if cls.DB_TYPE != 'auto':
            return cls.DB_TYPE
        
        # Check for MySQL environment indicators
        if (cls.DB_HOST != 'localhost' or 
            cls.DB_USER != 'test' or 
            'mysql' in cls.DB_NAME.lower()):
            return 'mysql'
        
        # Check hosting environment
        hosting_indicators = [
            'CPANEL', 'SHARED_HOSTING', '/home/',
            'inmotionhosting.com', 'hostgator.com'
        ]
        
        for indicator in hosting_indicators:
            if (indicator in os.environ.get('PWD', '') or 
                indicator in os.environ.get('SERVER_NAME', '') or
                indicator in os.environ.get('HTTP_HOST', '')):
                return 'mysql'
        
        return 'sqlite'
    
    @classmethod
    def validate_configuration(cls):
        """Validate configuration and return warnings"""
        warnings = []
        
        # Check messaging service
        if cls.MESSAGING_SERVICE == 'twilio':
            if not cls.TWILIO_ACCOUNT_SID:
                warnings.append('TWILIO_ACCOUNT_SID not set')
            if not cls.TWILIO_AUTH_TOKEN:
                warnings.append('TWILIO_AUTH_TOKEN not set')
            if not cls.TWILIO_FROM_NUMBER:
                warnings.append('TWILIO_FROM_NUMBER not set')
        
        elif cls.MESSAGING_SERVICE == 'email':
            if not cls.EMAIL_ADDRESS:
                warnings.append('EMAIL_ADDRESS not set')
            if not cls.EMAIL_PASSWORD:
                warnings.append('EMAIL_PASSWORD not set')
        
        # Check database for MySQL
        db_type = cls.detect_database_type()
        if db_type == 'mysql':
            if cls.DB_HOST == 'localhost':
                warnings.append('DB_HOST should be set for MySQL')
            if cls.DB_NAME == 'selfie_booth.db':
                warnings.append('DB_NAME should be MySQL database name')
            if cls.DB_USER == 'test':
                warnings.append('DB_USER should be set for production')
            if cls.DB_PASSWORD == 'test':
                warnings.append('DB_PASSWORD should be set for production')
        
        # Production warnings
        if not cls.DEBUG:
            if cls.SECRET_KEY == 'dev-secret-key':
                warnings.append('SECRET_KEY should be set for production')
        
        return warnings
    
    @classmethod
    def print_startup_info(cls):
        """Print startup information"""
        db_type = cls.detect_database_type()
        warnings = cls.validate_configuration()
        
        print("🚀 Selfie Booth API Starting...")
        print(f"📊 Database: {db_type.upper()}")
        
        if db_type == 'mysql':
            print(f"🔗 MySQL Host: {cls.DB_HOST}")
            print(f"🗄️ Database: {cls.DB_NAME}")
        else:
            print(f"📁 SQLite File: {cls.DB_NAME}")
        
        print(f"📱 Messaging: {cls.MESSAGING_SERVICE}")
        print(f"🔧 Debug Mode: {cls.DEBUG}")
        print(f"⚡ Rate Limiting: {cls.ENABLE_RATE_LIMITING}")
        
        if warnings:
            print("\n⚠️ Configuration Warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        print("\n🌐 API Endpoints:")
        print("   - Health Check: /api/health")
        print("   - Registration: /api/register")
        print("   - Verification: /api/verify")
        print("   - Session Check: /api/session_check")
        print("   - Admin Stats: /api/admin/stats")
        
        if cls.DEBUG:
            print("\n🔧 Debug Endpoints:")
            print("   - Debug Info: /api/debug/info")
        
        print()


# Create global config instance
config = APIConfig()

# Auto-print startup info when imported
if __name__ != '__main__':
    config.print_startup_info()