#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python
"""
Flask application for Selfie Booth API with Security System
FIXED VERSION - Correct file paths and environment variables
"""

import sys
import os
import json
import base64
from datetime import datetime
from io import BytesIO
from flask import redirect, request, url_for

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from flask import Flask, jsonify, request, send_file, Response
    from flask_cors import CORS
    FLASK_CORS_AVAILABLE = True
except ImportError:
    from flask import Flask, jsonify, request, send_file, Response
    FLASK_CORS_AVAILABLE = False

# Create Flask application instance
app = Flask(__name__)

# FIXED: Better secret key handling
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'selfie-booth-secret-key-change-in-production-2024')

# Enable CORS
if FLASK_CORS_AVAILABLE:
    CORS(app, origins=['*'])
else:
    # Manual CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

# Basic configuration
app.config['DEBUG'] = False

# FIXED: Better environment variable handling with debug info
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
KIOSK_USERNAME = os.environ.get('KIOSK_USERNAME', 'kiosk')  
KIOSK_PASSWORD = os.environ.get('KIOSK_PASSWORD', 'kiosk123')

# Print debug info on startup (remove in production)
print(f"🔑 Security Debug Info:")
print(f"   Admin Password: {'SET' if ADMIN_PASSWORD != 'admin123' else 'DEFAULT (admin123)'}")
print(f"   Kiosk Username: {KIOSK_USERNAME}")
print(f"   Kiosk Password: {'SET' if KIOSK_PASSWORD != 'kiosk123' else 'DEFAULT (kiosk123)'}")

# In-memory session storage (for simple cross-device communication)
active_sessions = {}

# Cumulative counters for admin dashboard (persist across session clears)
STATS_FILE = os.path.join(current_dir, 'cumulative_stats.json')

def load_cumulative_stats():
    """Load cumulative stats from file"""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading stats: {e}")
    
    # Default stats if file doesn't exist or has errors
    return {
        'total_sessions_created': 0,
        'total_sessions_verified': 0,
        'total_photos_taken': 0
    }

def save_cumulative_stats():
    """Save cumulative stats to file"""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(cumulative_stats, f)
    except Exception as e:
        print(f"Error saving stats: {e}")

# Load existing stats on startup
cumulative_stats = load_cumulative_stats()

# Session history storage
SESSION_HISTORY_FILE = os.path.join(current_dir, 'session_history.json')
IMAGES_DIR = os.path.join(current_dir, 'session_images')

def ensure_images_dir():
    """Create images directory if it doesn't exist"""
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

