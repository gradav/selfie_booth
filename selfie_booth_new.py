#!/usr/bin/env python3
"""
Selfie Booth Application - Modular Version
A web-based selfie booth that validates users and sends photos via SMS/email
"""

from config import create_app, get_config, print_startup_info
from database import SessionManager
from routes import create_routes


def main():
    """Main application entry point"""
    # Get configuration
    config = get_config()
    
    # Validate configuration
    config.validate_configuration()
    
    # Create Flask app
    app = create_app()
    
    # Create session manager
    session_manager = SessionManager(config.DATABASE_PATH)
    
    # Create routes
    create_routes(app, session_manager, config.UPLOAD_FOLDER)
    
    # Print startup information
    print_startup_info()
    
    # Run the application
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )


if __name__ == '__main__':
    main()