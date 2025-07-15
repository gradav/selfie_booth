# security_enhancements.py - Add to your existing code

import os
import magic
from functools import wraps
from flask import request, jsonify

# 1. Add to config.py - Production security headers
def add_security_headers(app):
    """Add basic security headers"""
    @app.after_request
    def security_headers(response):
        if not app.debug:  # Only in production
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    return app

# 2. Add to routes.py - File upload validation
def validate_image_file(file_data, max_size_mb=16):
    """Validate uploaded image file"""
    # Check file size
    if len(file_data) > max_size_mb * 1024 * 1024:
        return False, f"File too large (max {max_size_mb}MB)"
    
    # Check file signature
    try:
        file_type = magic.from_buffer(file_data[:1024], mime=True)
        if not file_type.startswith('image/'):
            return False, "File is not an image"
        
        # Additional check: ensure it's a common image format
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if file_type not in allowed_types:
            return False, f"Unsupported image type: {file_type}"
            
        return True, "Valid image"
    except Exception as e:
        return False, f"File validation error: {str(e)}"

# 3. Add to routes.py - Input sanitization
import re
from markupsafe import escape

def sanitize_text_input(text, max_length=50):
    """Sanitize text input"""
    if not text:
        return ""
    # Strip whitespace, escape HTML, limit length
    sanitized = escape(text.strip())
    return str(sanitized)[:max_length]

def validate_phone_number(phone):
    """Validate phone number format"""
    if not phone:
        return False, "Phone number required"
    
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', phone)
    
    # Check length (US format)
    if len(digits_only) == 10:
        return True, f"1{digits_only}"  # Add country code
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return True, digits_only
    else:
        return False, "Invalid phone number format"

# 4. Rate limiting (simple implementation)
from collections import defaultdict
from datetime import datetime, timedelta

class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key, max_requests=10, window_minutes=1):
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        return False

rate_limiter = SimpleRateLimiter()

def rate_limit(max_requests=10, window_minutes=1):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            if not rate_limiter.is_allowed(client_ip, max_requests, window_minutes):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# 5. Update your register route with validation:
@app.route('/register', methods=['POST'])
@rate_limit(max_requests=5, window_minutes=1)  # Prevent spam
def register():
    """Register a new user session with validation"""
    data = request.get_json()
    
    # Validate and sanitize inputs
    first_name = sanitize_text_input(data.get('firstName'))
    phone = data.get('phone', '').strip()
    email = sanitize_text_input(data.get('email', ''), max_length=100)
    
    # Validation
    if not first_name:
        return jsonify({'success': False, 'error': 'First name is required'})
    
    valid_phone, clean_phone = validate_phone_number(phone)
    if not valid_phone:
        return jsonify({'success': False, 'error': clean_phone})
    
    if not data.get('consent'):
        return jsonify({'success': False, 'error': 'Consent is required'})
    
    # Continue with existing logic...
    verification_code = str(random.randint(100000, 999999))
    session_id = session_manager.create_session(first_name, clean_phone, email, verification_code)
    session['session_id'] = session_id
    
    print(f"📝 New registration: {first_name} - Code: {verification_code}")
    return jsonify({'success': True})

# 6. Update your upload_photo route:
@app.route('/upload_photo', methods=['POST'])
@rate_limit(max_requests=3, window_minutes=1)  # Prevent photo spam
def upload_photo():
    """Upload photo with enhanced validation"""
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo uploaded'})
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'success': False, 'error': 'No photo selected'})
    
    session_id = request.form.get('session_id') or session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'No session found'})
    
    # Validate session
    result = session_manager.get_session_by_id(session_id)
    if not result or not result[6]:  # Not verified
        return jsonify({'success': False, 'error': 'Session not verified'})
    
    try:
        photo_data = photo.read()
        
        # Enhanced file validation
        is_valid, error_msg = validate_image_file(photo_data)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg})
        
        # Continue with existing logic...
        photo_data_b64 = base64.b64encode(photo_data).decode('utf-8')
        session_manager.update_photo_data(session_id, photo_data_b64)
        
        print(f"📸 Photo uploaded successfully - Session: {session_id}")
        return jsonify({'success': True, 'message': 'Photo ready for review'})
        
    except Exception as e:
        app.logger.error(f"Photo upload error: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload processing failed'})

# 7. Update your main app creation:
def main():
    """Updated main with security enhancements"""
    config = get_config()
    config.validate_configuration()
    
    app = create_app()
    
    # Add security headers
    app = add_security_headers(app)
    
    session_manager = SessionManager(config.DATABASE_PATH)
    create_routes(app, session_manager, config.UPLOAD_FOLDER)
    
    print_startup_info()
    
    # Production check
    if not config.DEBUG:
        print("🔒 Running in PRODUCTION mode")
        print("🔐 Security headers enabled")
        print("⚡ Rate limiting active")
    
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)