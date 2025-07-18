#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python
"""
Flask application for Selfie Booth API
Complete version with QR code generation endpoint
"""

import sys
import os
import json
import base64
from datetime import datetime
from io import BytesIO
from flask import redirect, request

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
app.config['SECRET_KEY'] = 'selfie-booth-secret-key-change-in-production'
app.config['DEBUG'] = False

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

# ============ Core API Endpoints ============

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
                '/qr_code'
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

# ============ Future Photo Endpoints ============

@app.route('/upload_photo', methods=['POST', 'OPTIONS'])
def upload_photo():
    """Photo upload endpoint (placeholder)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({
        'success': False,
        'error': 'Photo upload not yet implemented'
    }), 501

@app.route('/check_photo', methods=['GET'])
def check_photo():
    """Photo status check endpoint (placeholder)"""
    return jsonify({
        'success': False,
        'error': 'Photo check not yet implemented'
    }), 501

@app.route('/keep_photo', methods=['POST', 'OPTIONS'])
def keep_photo():
    """Keep photo endpoint (placeholder)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({
        'success': False,
        'error': 'Keep photo not yet implemented'
    }), 501

@app.route('/retake_photo', methods=['POST', 'OPTIONS'])
def retake_photo():
    """Retake photo endpoint (placeholder)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({
        'success': False,
        'error': 'Retake photo not yet implemented'
    }), 501

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

# ============ Admin Endpoints (Placeholders) ============

@app.route('/admin/stats')
def admin_stats():
    """Admin statistics endpoint"""
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
def admin_sessions():
    """Admin sessions list endpoint"""
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
def admin_reset():
    """Admin reset sessions endpoint"""
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

@app.route('/admin/history')
def admin_history():
    """Admin session history endpoint"""
    try:
        history = load_session_history()
        
        # Sort by most recent first
        history.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
        
        # Optional pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_history = history[start:end]
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': paginated_history,
                'total': len(history),
                'page': page,
                'per_page': per_page,
                'total_pages': (len(history) + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'History retrieval failed: {str(e)}'
        }), 500

@app.route('/selfie_booth/<kiosk_number>')
def kiosk_short_url(kiosk_number):
    try:
        num = int(kiosk_number)
        if not (1 <= num <= 50):
            return 'Invalid kiosk number', 404
    except ValueError:
        return 'Invalid kiosk number', 404
    # Build the absolute redirect URL
    base_url = request.url_root.rstrip('/')
    target = f'{base_url}/selfie_booth/mobile.html?tablet_id=KIOSK{num}&location=lobby'
    return redirect(target)

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
    print("🚀 Starting Flask app locally...")
    app.run(debug=True, host='0.0.0.0', port=5000)