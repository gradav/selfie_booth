#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python
"""
Flask application for Selfie Booth API
Complete version with QR code generation endpoint
"""

import sys
import os
from datetime import datetime
from io import BytesIO

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
        
        # For testing, accept any 6-digit code
        if len(code) == 6 and code.isdigit():
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

# ============ Admin Endpoints (Placeholders) ============

@app.route('/admin/stats')
def admin_stats():
    """Admin statistics endpoint (placeholder)"""
    return jsonify({
        'success': True,
        'data': {
            'total_sessions': 0,
            'active_sessions': 0,
            'photos_taken': 0,
            'photos_sent': 0
        }
    }), 200

@app.route('/admin/sessions')
def admin_sessions():
    """Admin sessions list endpoint (placeholder)"""
    return jsonify({
        'success': True,
        'data': {
            'sessions': [],
            'total': 0
        }
    }), 200

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    """Admin reset sessions endpoint (placeholder)"""
    return jsonify({
        'success': True,
        'data': {
            'deleted_count': 0,
            'message': 'Reset not yet implemented'
        }
    }), 200

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