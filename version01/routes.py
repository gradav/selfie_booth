#!/usr/bin/env python3
"""
Fixed Routes module - Direct route registration like the original
"""

import os
import random
import base64
import re
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, session, redirect, render_template_string
from markupsafe import escape

# Import templates
from templates import (
    KIOSK_PAGE_OPTIMIZED, MOBILE_PAGE_OPTIMIZED, VERIFY_PAGE_OPTIMIZED,
    PHOTO_SESSION_PAGE_OPTIMIZED, CAMERA_PAGE_OPTIMIZED, VERIFICATION_DISPLAY_PAGE
)

# Rate limiting
class UnifiedRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.last_cleanup = datetime.now()
    
    def cleanup_old_requests(self):
        now = datetime.now()
        if now - self.last_cleanup > timedelta(minutes=5):
            cutoff = now - timedelta(minutes=10)
            for ip in list(self.requests.keys()):
                self.requests[ip] = [req_time for req_time in self.requests[ip] if req_time > cutoff]
                if not self.requests[ip]:
                    del self.requests[ip]
            self.last_cleanup = now
    
    def is_allowed(self, key, max_requests=10, window_minutes=1):
        self.cleanup_old_requests()
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        return False

# Global rate limiter
rate_limiter = UnifiedRateLimiter()

def rate_limit(max_requests=10, window_minutes=1):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.headers.get('X-Forwarded-For', 
                       request.headers.get('X-Real-IP', 
                       request.remote_addr))
            
            if not rate_limiter.is_allowed(client_ip, max_requests, window_minutes):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Input validation
def sanitize_text_input(text, max_length=50):
    if not text:
        return ""
    sanitized = escape(text.strip())
    return str(sanitized)[:max_length]

def validate_phone_number(phone):
    if not phone:
        return False, "Phone number required"
    
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) == 10:
        return True, f"1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return True, digits_only
    else:
        return False, "Invalid phone number format"

def get_tablet_id():
    tablet_id = session.get('tablet_id')
    if not tablet_id:
        tablet_id = str(uuid.uuid4())[:8]
        session['tablet_id'] = tablet_id
    return tablet_id

def get_location():
    location = request.args.get('location') or session.get('location', 'default')
    session['location'] = location
    return location

def get_short_url_for_tablet(tablet_id, base_url):
    from config import Config
    return Config.get_short_url_for_tablet(tablet_id, base_url)

# Global variables to store managers (set by register_routes)
session_manager = None
messaging_factory = None
upload_folder = None

