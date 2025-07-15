#!/usr/bin/env python3
"""
Routes module for Selfie Booth application - WITH SECURITY ENHANCEMENTS
Contains all Flask routes and request handlers
"""

import os
import random
import base64
import re
import magic
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, session, redirect
from markupsafe import escape

from database import SessionManager
from messaging import MessagingServiceFactory
from templates import (
    KIOSK_PAGE, MOBILE_PAGE, KIOSK_VERIFICATION_PAGE, 
    KIOSK_CAMERA_PAGE, PHOTO_SESSION_PAGE, VERIFY_PAGE
)

# Security: Rate limiting implementation
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

# Security: Input validation functions
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


def create_routes(app, session_manager, upload_folder):
    """Create and register all routes with the Flask app"""
    
    @app.route('/')
    def kiosk():
        """Kiosk display page - shows QR code, verification code, or camera"""
        # Clean up old sessions first
        session_manager.cleanup_old_sessions()
        
        debug_status = "Default QR screen"
        current_time = datetime.now().strftime('%H:%M:%S')
        last_cleanup = "Just now"
        
        # Debug: Show all sessions
        all_sessions = session_manager.get_all_sessions_debug()
        print(f"🔍 Debug - All sessions: {all_sessions}")
        
        # Check if there's a verified user ready for photo
        verified_result = session_manager.get_verified_session()
        
        if verified_result:
            first_name, session_id, created_at = verified_result
            print(f"🔍 Found verified session: {first_name}, {session_id}, {created_at}")
            try:
                # Handle different timestamp formats
                if 'T' in created_at:
                    created_time = datetime.fromisoformat(created_at)
                else:
                    created_time = datetime.fromisoformat(created_at.replace(' ', 'T'))
                
                time_diff = datetime.now() - created_time
                if time_diff < timedelta(minutes=3):
                    debug_status = f"Camera mode for {first_name} (verified {time_diff.total_seconds():.0f}s ago)"
                    print(f"🎥 Showing camera interface for {first_name}")
                    return render_template_string(KIOSK_CAMERA_PAGE, name=first_name, session_id=session_id)
                else:
                    print(f"⏰ Verified session for {first_name} expired ({time_diff.total_seconds():.0f}s ago)")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error parsing timestamp {created_at}: {e}")
        
        # Check if there's a recent registration waiting for verification
        unverified_result = session_manager.get_unverified_session()
        
        if unverified_result:
            first_name, verification_code, created_at = unverified_result
            print(f"🔍 Found unverified session: {first_name}, {verification_code}, {created_at}")
            try:
                # Handle different timestamp formats
                if 'T' in created_at:
                    created_time = datetime.fromisoformat(created_at)
                else:
                    created_time = datetime.fromisoformat(created_at.replace(' ', 'T'))
                
                time_diff = datetime.now() - created_time
                if time_diff < timedelta(minutes=2):
                    debug_status = f"Verification for {first_name} (registered {time_diff.total_seconds():.0f}s ago)"
                    print(f"🔢 Showing verification code {verification_code} for {first_name}")
                    return render_template_string(KIOSK_VERIFICATION_PAGE, 
                                                name=first_name, 
                                                code=verification_code)
                else:
                    print(f"⏰ Unverified session for {first_name} expired ({time_diff.total_seconds():.0f}s ago)")
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error parsing timestamp {created_at}: {e}")
        
        # Show normal kiosk page (default state)
        print(f"🏠 Showing default kiosk page - No active sessions found")
        base_url = request.host_url.rstrip('/')
        return render_template_string(KIOSK_PAGE, 
                                    base_url=base_url,
                                    debug_status=debug_status,
                                    current_time=current_time,
                                    last_cleanup=last_cleanup)

    @app.route('/mobile')
    def mobile():
        """Mobile registration page - accessed via QR code"""
        return render_template_string(MOBILE_PAGE)

    @app.route('/register', methods=['POST'])
    @rate_limit(max_requests=5, window_minutes=1)  # Prevent registration spam
    def register():
        """Register a new user session with enhanced validation"""
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
        
        # Generate verification code
        verification_code = str(random.randint(100000, 999999))
        
        # Create session
        session_id = session_manager.create_session(
            first_name, 
            clean_phone,  # Use sanitized phone number
            email, 
            verification_code
        )
        
        session['session_id'] = session_id
        
        print(f"📝 New registration: {first_name} - Code: {verification_code} - Session: {session_id}")
        
        return jsonify({'success': True})

    @app.route('/photo_session')
    def photo_session():
        """Photo session page for mobile users"""
        if 'session_id' not in session:
            return redirect('/mobile')
        
        # Check if session exists and is verified
        result = session_manager.get_session_by_id(session['session_id'])
        
        if not result:
            return redirect('/mobile')
        
        if not result[6]:  # verified column
            return redirect('/verify')
        
        return render_template_string(PHOTO_SESSION_PAGE, session_id=session['session_id'])

    @app.route('/check_photo')
    @rate_limit(max_requests=30, window_minutes=1)  # Allow frequent polling but prevent abuse
    def check_photo():
        """Check if photo is ready for a session"""
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'photo_ready': False, 'error': 'No session ID'})
        
        result = session_manager.get_photo_data(session_id)
        
        if result and result[0]:  # photo_ready is True
            return jsonify({'photo_ready': True, 'photo_data': result[1]})
        else:
            return jsonify({'photo_ready': False})

    @app.route('/keep_photo', methods=['POST'])
    @rate_limit(max_requests=3, window_minutes=1)  # Prevent photo sending spam
    def keep_photo():
        """Keep and send the photo to the user"""
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        # Get session data
        result = session_manager.get_session_data(session_id)
        
        if not result:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        phone, first_name, email, photo_data_b64 = result
        
        try:
            # Decode photo data
            photo_data = base64.b64decode(photo_data_b64)
            
            # Send photo using configured messaging service
            messaging_service = MessagingServiceFactory.create_service(upload_folder=upload_folder)
            message = f"Hi {first_name}! Here's your selfie from the photo booth. Reply 'background' to change the background!"
            
            # Get appropriate recipient
            recipient = MessagingServiceFactory.get_recipient_for_service(
                messaging_service, phone, email, session_id
            )
            
            success, details = messaging_service.send_photo(recipient, photo_data, message)
            
            if success:
                # Save photo file locally too
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                photo_filename = f"selfie_{session_id}_{timestamp}.jpg"
                photo_path = os.path.join(upload_folder, photo_filename)
                
                with open(photo_path, 'wb') as f:
                    f.write(photo_data)
                
                # Clean up this completed session
                session_manager.delete_session(session_id)
                
                print(f"📸 Photo sent successfully for {first_name}")
                return jsonify({'success': True, 'message': details})
            else:
                return jsonify({'success': False, 'error': details})
                
        except Exception as e:
            app.logger.error(f"Photo sending error: {str(e)}")
            return jsonify({'success': False, 'error': 'Photo processing failed'})

    @app.route('/retake_photo', methods=['POST'])
    @rate_limit(max_requests=5, window_minutes=1)  # Prevent retake spam
    def retake_photo():
        """Reset photo status for retake"""
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session ID'})
        
        # Reset photo status for retake
        session_manager.reset_photo_for_retake(session_id)
        
        print(f"🔄 Photo retake requested for session {session_id}")
        return jsonify({'success': True})

    @app.route('/verify')
    def verify():
        """Verification page for mobile users"""
        if 'session_id' not in session:
            return redirect('/mobile')
        
        # Check if session exists and is not verified
        result = session_manager.get_session_by_id(session['session_id'])
        
        if not result:
            return redirect('/mobile')
        
        if result[6]:  # Already verified
            return redirect('/')
        
        return render_template_string(VERIFY_PAGE)

    @app.route('/verify', methods=['POST'])
    @rate_limit(max_requests=10, window_minutes=1)  # Prevent verification brute force
    def verify_code():
        """Verify the code entered by user"""
        if 'session_id' not in session:
            return jsonify({'success': False, 'error': 'Session expired'})
        
        data = request.get_json()
        entered_code = data.get('code', '').strip()
        
        # Sanitize code input
        if not entered_code.isdigit() or len(entered_code) != 6:
            return jsonify({'success': False, 'error': 'Invalid code format'})
        
        # Verify code
        success, first_name = session_manager.verify_session(session['session_id'], entered_code)
        
        if success:
            print(f"✅ Verification successful for {first_name} - Session: {session['session_id']}")
            return jsonify({'success': True, 'redirect': '/photo_session'})
        else:
            print(f"❌ Verification failed for session {session.get('session_id')} - Code: {entered_code}")
            return jsonify({'success': False, 'error': 'Invalid code'})

    @app.route('/upload_photo', methods=['POST'])
    @rate_limit(max_requests=3, window_minutes=1)  # Prevent photo upload spam
    def upload_photo():
        """Upload and store photo from kiosk camera with enhanced validation"""
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo uploaded'})
        
        photo = request.files['photo']
        if photo.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'})
        
        # Get session_id from form data (sent from kiosk) or session (from mobile)
        session_id = request.form.get('session_id') or session.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session found'})
        
        # Get user info
        result = session_manager.get_session_by_id(session_id)
        
        if not result or not result[6]:  # Not verified
            return jsonify({'success': False, 'error': 'Not verified'})
        
        try:
            # Read photo data
            photo_data = photo.read()
            
            # Enhanced file validation
            is_valid, error_msg = validate_image_file(photo_data)
            if not is_valid:
                return jsonify({'success': False, 'error': error_msg})
            
            # Convert to base64 for storage
            photo_data_b64 = base64.b64encode(photo_data).decode('utf-8')
            
            # Store photo data in database and mark as ready
            session_manager.update_photo_data(session_id, photo_data_b64)
            
            print(f"📸 Photo captured and ready for review - Session: {session_id}")
            return jsonify({'success': True, 'message': 'Photo ready for review on mobile device'})
                
        except Exception as e:
            app.logger.error(f"Photo upload error: {str(e)}")
            return jsonify({'success': False, 'error': 'Upload processing failed'})

    @app.route('/trigger_photo', methods=['POST'])
    def trigger_photo():
        """Manual photo trigger from kiosk (for testing or manual operation)"""
        # Check if there's a verified user ready for photo
        verified_result = session_manager.get_verified_session()
        
        if verified_result:
            # Set the session and redirect to camera
            session['session_id'] = verified_result[1]  # session_id
            return jsonify({'success': True, 'redirect': '/camera'})
        else:
            return jsonify({'success': False, 'error': 'No verified user ready'})

    @app.route('/admin/reset_sessions', methods=['POST'])
    @rate_limit(max_requests=5, window_minutes=1)  # Prevent admin spam
    def reset_sessions():
        """Reset all sessions (for debugging)"""
        try:
            deleted_count = session_manager.reset_all_sessions()
            
            print(f"🔄 Reset {deleted_count} sessions")
            return jsonify({'success': True, 'message': f'Reset {deleted_count} sessions'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/admin/config')
    def admin_config():
        """Admin configuration page"""
        # Get session statistics
        total_count, verified_count, unverified_count = session_manager.get_session_stats()
        
        # Get recent sessions for debugging
        recent_sessions = session_manager.get_recent_sessions()
        
        sessions_html = ""
        if recent_sessions:
            sessions_html = "<h3>Recent Sessions (Last 10):</h3><table border='1' style='border-collapse: collapse; width: 100%;'>"
            sessions_html += "<tr><th>Name</th><th>Phone</th><th>Verified</th><th>Code</th><th>Photo</th><th>Created</th><th>Age</th></tr>"
            
            for session_data in recent_sessions:
                session_id, name, phone, verified, code, photo_ready, created_at = session_data
                try:
                    if 'T' in created_at:
                        created_time = datetime.fromisoformat(created_at)
                    else:
                        created_time = datetime.fromisoformat(created_at.replace(' ', 'T'))
                    age = datetime.now() - created_time
                    age_str = f"{age.total_seconds():.0f}s ago"
                except:
                    age_str = "Unknown"
                
                verified_str = "✅ Yes" if verified else "❌ No"
                photo_str = "📸 Ready" if photo_ready else "⏳ Waiting"
                sessions_html += f"<tr><td>{escape(name)}</td><td>{escape(phone)}</td><td>{verified_str}</td><td>{code}</td><td>{photo_str}</td><td>{created_at}</td><td>{age_str}</td></tr>"
            
            sessions_html += "</table>"
        else:
            sessions_html = "<p><em>No sessions found</em></p>"
        
        return f'''
        <h2>Selfie Booth Configuration</h2>
        <p><strong>Current messaging service:</strong> {escape(os.getenv('MESSAGING_SERVICE', 'local'))}</p>
        <p><strong>Active sessions:</strong> {total_count} total ({verified_count} verified, {unverified_count} unverified)</p>
        <p><strong>Current time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div style="margin: 20px 0;">
            <button onclick="resetSessions()" style="background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">
                🔄 Reset All Sessions
            </button>
            <button onclick="location.reload()" style="background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                🔄 Refresh Page
            </button>
        </div>
        
        {sessions_html}
        
        <h3>URL Structure:</h3>
        <ul>
            <li><strong>Kiosk Display:</strong> <a href="/">http://localhost:5001/</a> (shows QR code)</li>
            <li><strong>Mobile Registration:</strong> <a href="/mobile">http://localhost:5001/mobile</a> (for phones)</li>
            <li><strong>Admin Config:</strong> <a href="/admin/config">http://localhost:5001/admin/config</a></li>
        </ul>
        
        <h3>To switch messaging services, set environment variables:</h3>
        <ul>
            <li><strong>Local Storage:</strong> MESSAGING_SERVICE=local (default)</li>
            <li><strong>Twilio:</strong> MESSAGING_SERVICE=twilio, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER</li>
            <li><strong>Email:</strong> MESSAGING_SERVICE=email, EMAIL_ADDRESS, EMAIL_PASSWORD</li>
        </ul>
        
        <h3>QR Code Setup:</h3>
        <p>Generate a QR code pointing to: <strong>http://your-domain.com/mobile</strong></p>
        
        <h3>Debugging Steps:</h3>
        <ol>
            <li><strong>Test Mobile Registration:</strong> <a href="/mobile" target="_blank">Open mobile page</a></li>
            <li><strong>Check Kiosk Display:</strong> <a href="/" target="_blank">Open kiosk page</a></li>
            <li><strong>Monitor Server Console:</strong> Watch the terminal for debug messages</li>
            <li><strong>Reset if Stuck:</strong> Use the reset button above</li>
        </ol>
        
        <script>
            async function resetSessions() {{
                if (confirm('Are you sure you want to reset all sessions?')) {{
                    try {{
                        const response = await fetch('/admin/reset_sessions', {{ method: 'POST' }});
                        const result = await response.json();
                        
                        if (result.success) {{
                            alert('Sessions reset successfully!');
                            location.reload();
                        }} else {{
                            alert('Error: ' + result.error);
                        }}
                    }} catch (error) {{
                        alert('Error resetting sessions');
                    }}
                }}
            }}
            
            // Auto-refresh every 5 seconds
            setTimeout(() => {{
                location.reload();
            }}, 5000);
        </script>
        '''