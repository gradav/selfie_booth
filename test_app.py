# test_app.py - Simple test to verify InMotion setup
"""
Upload this simple file first to test your InMotion Python app setup
Before uploading the full selfie booth application
"""

from flask import Flask, jsonify
import os
import sys

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """Simple home page to test basic Flask functionality"""
    return '''
    <html>
    <head><title>InMotion Python Test</title></head>
    <body style="font-family: Arial; padding: 40px; text-align: center;">
        <h1 style="color: #667eea;">🎉 Python App Working!</h1>
        <p>Your InMotion Python setup is working correctly.</p>
        <p><strong>Next steps:</strong></p>
        <ul style="text-align: left; max-width: 400px; margin: 20px auto;">
            <li>✅ Python app is running</li>
            <li>⏳ Test database connection</li>
            <li>⏳ Upload full selfie booth code</li>
            <li>⏳ Configure environment variables</li>
        </ul>
        <div style="margin-top: 30px;">
            <a href="/test-db" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Test Database</a>
            <a href="/info" style="background: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">System Info</a>
        </div>
    </body>
    </html>
    '''

@app.route('/test-db')
def test_database():
    """Test database connection"""
    try:
        import mysql.connector
        
        # Get database credentials from environment
        db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'database': os.environ.get('DB_NAME', 'test'),
            'user': os.environ.get('DB_USER', 'test'),
            'password': os.environ.get('DB_PASSWORD', 'test')
        }
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful!',
            'test_result': result[0],
            'database': db_config['database']
        })
        
    except ImportError:
        return jsonify({
            'status': 'error',
            'message': 'mysql-connector-python not installed',
            'solution': 'Install mysql-connector-python in Python App settings'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database connection failed: {str(e)}',
            'config': {
                'host': os.environ.get('DB_HOST', 'NOT_SET'),
                'database': os.environ.get('DB_NAME', 'NOT_SET'),
                'user': os.environ.get('DB_USER', 'NOT_SET'),
                'password': 'SET' if os.environ.get('DB_PASSWORD') else 'NOT_SET'
            }
        })

@app.route('/info')
def system_info():
    """Display system information"""
    return jsonify({
        'python_version': sys.version,
        'flask_working': True,
        'current_directory': os.getcwd(),
        'environment_variables': {
            'DB_HOST': os.environ.get('DB_HOST', 'NOT_SET'),
            'DB_NAME': os.environ.get('DB_NAME', 'NOT_SET'),
            'DB_USER': os.environ.get('DB_USER', 'NOT_SET'),
            'DB_PASSWORD': 'SET' if os.environ.get('DB_PASSWORD') else 'NOT_SET',
            'SECRET_KEY': 'SET' if os.environ.get('SECRET_KEY') else 'NOT_SET',
            'MESSAGING_SERVICE': os.environ.get('MESSAGING_SERVICE', 'NOT_SET'),
            'TWILIO_ACCOUNT_SID': 'SET' if os.environ.get('TWILIO_ACCOUNT_SID') else 'NOT_SET'
        },
        'path': sys.path[:3]  # Show first 3 path entries
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'InMotion Test App',
        'ready_for_selfie_booth': True
    })

if __name__ == '__main__':
    app.run(debug=True)


# from flask import Flask
# app = Flask(__name__)

# @app.route('/')
# def hello():
#     return "Hello World - Basic Flask Test!"

# if __name__ == '__main__':
#     app.run()
######
# import os
# import sys


# sys.path.insert(0, os.path.dirname(__file__))


# def app(environ, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     message = 'It works yes thats right!\n'
#     version = 'Python v' + sys.version.split()[0] + '\n'
#     response = '\n'.join([message, version])
#     return [response.encode()]