def register_routes(app, sm, mf, uf):
    """Register all routes - called from app.py"""
    global session_manager, messaging_factory, upload_folder
    session_manager = sm
    messaging_factory = mf
    upload_folder = uf
    
    print("🔗 Registering routes...")
    
    # Root redirect - only for local development
    @app.route('/')
    def root():
        # Check if we're in a hosted subdirectory environment
        if request.environ.get('SCRIPT_NAME') or '/selfie_booth' in request.url_root:
            # In hosted environment, serve kiosk directly
            return kiosk()
        else:
            # Local development, redirect to selfie_booth
            return redirect('/selfie_booth/')
    
    # Kiosk display
    @app.route('/selfie_booth/')
    def kiosk():
        tablet_id = get_tablet_id()
        location = get_location()
        
        session_manager.cleanup_old_sessions()
        
        # Check for verified session ready for photo
        verified_result = session_manager.get_verified_session(tablet_id)
        if verified_result:
            first_name, session_id, created_at = verified_result
            try:
                if isinstance(created_at, datetime):
                    created_time = created_at
                else:
                    created_time = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                
                time_diff = datetime.now() - created_time
                if time_diff < timedelta(minutes=3):
                    return render_template_string(CAMERA_PAGE_OPTIMIZED, 
                                                name=first_name, 
                                                session_id=session_id)
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error parsing timestamp {created_at}: {e}")
        
        # Check for unverified session
        unverified_result = session_manager.get_unverified_session(tablet_id)
        if unverified_result:
            first_name, verification_code, created_at = unverified_result
            try:
                if isinstance(created_at, datetime):
                    created_time = created_at
                else:
                    created_time = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                
                time_diff = datetime.now() - created_time
                if time_diff < timedelta(minutes=2):
                    return render_template_string(VERIFICATION_DISPLAY_PAGE,
                                                name=first_name,
                                                code=verification_code,
                                                tablet_id=tablet_id)
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error parsing timestamp {created_at}: {e}")
        
        # Default kiosk page
        base_url = request.host_url.rstrip('/')
        short_url = get_short_url_for_tablet(tablet_id, base_url)
        
        return render_template_string(KIOSK_PAGE_OPTIMIZED,
                                    tablet_id=tablet_id,
                                    location=location,
                                    mobile_url=short_url)
    
    # Mobile registration
    @app.route('/selfie_booth/mobile')
    @app.route('/mobile')
    def mobile():
        # Check for redirect loop indicators
        from_verify = request.args.get('from_verify')
        from_photo = request.args.get('from_photo')
        
        if from_verify or from_photo:
            # Clear any problematic session data
            session.pop('session_id', None)
        
        tablet_id = request.args.get('tablet_id') or get_tablet_id()
        location = request.args.get('location') or get_location()
        
        session['tablet_id'] = tablet_id
        session['location'] = location
        
        return render_template_string(MOBILE_PAGE_OPTIMIZED, 
                                    tablet_id=tablet_id,
                                    location=location)
    
    # Registration endpoint
    @app.route('/selfie_booth/register', methods=['POST'])
    @app.route('/register', methods=['POST'])
    @rate_limit(max_requests=50, window_minutes=1)
    def register():
        data = request.get_json()
        
        tablet_id = data.get('tablet_id') or session.get('tablet_id')
        location = data.get('location') or session.get('location')
        
        first_name = sanitize_text_input(data.get('firstName'))
        phone = data.get('phone', '').strip()
        email = sanitize_text_input(data.get('email', ''), max_length=100)
        
        if not first_name:
            return jsonify({'success': False, 'error': 'First name is required'})
        
        valid_phone, clean_phone = validate_phone_number(phone)
        if not valid_phone:
            return jsonify({'success': False, 'error': clean_phone})
        
        if not data.get('consent'):
            return jsonify({'success': False, 'error': 'Consent is required'})
        
        verification_code = str(random.randint(100000, 999999))
        
        session_id = session_manager.create_session(
            first_name, clean_phone, email, verification_code, tablet_id, location
        )
        
        if session_id:
            session['session_id'] = session_id
            session['tablet_id'] = tablet_id
            session['location'] = location
            
            print(f"📝 New registration: {first_name} - Code: {verification_code} - Tablet: {tablet_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Registration failed'})
    
    # Verification page
    @app.route('/selfie_booth/verify')
    @app.route('/verify')
    def verify_page():
        # Check if we're coming from a redirect loop
        if request.args.get('from_redirect'):
            # Clear session and start fresh
            session.clear()
            return redirect('/selfie_booth/')
        
        if 'session_id' not in session:
            return redirect('/selfie_booth/mobile?from_verify=1')
        
        return render_template_string(VERIFY_PAGE_OPTIMIZED)
    
    # Verification endpoint
    @app.route('/selfie_booth/verify', methods=['POST'])
    @app.route('/verify', methods=['POST'])
    @rate_limit(max_requests=25, window_minutes=1)
    def verify_code():
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        print(f"🔐 verify_code called at {datetime.now().isoformat()} from IP {client_ip}")
        
        if 'session_id' not in session:
            print(f"❌ Session expired for {client_ip}")
            return jsonify({'success': False, 'error': 'Session expired'})
        
        data = request.get_json()
        entered_code = data.get('code', '').strip()
        
        if not entered_code.isdigit() or len(entered_code) != 6:
            return jsonify({'success': False, 'error': 'Invalid code format'})
        
        success, first_name = session_manager.verify_session(session['session_id'], entered_code)
        
        if success:
            print(f"✅ Verification successful for {first_name} from {client_ip}")
            return jsonify({'success': True, 'redirect': '/selfie_booth/photo_session'})
        else:
            print(f"❌ Invalid verification code from {client_ip}")
            return jsonify({'success': False, 'error': 'Invalid code'})
    
    # Photo session
    @app.route('/selfie_booth/photo_session')
    @app.route('/photo_session')
    def photo_session():
        # Check if we're coming from a redirect loop
        if request.args.get('from_redirect'):
            # Clear session and start fresh
            session.clear()
            return redirect('/selfie_booth/')
        
        if 'session_id' not in session:
            return redirect('/selfie_booth/mobile?from_photo=1')
        
        result = session_manager.get_session_by_id(session['session_id'])
        if not result or not result[6]:
            return redirect('/selfie_booth/verify?from_photo=1')
        
        return render_template_string(PHOTO_SESSION_PAGE_OPTIMIZED, 
                                    session_id=session['session_id'])
    
    # Upload photo
    @app.route('/selfie_booth/upload_photo', methods=['POST'])
    @app.route('/upload_photo', methods=['POST'])
    @rate_limit(max_requests=100, window_minutes=1)
    def upload_photo():
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        print(f"🔍 upload_photo called at {datetime.now().isoformat()} from IP {client_ip}")
        
        if 'photo' not in request.files:
            print(f"❌ No photo in request from {client_ip}")
            return jsonify({'success': False, 'error': 'No photo uploaded'})
        
        photo = request.files['photo']
        session_id = request.form.get('session_id') or session.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session found'})
        
        result = session_manager.get_session_by_id(session_id)
        if not result or not result[6]:
            return jsonify({'success': False, 'error': 'Session not verified'})
        
        try:
            photo_data = photo.read()
            photo_data_b64 = base64.b64encode(photo_data).decode('utf-8')
            session_manager.update_photo_data(session_id, photo_data_b64)
            
            print(f"📸 Photo uploaded successfully for session: {session_id} from {client_ip}")
            return jsonify({'success': True, 'message': 'Photo ready for review'})
            
        except Exception as e:
            print(f"❌ Upload failed for session {session_id} from {client_ip}: {str(e)}")
            return jsonify({'success': False, 'error': 'Upload failed'})
    
    # Check photo
    @app.route('/selfie_booth/check_photo')
    @app.route('/check_photo')
    @rate_limit(max_requests=30, window_minutes=1)
    def check_photo():
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'photo_ready': False})
        
        result = session_manager.get_photo_data(session_id)
        
        if result and result[0]:
            return jsonify({'photo_ready': True, 'photo_data': result[1]})
        else:
            return jsonify({'photo_ready': False})
    
    # Keep photo
    @app.route('/selfie_booth/keep_photo', methods=['POST'])
    @app.route('/keep_photo', methods=['POST'])
    @rate_limit(max_requests=50, window_minutes=1)
    def keep_photo():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        result = session_manager.get_session_data(session_id)
        if not result:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        phone, first_name, email, photo_data_b64 = result
        
        try:
            photo_data = base64.b64decode(photo_data_b64)
            
            messaging_service = messaging_factory.create_service(upload_folder=upload_folder)
            message = f"Hi {first_name}! Here's your selfie from the photo booth!"
            
            recipient = messaging_factory.get_recipient_for_service(
                messaging_service, phone, email, session_id
            )
            
            success, details = messaging_service.send_photo(recipient, photo_data, message)
            
            if success:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                photo_filename = f"selfie_{session_id}_{timestamp}.jpg"
                photo_path = os.path.join(upload_folder, photo_filename)
                
                with open(photo_path, 'wb') as f:
                    f.write(photo_data)
                
                session_manager.delete_session(session_id)
                
                print(f"📸 Photo sent successfully for {first_name}")
                return jsonify({'success': True, 'message': details})
            else:
                return jsonify({'success': False, 'error': details})
                
        except Exception as e:
            return jsonify({'success': False, 'error': 'Sending failed'})
    
    # Retake photo
    @app.route('/selfie_booth/retake_photo', methods=['POST'])
    @app.route('/retake_photo', methods=['POST'])
    @rate_limit(max_requests=25, window_minutes=1)
    def retake_photo():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        session_manager.reset_photo_for_retake(session_id)
        
        print(f"🔄 Photo retake for session {session_id}")
        return jsonify({'success': True})
    
    # Session check - both paths for hosted and local environments
    @app.route('/selfie_booth/session_check')
    @app.route('/session_check')
    @rate_limit(max_requests=100, window_minutes=1)
    def session_check():
        tablet_id = request.args.get('tablet_id')
        session_state = session_manager.get_session_state(tablet_id)
        
        return jsonify({
            'session_state': session_state,
            'timestamp': datetime.now().isoformat(),
            'tablet_id': tablet_id
        })
    
    # Short URLs - both paths for hosted and local environments
    @app.route('/selfie_booth/1')
    @app.route('/1')
    def booth_location_1():
        return redirect('mobile?tablet_id=TABLET1&location=lobby')

    @app.route('/selfie_booth/2') 
    @app.route('/2')
    def booth_location_2():
        return redirect('mobile?tablet_id=TABLET2&location=entrance')

    @app.route('/selfie_booth/3')
    @app.route('/3')
    def booth_location_3():
        return redirect('mobile?tablet_id=TABLET3&location=event_hall')

    @app.route('/selfie_booth/4')
    @app.route('/4')
    def booth_location_4():
        return redirect('mobile?tablet_id=TABLET4&location=party_room')
    
    # Admin
    @app.route('/selfie_booth/admin')
    @app.route('/admin')
    def admin():
        total_count, verified_count, unverified_count = session_manager.get_session_stats()
        recent_sessions = session_manager.get_recent_sessions(10)
        
        sessions_html = ""
        for session_data in recent_sessions:
            status = '✅' if session_data[3] else '⏳'
            sessions_html += f"<tr><td>{session_data[1]}</td><td>{session_data[2]}</td><td>{status}</td><td>{session_data[4]}</td><td>{session_data[5]}</td></tr>"
        
        return f"""
        <html>
        <head><title>Selfie Booth Admin</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1>📸 Selfie Booth Admin Dashboard</h1>
            <p><strong>Sessions:</strong> {total_count} total, {verified_count} verified, {unverified_count} pending</p>
            
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr><th>Name</th><th>Phone</th><th>Status</th><th>Code</th><th>Created</th></tr>
                {sessions_html}
            </table>
            
            <h3>Quick Links:</h3>
            <ul>
                <li><a href="/selfie_booth/">← Back to Kiosk</a></li>
                <li><a href="/selfie_booth/mobile">Mobile Registration Page</a></li>
                <li><a href="/selfie_booth/health">Health Check</a></li>
            </ul>
        </body>
        </html>
        """
    
    # Health check
    @app.route('/selfie_booth/health')
    @app.route('/health')
    def health():
        try:
            if hasattr(session_manager, 'get_connection'):
                db_conn = session_manager.get_connection()
                db_status = "connected" if db_conn else "disconnected"
                if db_conn:
                    db_conn.close()
            else:
                db_status = "sqlite"
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': db_status,
                'config': {
                    'messaging_service': 'local'
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # Test endpoint
    @app.route('/selfie_booth/test')
    @app.route('/test')
    def test_route():
        return jsonify({
            'status': 'success',
            'message': 'Routes are working!',
            'timestamp': datetime.now().isoformat(),
            'session_manager': str(type(session_manager)),
            'messaging_factory': str(type(messaging_factory)),
            'session_data': dict(session) if session else 'No session'
        })
    
    # Debug route to see all registered routes
    @app.route('/selfie_booth/debug_routes')
    @app.route('/debug_routes')
    def debug_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': str(rule)
            })
        return jsonify({
            'total_routes': len(routes),
            'routes': routes
        })
    
    route_count = len([rule for rule in app.url_map.iter_rules() if rule.endpoint != 'static'])
    print(f"✅ Successfully registered {route_count} routes")
    
    return app