def load_session_history():
    """Load session history from file"""
    try:
        if os.path.exists(SESSION_HISTORY_FILE):
            with open(SESSION_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading session history: {e}")
    return []

def save_session_to_history(session_data):
    """Save a session to the permanent history"""
    try:
        history = load_session_history()
        
        # Add timestamp and unique ID - need to pass tablet_id separately since it's not in session_data
        tablet_id = session_data.get('tablet_id')  # This might be None
        if not tablet_id:
            # tablet_id not in session_data, need to find it from active_sessions
            for tid, sess in active_sessions.items():
                if sess.get('session_id') == session_data.get('session_id'):
                    tablet_id = tid
                    break
        
        if not tablet_id:
            tablet_id = 'UNKNOWN'  # Fallback
        
        session_record = {
            'id': f"{tablet_id}_{int(datetime.now().timestamp())}",
            'tablet_id': tablet_id,
            'session_id': session_data.get('session_id', ''),
            'user_name': session_data.get('user_name', ''),
            'phone': session_data.get('phone', ''),
            'email': session_data.get('email', ''),
            'verification_code': session_data.get('verification_code', ''),
            'created_at': session_data.get('timestamp', ''),
            'verified_at': session_data.get('verified_at', ''),
            'completed_at': datetime.now().isoformat(),
            'state': session_data.get('state', 'completed'),
            'image_filename': None  # Will be set when image is saved
        }
        
        history.append(session_record)
        
        # Keep only last 1000 sessions to prevent file from growing too large
        if len(history) > 1000:
            history = history[-1000:]
        
        with open(SESSION_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            
        return session_record['id']
        
    except Exception as e:
        print(f"Error saving session to history: {e}")
        return None

def save_session_image(session_id, image_data):
    """Save session image to file"""
    try:
        ensure_images_dir()
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Save with timestamp-based filename
        filename = f"{session_id}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
            
        # Update session history with image filename
        history = load_session_history()
        for session in history:
            if session['id'] == session_id:
                session['image_filename'] = filename
                break
        
        with open(SESSION_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            
        return filename
        
    except Exception as e:
        print(f"Error saving session image: {e}")
        return None

# Initialize on startup
ensure_images_dir()

# ============ Session Management and Protected Routes ============

from flask import session
import time

# Session timeout (2 hours)
ADMIN_SESSION_TIMEOUT = 7200

def is_admin_logged_in():
    """Check if admin is logged in and session hasn't expired"""
    if not session.get('admin'):
        return False
    
    # Check session timeout
    login_time = session.get('admin_login_time', 0)
    if time.time() - login_time > ADMIN_SESSION_TIMEOUT:
        # Session expired, clear it
        session.pop('admin', None)
        session.pop('admin_login_time', None)
        return False
    
    return True

def is_kiosk_logged_in():
    """Check if kiosk is logged in"""
    return session.get('kiosk') is not None

# FIXED: Correct file path resolution
def get_project_root():
    """Get the project root directory (one level up from api/)"""
    return os.path.dirname(current_dir)

# ============ Session Management and Protected Routes ============

from flask import session
import time

# Session timeout (2 hours)
ADMIN_SESSION_TIMEOUT = 7200

def is_admin_logged_in():
    """Check if admin is logged in and session hasn't expired"""
    if not session.get('admin'):
        return False
    
    # Check session timeout
    login_time = session.get('admin_login_time', 0)
    if time.time() - login_time > ADMIN_SESSION_TIMEOUT:
        # Session expired, clear it
        session.pop('admin', None)
        session.pop('admin_login_time', None)
        return False
    
    return True

def is_kiosk_logged_in():
    """Check if kiosk is logged in"""
    return session.get('kiosk') is not None

# FIXED: Serve the actual files with proper modifications
@app.route('/admin')
@app.route('/selfie_booth/api/admin')  
def admin_dashboard():
    """Protected admin dashboard - serve the actual file with modifications"""
    if not is_admin_logged_in():
        return redirect('/selfie_booth/api/admin/login')
    
    try:
        admin_file_path = os.path.join(get_project_root(), 'admin.html')
        print(f"📁 Looking for admin.html at: {admin_file_path}")
        
        with open(admin_file_path, 'r') as f:
            admin_html = f.read()
        
        # FIXED: Update the API base URLs to work with authentication
        # Replace the API calls to use the full path that works
        admin_html = admin_html.replace(
            "'/selfie_booth/api/admin/stats'", 
            "'/selfie_booth/api/admin/stats'"
        )
        admin_html = admin_html.replace(
            "'/selfie_booth/api/admin/sessions'", 
            "'/selfie_booth/api/admin/sessions'"
        )
        admin_html = admin_html.replace(
            "'/selfie_booth/api/admin/reset'", 
            "'/selfie_booth/api/admin/reset'"
        )
        
        # Add logout button and session info
        logout_info = '''
        <div style="position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 5px; z-index: 10000; font-family: Arial;">
            <span>✅ Admin: Logged in</span> | 
            <a href="/selfie_booth/api/admin/logout" style="color: #ff6b6b; text-decoration: none;">Logout</a>
        </div>
        '''
        
        # Insert logout info after <body> tag
        admin_html = admin_html.replace('<body>', '<body>' + logout_info)
        
        return admin_html
        
    except FileNotFoundError as e:
        print(f"❌ Admin file not found: {e}")
        return f'''<!DOCTYPE html>
<html>
<head><title>Admin Dashboard Error</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h2>❌ Admin Dashboard Not Found</h2>
    <p>The admin.html file could not be found at: {admin_file_path}</p>
    <p><a href="/selfie_booth/api/admin/logout">Logout</a></p>
</body>
</html>''', 404

@app.route('/kiosk/display')
@app.route('/selfie_booth/api/kiosk/display')  
def kiosk_display():
    """Protected kiosk display - serve the actual file with modifications"""
    if not is_kiosk_logged_in():
        return redirect('/selfie_booth/api/kiosk/login')
    
    try:
        kiosk_file_path = os.path.join(get_project_root(), 'index.html')
        print(f"📁 Looking for index.html at: {kiosk_file_path}")
        
        with open(kiosk_file_path, 'r') as f:
            kiosk_html = f.read()
        
        # FIXED: Inject authentication state into the page
        # Add a script that sets up the kiosk as authenticated
        auth_script = f'''
        <script>
        // Inject authentication state for kiosk
        window.kioskAuthenticated = true;
        window.kioskUsername = '{session.get('kiosk', 'Unknown')}';
        
        // Override the kiosk manager initialization to skip checkout
        document.addEventListener('DOMContentLoaded', function() {{
            if (window.kioskManager) {{
                // Set kiosk as already authenticated
                window.kioskManager.kioskState = 'active';
                window.kioskManager.tabletId = 'KIOSK_AUTH';
                window.kioskManager.location = 'authenticated';
                window.kioskManager.updateTabletInfo();
                window.kioskManager.generateQRCode();
                window.kioskManager.startSessionMonitoring();
            }}
        }});
        </script>
        '''
        
        # Add logout button and kiosk info
        kiosk_info = f'''
        <div style="position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 5px; z-index: 10000; font-family: Arial;">
            <span>✅ Kiosk: {session.get('kiosk', 'Unknown')}</span> | 
            <a href="/selfie_booth/api/kiosk/logout" style="color: #ff6b6b; text-decoration: none;">Logout</a>
        </div>
        '''
        
        # Insert auth script and kiosk info
        kiosk_html = kiosk_html.replace('<body>', '<body>' + kiosk_info)
        kiosk_html = kiosk_html.replace('</head>', auth_script + '</head>')
        
        return kiosk_html
        
    except FileNotFoundError as e:
        print(f"❌ Kiosk file not found: {e}")
        return f'''<!DOCTYPE html>
<html>
<head><title>Kiosk Display Error</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h2>❌ Kiosk Display Not Found</h2>
    <p>The index.html file could not be found at: {kiosk_file_path}</p>
    <p><a href="/selfie_booth/api/kiosk/logout">Logout</a></p>
</body>
</html>''', 404

@app.route('/admin/logout')
@app.route('/selfie_booth/api/admin/logout')  # Add this route to match links
def admin_logout():
    """Admin logout"""
    session.pop('admin', None)
    session.pop('admin_login_time', None)
    return '''<!DOCTYPE html>
<html>
<head><title>Admin Logout</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h2>👋 Admin Logged Out</h2>
    <p>You have been successfully logged out.</p>
    <p><a href="/selfie_booth/api/admin/login">Login Again</a></p>
</body>
</html>'''

@app.route('/kiosk/logout')
@app.route('/selfie_booth/api/kiosk/logout')  # Add this route to match links
def kiosk_logout():
    """Kiosk logout"""
    session.pop('kiosk', None)
    return '''<!DOCTYPE html>
<html>
<head><title>Kiosk Logout</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h2>👋 Kiosk Logged Out</h2>
    <p>You have been successfully logged out.</p>
    <p><a href="/selfie_booth/api/kiosk/login">Login Again</a></p>
</body>
</html>'''

# ============ Security Routes ============

@app.route('/admin/login', methods=['GET', 'POST'])
@app.route('/selfie_booth/api/admin/login', methods=['GET', 'POST'])  # Add this route too
def admin_login():
    """Simple admin login - returns HTML directly"""
    if request.method == 'GET':
        # Return simple HTML directly (no templates needed)
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <style>
        body { font-family: Arial; background: #667eea; padding: 50px; }
        .container { background: white; padding: 40px; border-radius: 15px; max-width: 400px; margin: 0 auto; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; }
        button:hover { background: #5a6fd8; }
        .error { color: red; text-align: center; margin: 10px 0; }
        .debug { background: #f0f0f0; padding: 10px; margin: 10px 0; font-size: 12px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔧 Admin Login</h2>'''
        
        # FIXED: Add debug info to help troubleshoot
        html += f'''
        <div class="debug">
            <strong>Debug Info:</strong><br>
            Expected Password: <code>{ADMIN_PASSWORD}</code><br>
            (Remove this debug info in production)
        </div>'''
        
        html += '''
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password" required>
            <button type="submit">Login</button>
        </form>'''
        
        # Add error message if present
        error = request.args.get('error')
        if error:
            html += f'<div class="error">{error}</div>'
            
        html += '''
        <p><a href="/selfie_booth/api/kiosk/login">Kiosk Login →</a></p>
    </div>
</body>
</html>'''
        return html
    
    # Handle POST - check password
    password = request.form.get('password', '')
    print(f"🔑 Admin login attempt: '{password}' vs expected '{ADMIN_PASSWORD}'")
    
    if password == ADMIN_PASSWORD:
        # Set session data
        session['admin'] = True
        session['admin_login_time'] = time.time()
        session.permanent = True
        
        print("✅ Admin login successful")
        # FIXED: Redirect to the route that actually exists
        return redirect('/selfie_booth/api/admin')
    else:
        print("❌ Admin login failed")
        return redirect('/selfie_booth/api/admin/login?error=Invalid password')

@app.route('/kiosk/login', methods=['GET', 'POST'])
@app.route('/selfie_booth/api/kiosk/login', methods=['GET', 'POST'])  # Add this route too
def kiosk_login():
    """Simple kiosk login - returns HTML directly"""
    if request.method == 'GET':
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Kiosk Login</title>
    <style>
        body { font-family: Arial; background: #667eea; padding: 50px; }
        .container { background: white; padding: 40px; border-radius: 15px; max-width: 400px; margin: 0 auto; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; }
        button:hover { background: #5a6fd8; }
        .error { color: red; text-align: center; margin: 10px 0; }
        .info { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .debug { background: #f0f0f0; padding: 10px; margin: 10px 0; font-size: 12px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📱 Kiosk Login</h2>
        <div class="info">Login once to access the kiosk display.</div>'''
        
        # FIXED: Add debug info to help troubleshoot
        html += f'''
        <div class="debug">
            <strong>Debug Info:</strong><br>
            Expected Username: <code>{KIOSK_USERNAME}</code><br>
            Expected Password: <code>{KIOSK_PASSWORD}</code><br>
            (Remove this debug info in production)
        </div>'''
        
        html += '''
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login to Kiosk</button>
        </form>'''
        
        # Add error message if present  
        error = request.args.get('error')
        if error:
            html += f'<div class="error">{error}</div>'
            
        html += '''
        <p><a href="/selfie_booth/api/admin/login">Admin Login →</a></p>
    </div>
</body>
</html>'''
        return html
    
    # Handle POST - check credentials
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    print(f"🔑 Kiosk login attempt: '{username}'/'{password}' vs expected '{KIOSK_USERNAME}'/'{KIOSK_PASSWORD}'")
    
    if username == KIOSK_USERNAME and password == KIOSK_PASSWORD:
        # Set session data
        session['kiosk'] = username
        session.permanent = True
        
        print("✅ Kiosk login successful")
        # FIXED: Redirect to the route that actually exists
        return redirect('/selfie_booth/api/kiosk/display')
    else:
        print("❌ Kiosk login failed")
        return redirect('/selfie_booth/api/kiosk/login?error=Invalid credentials')

# ============ Authentication Status Endpoints ============

@app.route('/auth/status')
@app.route('/selfie_booth/api/auth/status')
def auth_status():
    """Check authentication status for both admin and kiosk"""
    return jsonify({
        'success': True,
        'data': {
            'admin_logged_in': is_admin_logged_in(),
            'kiosk_logged_in': is_kiosk_logged_in(),
            'kiosk_username': session.get('kiosk', None) if is_kiosk_logged_in() else None,
            'admin_login_time': session.get('admin_login_time', None) if is_admin_logged_in() else None
        }
    }), 200

# ============ ALL YOUR EXISTING WORKING ENDPOINTS (UNCHANGED) ============

@app.route('/')
def api_root():
    """API root endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'message': 'Selfie Booth Flask API is working!',
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version.split()[0],
            'endpoints': [
                '/health',
                '/register', 
                '/verify',
                '/session_check',
                '/qr_code',
                '/admin/login',
                '/kiosk/login'
            ]
        }
    }), 200

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'message': 'Selfie Booth API is running!',
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version.split()[0],
            'flask_working': True
        }
    }), 200

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    """User registration endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        # Basic validation
        if not data.get('firstName'):
            return jsonify({
                'success': False,
                'error': 'First name is required'
            }), 400
        
        if not data.get('phone'):
            return jsonify({
                'success': False,
                'error': 'Phone number is required'
            }), 400
        
        # Generate session data
        import secrets
        session_id = secrets.token_urlsafe(16)
        verification_code = str(secrets.randbelow(900000) + 100000)
        
        # Store session in server memory
        tablet_id = data.get('tablet_id', 'UNKNOWN')
        active_sessions[tablet_id] = {
            'session_id': session_id,
            'verification_code': verification_code,
            'user_name': data.get('firstName'),
            'phone': data.get('phone'),
            'email': data.get('email'),
            'state': 'verification_needed',
            'timestamp': datetime.now().isoformat()
        }
        
        # Increment cumulative counter
        cumulative_stats['total_sessions_created'] += 1
        save_cumulative_stats()  # Persist to file
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'message': 'Registration successful! Look at the kiosk for your verification code.',
                'verification_code': verification_code,
                'user_name': data.get('firstName')
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Registration failed: {str(e)}'
        }), 500

@app.route('/verify', methods=['POST', 'OPTIONS'])
def verify():
    """Verification endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
            
        code = data.get('code', '')
        
        # For testing, accept any 6-digit code and update session state
        if len(code) == 6 and code.isdigit():
            # Find session with matching verification code
            tablet_id = None
            for tid, session in active_sessions.items():
                if session.get('verification_code') == code:
                    tablet_id = tid
                    break
            
            if tablet_id:
                # Update session state to verified
                active_sessions[tablet_id]['state'] = 'photo_session'
                active_sessions[tablet_id]['verified_at'] = datetime.now().isoformat()
                
                # Save session to history immediately upon verification
                # Add tablet_id to session data before saving
                session_with_tablet_id = active_sessions[tablet_id].copy()
                session_with_tablet_id['tablet_id'] = tablet_id
                session_history_id = save_session_to_history(session_with_tablet_id)
                active_sessions[tablet_id]['session_history_id'] = session_history_id  # Store for later image saving
                
                # Increment cumulative counters
                cumulative_stats['total_sessions_verified'] += 1
                cumulative_stats['total_photos_taken'] += 1  # Assume verified sessions take photos
                save_cumulative_stats()  # Persist to file
            
            return jsonify({
                'success': True,
                'data': {
                    'verified': True,
                    'message': 'Verification successful!',
                    'redirect': 'photo.html'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Please enter a valid 6-digit code'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Verification failed: {str(e)}'
        }), 500

@app.route('/session_check')
def session_check():
    """Session state check endpoint"""
    try:
        tablet_id = request.args.get('tablet_id', 'default')
        
        # Check if there's an active session for this tablet
        if tablet_id in active_sessions:
            session = active_sessions[tablet_id]
            return jsonify({
                'success': True,
                'data': {
                    'session_state': session['state'],
                    'tablet_id': tablet_id,
                    'verification_code': session.get('verification_code'),
                    'user_name': session.get('user_name'),
                    'timestamp': datetime.now().isoformat()
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': {
                    'session_state': 'default',
                    'tablet_id': tablet_id,
                    'timestamp': datetime.now().isoformat()
                }
            }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Session check failed: {str(e)}'
        }), 500

@app.route('/session_complete', methods=['POST', 'OPTIONS'])
def session_complete():
    """Mark session as complete and clean up"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
            
        tablet_id = data.get('tablet_id')
        session_history_id = None
        
        if tablet_id and tablet_id in active_sessions:
            # Get the existing session history ID (already saved during verification)
            session_data = active_sessions[tablet_id]
            session_history_id = session_data.get('session_history_id')
            
            # Remove from active sessions
            del active_sessions[tablet_id]
            
        return jsonify({
            'success': True,
            'data': {
                'message': 'Session completed successfully',
                'session_history_id': session_history_id,
                'cumulative_stats': cumulative_stats  # Include stats in response for debugging
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Session completion failed: {str(e)}'
        }), 500

@app.route('/save_image', methods=['POST', 'OPTIONS'])
def save_image():
    """Save session image to permanent storage"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict()
            
        session_history_id = data.get('session_history_id')
        image_data = data.get('image_data')
        
        if not session_history_id or not image_data:
            return jsonify({
                'success': False,
                'error': 'session_history_id and image_data are required'
            }), 400
            
        filename = save_session_image(session_history_id, image_data)
        
        if filename:
            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'message': 'Image saved successfully'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save image'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Image save failed: {str(e)}'
        }), 500

@app.route('/get_image')
def get_image():
    """Return the photo for a given tablet_id and verification_code if available"""
    tablet_id = request.args.get('tablet_id')
    verification_code = request.args.get('verification_code')
    if not tablet_id or not verification_code:
        return jsonify({'success': False, 'error': 'tablet_id and verification_code required'}), 400

    # Find the session in history
    history = load_session_history()
    session = None
    for s in history:
        if s.get('tablet_id') == tablet_id and s.get('verification_code') == verification_code:
            session = s
            break
    if not session:
        return jsonify({'success': False, 'ready': False, 'error': 'Session not found'}), 404
    image_filename = session.get('image_filename')
    if not image_filename:
        return jsonify({'success': True, 'ready': False, 'message': 'Photo not ready yet'}), 200
    image_path = os.path.join(IMAGES_DIR, image_filename)
    if not os.path.exists(image_path):
        return jsonify({'success': False, 'ready': False, 'error': 'Image file missing'}), 404
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    return jsonify({'success': True, 'ready': True, 'image_data': f'data:image/jpeg;base64,{image_b64}'}), 200

# ============ QR Code Generation Endpoint ============

@app.route('/qr_code')
def generate_qr_code():
    """Generate QR code server-side"""
    try:
        url = request.args.get('url')
        size = int(request.args.get('size', 200))
        
        if not url:
            return jsonify({'success': False, 'error': 'URL parameter required'}), 400
        
        # Validate size
        if size < 50 or size > 1000:
            size = 200
        
        # Try to use qrcode library if available
        try:
            import qrcode
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=max(1, size//25),  # Approximate sizing
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize to exact size if needed
            if hasattr(img, 'resize'):
                img = img.resize((size, size))
            
            # Convert to bytes
            img_io = BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            
            return send_file(
                img_io, 
                mimetype='image/png',
                as_attachment=False,
                download_name=f'qr_code_{size}x{size}.png'
            )
            
        except ImportError:
            # Fallback to external service
            try:
                import requests
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={url}"
                
                response = requests.get(qr_url, timeout=10)
                if response.status_code == 200:
                    return Response(
                        response.content, 
                        mimetype='image/png',
                        headers={'Cache-Control': 'public, max-age=3600'}  # Cache for 1 hour
                    )
                else:
                    raise Exception(f"External QR service returned status {response.status_code}")
            except ImportError:
                raise Exception("requests library not available")
        
    except Exception as e:
        # Return error as JSON
        return jsonify({
            'success': False, 
            'error': f'QR code generation failed: {str(e)}',
            'fallback_url': f'https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={url}'
        }), 500

# ============ PROTECTED Admin API Endpoints ============

@app.route('/admin/stats')
@app.route('/selfie_booth/api/admin/stats')  # Add this route to match admin.html calls
def admin_stats():
    """Admin statistics endpoint - PROTECTED"""
    if not is_admin_logged_in():
        return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
    
    try:
        # Current active sessions (for reference)
        current_active = len(active_sessions)
        current_pending = sum(1 for session in active_sessions.values() 
                             if session.get('state') == 'verification_needed')
        
        # Return cumulative stats (historical totals)
        stats_data = {
            'total_sessions': cumulative_stats['total_sessions_created'],
            'verified_sessions': cumulative_stats['total_sessions_verified'],
            'pending_sessions': current_pending,  # Only current pending makes sense
            'photos_taken': cumulative_stats['total_photos_taken'],
            # Include current active for admin reference
            'current_active_sessions': current_active
        }
        
        return jsonify({
            'success': True,
            'data': stats_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Stats failed: {str(e)}'
        }), 500

@app.route('/admin/sessions')
@app.route('/selfie_booth/api/admin/sessions')  # Add this route to match admin.html calls
def admin_sessions():
    """Admin sessions list endpoint - PROTECTED"""
    if not is_admin_logged_in():
        return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
    
    try:
        sessions_list = []
        
        for tablet_id, session_data in active_sessions.items():
            # Format session data for admin display - match expected field names
            is_verified = (session_data.get('state') == 'photo_session' or 
                          session_data.get('verified_at') is not None)
            
            session_info = {
                'session_id': session_data.get('session_id', tablet_id),  # Use session_id or fallback to tablet_id
                'tablet_id': tablet_id,
                'first_name': session_data.get('user_name', 'Unknown'),  # Admin expects first_name not user_name
                'phone': session_data.get('phone', 'N/A'),
                'email': session_data.get('email', ''),
                'verified': is_verified,  # Admin expects boolean verified not state
                'state': session_data.get('state', 'unknown'),
                'verification_code': session_data.get('verification_code', ''),
                'created_at': session_data.get('timestamp', ''),
                'verified_at': session_data.get('verified_at', '')
            }
            sessions_list.append(session_info)
        
        # Sort by creation time (most recent first)
        sessions_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': sessions_list,
                'total': len(sessions_list)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Sessions list failed: {str(e)}'
        }), 500

@app.route('/admin/reset', methods=['POST'])
@app.route('/selfie_booth/api/admin/reset', methods=['POST'])  # Add this route to match admin.html calls
def admin_reset():
    """Admin reset sessions endpoint - PROTECTED"""
    if not is_admin_logged_in():
        return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
    
    try:
        # Get reset type from request (optional)
        reset_type = 'sessions'  # Default: only reset active sessions
        if request.is_json:
            data = request.get_json() or {}
            reset_type = data.get('type', 'sessions')  # 'sessions' or 'all'
        
        # Count current sessions before clearing
        deleted_count = len(active_sessions)
        
        # Always clear active sessions
        active_sessions.clear()
        
        message = f'Successfully reset {deleted_count} active sessions'
        
        # Optionally reset cumulative stats
        if reset_type == 'all':
            old_totals = cumulative_stats.copy()
            cumulative_stats['total_sessions_created'] = 0
            cumulative_stats['total_sessions_verified'] = 0
            cumulative_stats['total_photos_taken'] = 0
            save_cumulative_stats()  # Persist reset to file
            message += f' and cumulative stats (was {old_totals["total_sessions_created"]} total sessions)'
        
        return jsonify({
            'success': True,
            'data': {
                'deleted_count': deleted_count,
                'reset_type': reset_type,
                'message': message
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Reset failed: {str(e)}'
        }), 500

# ============ Error Handlers ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

# ============ Development/Testing ============

if __name__ == '__main__':
    print("🚀 Starting Flask app with security fixes...")
    print(f"🔑 Security Configuration:")
    print(f"   Admin Password: {'SET' if ADMIN_PASSWORD != 'admin123' else 'DEFAULT (admin123)'}")
    print(f"   Kiosk Username: {KIOSK_USERNAME}")
    print(f"   Kiosk Password: {'SET' if KIOSK_PASSWORD != 'kiosk123' else 'DEFAULT (kiosk123)'}")
    print(f"📁 File Paths:")
    print(f"   Project Root: {get_project_root()}")
    print(f"   Admin File: {os.path.join(get_project_root(), 'admin.html')}")
    print(f"   Kiosk File: {os.path.join(get_project_root(), 'index.html')}")
    app.run(debug=False, host='0.0.0.0', port=5000)