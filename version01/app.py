#!/usr/bin/env python3
"""
Selfie Booth - Fixed Modular Application
Works like the original but with proper modular structure
"""

import os
import sys

# Add current directory to Python path for InMotion hosting
sys.path.insert(0, os.path.dirname(__file__))

# Import configuration
from config import get_config, create_app as create_base_app

# Import database
from database import CloudSessionManager

# Import messaging
from messaging import MessagingServiceFactory

# Create Flask app
app = create_base_app()

# Initialize configuration
config = get_config()

# Initialize database manager
try:
    if config.detect_database_type() == 'mysql':
        session_manager = CloudSessionManager(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            port=config.DB_PORT
        )
        print("✅ Using MySQL CloudSessionManager")
    else:
        from database import SessionManager
        session_manager = SessionManager(config.DATABASE_PATH)
        print("✅ Using SQLite SessionManager")
except Exception as e:
    print(f"❌ Database manager initialization failed: {e}")
    from database import SessionManager
    session_manager = SessionManager('fallback.db')
    print("🔄 Using fallback SQLite database")

# Initialize messaging factory
messaging_factory = MessagingServiceFactory()

# Store managers in app context
app.session_manager = session_manager
app.messaging_factory = messaging_factory

# Import and register routes (this is the key difference)
from routes import register_routes
register_routes(app, session_manager, messaging_factory, config.UPLOAD_FOLDER)

print("🎉 Modular application initialized successfully!")

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)