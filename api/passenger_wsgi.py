#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python
"""
WSGI entry point for InMotion Hosting with Passenger
Fixed version - no undefined variables
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize application as None
application = None

try:
    # Import the Flask application
    from app import app
    
    # Set the application object for Passenger
    application = app
    
    # Configure for production
    application.config['DEBUG'] = False
    application.config['ENV'] = 'production'
    
    # Success - we have a Flask app
    print(f"✅ WSGI: Flask app loaded successfully", file=sys.stderr)

except ImportError as import_error:
    # Create a detailed error application for import issues
    print(f"❌ WSGI Import Error: {import_error}", file=sys.stderr)
    
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        ]
        start_response(status, headers)
        
        import json
        error_response = json.dumps({
            'success': False,
            'error': f'Import Error: {str(import_error)}',
            'error_type': 'ImportError',
            'debug': {
                'python_executable': sys.executable,
                'current_dir': current_dir,
                'files_in_dir': os.listdir(current_dir),
                'message': 'Flask or app.py could not be imported'
            }
        }, indent=2)
        
        return [error_response.encode('utf-8')]

except Exception as general_error:
    # Create an error application for any other issues
    print(f"❌ WSGI General Error: {general_error}", file=sys.stderr)
    
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*')
        ]
        start_response(status, headers)
        
        import json
        error_response = json.dumps({
            'success': False,
            'error': f'WSGI Error: {str(general_error)}',
            'error_type': type(general_error).__name__,
            'debug': {
                'python_executable': sys.executable,
                'current_dir': current_dir
            }
        }, indent=2)
        
        return [error_response.encode('utf-8')]

# Final safety check
if application is None:
    print(f"❌ WSGI: No application object defined", file=sys.stderr)
    
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'WSGI application object not properly defined']