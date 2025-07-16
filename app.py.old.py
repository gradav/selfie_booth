#!/usr/bin/env python3
"""
Selfie Booth - InMotion Hosting Version (Optimized with Client-Side QR Generation)
Complete web-hosted selfie booth application with tablet clients
Optimized QR code generation and refresh logic
"""

import os
import sys
import random
import base64
import re
import uuid
import secrets
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from markupsafe import escape


def get_short_url_for_tablet(tablet_id, base_url):
    """Map tablet IDs to short URLs"""
    tablet_mapping = {
        'TABLET1': '1',
        'TABLET2': '2', 
        'TABLET3': '3',
        'TABLET4': '4',
        'f4d1e4b5': '1',  # Your current test tablet
    }
    
    short_path = tablet_mapping.get(tablet_id, '1')  # Default to '1'
    return f"{base_url}/selfie_booth/{short_path}"

# Add current directory to Python path for InMotion
sys.path.insert(0, os.path.dirname(__file__))

# Database imports
try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql.connector = None

# Messaging imports
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

# Configuration class
class Config:
    """Web hosting configuration"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Database configuration (InMotion MySQL)
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'test')
    DB_USER = os.environ.get('DB_USER', 'test')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'test')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Application settings
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Messaging configuration
    MESSAGING_SERVICE = os.environ.get('MESSAGING_SERVICE', 'local')
    
    # Twilio settings
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')

# Database Manager
class CloudSessionManager:
    """Manages MySQL database sessions for web hosting"""
    
    def __init__(self, host, database, user, password, port=3306):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        if not mysql.connector:
            return None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def init_db(self):
        """Initialize database tables"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20),
            first_name VARCHAR(100),
            email VARCHAR(255),
            verification_code VARCHAR(6),
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            photo_path VARCHAR(500),
            photo_data LONGTEXT,
            photo_ready BOOLEAN DEFAULT FALSE,
            tablet_id VARCHAR(100),
            location VARCHAR(100)
        )
        """
        
        try:
            cursor.execute(create_table_query)
            connection.commit()
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()
            connection.close()
    
    def create_session(self, first_name, phone, email, verification_code, tablet_id=None, location=None):
        """Create a new session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        session_id = secrets.token_urlsafe(16)
        
        query = """
        INSERT INTO sessions (session_id, phone, first_name, email, verification_code, verified, tablet_id, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            cursor.execute(query, (session_id, phone, first_name, email, verification_code, False, tablet_id, location))
            connection.commit()
            return session_id
        except Error as e:
            print(f"Error creating session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_session_by_id(self, session_id):
        """Get session by ID"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        query = "SELECT * FROM sessions WHERE session_id = %s"
        
        try:
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error getting session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def verify_session(self, session_id, verification_code):
        """Verify session with code"""
        connection = self.get_connection()
        if not connection:
            return False, None
        
        cursor = connection.cursor()
        
        check_query = "SELECT first_name FROM sessions WHERE session_id = %s AND verification_code = %s"
        cursor.execute(check_query, (session_id, verification_code))
        result = cursor.fetchone()
        
        if result:
            update_query = "UPDATE sessions SET verified = TRUE WHERE session_id = %s"
            cursor.execute(update_query, (session_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return True, result[0]
        else:
            cursor.close()
            connection.close()
            return False, None
    
    def get_verified_session(self, tablet_id=None):
        """Get most recent verified session for a tablet"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        
        if tablet_id:
            query = """
            SELECT first_name, session_id, created_at FROM sessions 
            WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL) 
            AND tablet_id = %s
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query, (tablet_id,))
        else:
            query = """
            SELECT first_name, session_id, created_at FROM sessions 
            WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL)
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query)
        
        try:
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error getting verified session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_unverified_session(self, tablet_id=None):
        """Get most recent unverified session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        
        if tablet_id:
            query = """
            SELECT first_name, verification_code, created_at FROM sessions 
            WHERE verified = FALSE AND tablet_id = %s
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query, (tablet_id,))
        else:
            query = """
            SELECT first_name, verification_code, created_at FROM sessions 
            WHERE verified = FALSE
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query)
        
        try:
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error getting unverified session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def cleanup_old_sessions(self):
        """Clean up sessions older than 30 minutes"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        
        cleanup_query = """
        DELETE FROM sessions 
        WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 MINUTE)
        """
        
        try:
            cursor.execute(cleanup_query)
            deleted_count = cursor.rowcount
            connection.commit()
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old sessions")
        except Error as e:
            print(f"Error cleaning up sessions: {e}")
        finally:
            cursor.close()
            connection.close()
    
    def update_photo_data(self, session_id, photo_data_b64):
        """Update session with photo data and mark as ready"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET photo_data = %s, photo_ready = TRUE 
            WHERE session_id = %s
        ''', (photo_data_b64, session_id))
        connection.commit()
        cursor.close()
        connection.close()
    
    def get_photo_data(self, session_id):
        """Get photo data for a session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        cursor.execute('SELECT photo_ready, photo_data FROM sessions WHERE session_id = %s', (session_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    
    def get_session_data(self, session_id):
        """Get full session data including photo"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        cursor.execute('''
            SELECT phone, first_name, email, photo_data FROM sessions WHERE session_id = %s
        ''', (session_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    
    def reset_photo_for_retake(self, session_id):
        """Reset photo status for retake"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET photo_ready = FALSE, photo_data = NULL, photo_path = NULL 
            WHERE session_id = %s
        ''', (session_id,))
        connection.commit()
        cursor.close()
        connection.close()
    
    def delete_session(self, session_id):
        """Delete a completed session"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_id = %s', (session_id,))
        connection.commit()
        cursor.close()
        connection.close()
    
    def reset_all_sessions(self):
        """Reset all sessions"""
        connection = self.get_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        cursor.execute('DELETE FROM sessions')
        deleted_count = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return deleted_count
    
    def get_session_stats(self):
        """Get session statistics"""
        connection = self.get_connection()
        if not connection:
            return 0, 0, 0
        
        cursor = connection.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = TRUE')
        verified_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = FALSE')
        unverified_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        return total_count, verified_count, unverified_count
    
    def get_recent_sessions(self, limit=10):
        """Get recent sessions"""
        connection = self.get_connection()
        if not connection:
            return []
        
        cursor = connection.cursor()
        cursor.execute('''
            SELECT session_id, first_name, phone, verified, verification_code, created_at, photo_ready, 
                   email, photo_path, photo_data, tablet_id, location
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT %s
        ''', (limit,))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
    
    def get_session_state(self, tablet_id=None):
        """Get current session state for refresh optimization"""
        connection = self.get_connection()
        if not connection:
            return 'error'
        
        cursor = connection.cursor()
        
        # Check for verified session
        if tablet_id:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL) 
                AND tablet_id = %s AND created_at > DATE_SUB(NOW(), INTERVAL 3 MINUTE)
            """, (tablet_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL)
                AND created_at > DATE_SUB(NOW(), INTERVAL 3 MINUTE)
            """)
        
        verified_count = cursor.fetchone()[0]
        
        if verified_count > 0:
            cursor.close()
            connection.close()
            return 'camera'
        
        # Check for unverified session
        if tablet_id:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = FALSE AND tablet_id = %s 
                AND created_at > DATE_SUB(NOW(), INTERVAL 2 MINUTE)
            """, (tablet_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = FALSE
                AND created_at > DATE_SUB(NOW(), INTERVAL 2 MINUTE)
            """)
        
        unverified_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        if unverified_count > 0:
            return 'verification'
        
        return 'default'

# Rate limiting for web hosting
class WebRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key, max_requests=10, window_minutes=1):
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        return False

rate_limiter = WebRateLimiter()

def rate_limit(max_requests=10, window_minutes=1):
    """Rate limiting decorator"""
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

# Input validation functions
def sanitize_text_input(text, max_length=50):
    """Sanitize text input"""
    if not text:
        return ""
    sanitized = escape(text.strip())
    return str(sanitized)[:max_length]

def validate_phone_number(phone):
    """Validate phone number format"""
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
    """Get or create tablet identifier"""
    tablet_id = session.get('tablet_id')
    if not tablet_id:
        tablet_id = str(uuid.uuid4())[:8]
        session['tablet_id'] = tablet_id
    return tablet_id

def get_location():
    """Get location from URL parameter or session"""
    location = request.args.get('location') or session.get('location', 'default')
    session['location'] = location
    return location

# Simple messaging service for local storage
class LocalStorageService:
    """Local storage service for development/testing"""
    
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        
    def send_photo(self, identifier, photo_data, message):
        """Save photo locally"""
        try:
            filename = f"photo_{identifier}_{datetime.now().timestamp()}.jpg"
            filepath = os.path.join(self.upload_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(photo_data)
            
            return True, f"Photo saved locally: {filepath}"
        except Exception as e:
            return False, f"Local storage error: {str(e)}"

def get_messaging_service():
    """Get appropriate messaging service"""
    service_type = Config.MESSAGING_SERVICE
    
    if service_type == 'twilio' and TwilioClient and Config.TWILIO_ACCOUNT_SID:
        try:
            client = TwilioClient(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            return 'twilio', client
        except:
            pass
    
    return 'local', LocalStorageService(Config.UPLOAD_FOLDER)

# HTML Templates - OPTIMIZED WITH CLIENT-SIDE QR GENERATION
KIOSK_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Selfie Booth - Kiosk</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .kiosk-container {
            background: white;
            padding: 60px;
            border-radius: 30px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
            max-width: 800px;
            width: 90%;
        }
        h1 {
            color: #333;
            font-size: 48px;
            margin-bottom: 20px;
        }
        .qr-info {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            border: 3px solid #667eea;
        }
        .qr-container {
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }
        #qrcode {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .url {
            font-size: 20px;
            color: #667eea;
            word-break: break-all;
            margin: 15px 0;
            font-weight: bold;
        }
        .tablet-info {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }
        .instructions {
            text-align: left;
            max-width: 400px;
            margin: 0 auto;
        }
        .instructions ol {
            font-size: 16px;
            line-height: 1.6;
        }
        .instructions li {
            margin-bottom: 8px;
        }
        @media screen and (max-width: 1024px) {
            .kiosk-container { padding: 40px 20px; }
            h1 { font-size: 36px; }
            .qr-info { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="tablet-info">
        Tablet: {{ tablet_id }}<br>
        Location: {{ location }}<br>
        Status: <span id="status">Ready</span>
    </div>
    
    <div class="kiosk-container">
        <h1>📸 Selfie Booth</h1>
        <p style="font-size: 24px; color: #666;">Scan QR code or visit URL on your phone!</p>
        
        <div class="qr-info">
            <div style="font-size: 18px; margin-bottom: 15px;">📱 Scan QR Code:</div>
            <div class="qr-container">
                <div id="qrcode"></div>
            </div>
            <div style="font-size: 16px; margin-top: 15px;">Or visit directly:</div>
            <div class="url">{{ mobile_url }}</div>
        </div>
        
        <div style="margin-top: 40px;">
            <div style="font-size: 18px; margin-bottom: 15px;">📋 Instructions:</div>
            <div class="instructions">
                <ol>
                    <li>Scan QR code with phone camera</li>
                    <li>Fill out registration form</li>
                    <li>Enter verification code from this screen</li>
                    <li>Smile for your photo!</li>
                </ol>
            </div>
        </div>
    </div>

    <!-- QR Code Library -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrious/4.0.2/qrious.min.js"></script>
    
    <script>
        // Generate QR code on page load
        function generateQRCode() {
            const qrContainer = document.getElementById('qrcode');
            
            // Clear any existing QR code
            qrContainer.innerHTML = '';
            
            // Create new QR code
            const qr = new QRious({
                element: document.createElement('canvas'),
                value: '{{ mobile_url }}',
                size: 200,
                level: 'M'
            });
            
            qrContainer.appendChild(qr.canvas);
        }
        
        // Smart refresh - only reload when session state changes
        let lastSessionState = '';
        let refreshCount = 0;
        
        async function checkForUpdates() {
            try {
                const response = await fetch('/selfie_booth/session_check?tablet_id={{ tablet_id }}');
                const data = await response.json();
                const currentState = data.session_state;
                
                // Update status indicator
                document.getElementById('status').textContent = currentState === 'default' ? 'Ready' : 
                    currentState === 'verification' ? 'Verifying' : 
                    currentState === 'camera' ? 'Photo Session' : 'Ready';
                
                // Only reload if session state actually changed and it's not the default state
                if (lastSessionState && lastSessionState !== currentState && currentState !== 'default') {
                    console.log(`Session state changed from ${lastSessionState} to ${currentState} - reloading`);
                    location.reload();
                }
                
                lastSessionState = currentState;
                refreshCount++;
                
                // Debug info
                console.log(`Check #${refreshCount}: Session state = ${currentState}`);
                
            } catch (error) {
                console.error('Session check failed:', error);
                // On error, show offline status
                document.getElementById('status').textContent = 'Offline';
            }
        }
        
        // Initialize QR code on page load
        generateQRCode();
        
        // Start session state checking
        setInterval(checkForUpdates, 3000);
        
        // Initial state check
        checkForUpdates();
        
        // Regenerate QR code if it gets corrupted (fallback)
        setInterval(() => {
            const qrContainer = document.getElementById('qrcode');
            if (!qrContainer.hasChildNodes() || qrContainer.children.length === 0) {
                console.log('QR code missing, regenerating...');
                generateQRCode();
            }
        }, 10000);
    </script>
</body>
</html>
'''

MOBILE_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Selfie Booth - Registration</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 400px;
            width: 100%;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; color: #555; font-weight: bold; }
        input[type="text"], input[type="tel"], input[type="email"] {
            width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px;
            font-size: 16px; box-sizing: border-box;
        }
        input:focus { border-color: #667eea; outline: none; }
        .checkbox-group { display: flex; align-items: center; margin-bottom: 20px; }
        .checkbox-group input { margin-right: 10px; }
        .submit-btn {
            width: 100%; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 8px; font-size: 18px; cursor: pointer;
            transition: transform 0.2s;
        }
        .submit-btn:hover { transform: translateY(-2px); }
        .submit-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .error { color: #e74c3c; margin-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Selfie Booth</h1>
        
        <form id="userForm">
            <input type="hidden" name="tablet_id" value="{{ tablet_id }}">
            <input type="hidden" name="location" value="{{ location }}">
            
            <div class="form-group">
                <label for="firstName">First Name *</label>
                <input type="text" id="firstName" name="firstName" required>
            </div>
            
            <div class="form-group">
                <label for="phone">Phone Number *</label>
                <input type="tel" id="phone" name="phone" placeholder="(555) 123-4567" required>
            </div>
            
            <div class="form-group">
                <label for="email">Email (Optional)</label>
                <input type="email" id="email" name="email">
            </div>
            
            <div class="checkbox-group">
                <input type="checkbox" id="consent" name="consent" required>
                <label for="consent">I agree to receive my photo via text</label>
            </div>
            
            <button type="submit" class="submit-btn" id="submitBtn">Start Photo Session</button>
            <div id="error" class="error"></div>
        </form>
    </div>

    <script>
        document.getElementById('userForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const errorDiv = document.getElementById('error');
            
            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Registering...';
            errorDiv.textContent = '';
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/selfie_booth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    submitBtn.textContent = 'Success! Redirecting...';
                    window.location.href = '/selfie_booth/verify';
                } else {
                    errorDiv.textContent = result.error;
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Start Photo Session';
                }
            } catch (error) {
                errorDiv.textContent = 'Network error. Please try again.';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Start Photo Session';
            }
        });
    </script>
</body>
</html>
'''

VERIFY_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enter Verification Code</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 400px;
            width: 100%;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 20px; }
        .instruction {
            background: #e8f4f8;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
        .code-input {
            font-size: 24px;
            text-align: center;
            padding: 15px;
            border: 3px solid #ddd;
            border-radius: 10px;
            width: 200px;
            margin: 20px 0;
            letter-spacing: 5px;
        }
        .code-input:focus { border-color: #667eea; outline: none; }
        .verify-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .verify-btn:hover { transform: translateY(-2px); }
        .verify-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .error { color: #e74c3c; margin-top: 15px; }
        .success { color: #27ae60; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Enter Verification Code</h1>
        
        <div class="instruction">
            <strong>Look at the kiosk screen</strong> for your 6-digit verification code
        </div>
        
        <form id="verifyForm">
            <input type="text" id="codeInput" class="code-input" maxlength="6" placeholder="000000" required>
            <br>
            <button type="submit" class="verify-btn" id="verifyBtn">Verify Code</button>
            <div id="message"></div>
        </form>
    </div>

    <script>
        const codeInput = document.getElementById('codeInput');
        const verifyBtn = document.getElementById('verifyBtn');
        const messageDiv = document.getElementById('message');
        
        // Auto-focus on input
        codeInput.focus();
        
        // Format input as numbers only
        codeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
        
        document.getElementById('verifyForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const code = codeInput.value;
            
            if (code.length !== 6) {
                messageDiv.innerHTML = '<div class="error">Please enter a 6-digit code</div>';
                return;
            }
            
            verifyBtn.disabled = true;
            verifyBtn.textContent = 'Verifying...';
            messageDiv.innerHTML = '';
            
            try {
                const response = await fetch('/selfie_booth/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    messageDiv.innerHTML = '<div class="success">✅ Verified! Redirecting...</div>';
                    setTimeout(() => {
                        window.location.href = result.redirect || '/selfie_booth/photo_session';
                    }, 1000);
                } else {
                    messageDiv.innerHTML = '<div class="error">❌ ' + result.error + '</div>';
                    verifyBtn.disabled = false;
                    verifyBtn.textContent = 'Verify Code';
                    codeInput.focus();
                    codeInput.select();
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="error">❌ Network error</div>';
                verifyBtn.disabled = false;
                verifyBtn.textContent = 'Verify Code';
            }
        });
    </script>
</body>
</html>
'''

PHOTO_SESSION_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo Session - Selfie Booth</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 20px; }
        .status {
            font-size: 18px;
            margin: 20px 0;
            padding: 20px;
            border-radius: 10px;
        }
        .waiting {
            background: #e8f4f8;
            color: #2c3e50;
            border-left: 4px solid #3498db;
        }
        .photo-container {
            margin: 30px 0;
            display: none;
        }
        .photo {
            max-width: 100%;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .button-group {
            display: none;
            gap: 15px;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        .btn {
            flex: 1;
            min-width: 120px;
            padding: 15px 25px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .btn-keep {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
        }
        .btn-retake {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .success-msg {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Photo Session</h1>
        
        <div id="waitingStatus" class="status waiting">
            <div>Look at the kiosk screen - your photo session is starting!</div>
            <div class="spinner"></div>
            <div>Waiting for photo to be taken...</div>
        </div>
        
        <div id="photoContainer" class="photo-container">
            <img id="photoImage" class="photo" alt="Your selfie">
        </div>
        
        <div id="buttonGroup" class="button-group">
            <button id="keepBtn" class="btn btn-keep">✅ Send to Phone</button>
            <button id="retakeBtn" class="btn btn-retake">🔄 Retake</button>
        </div>
        
        <div id="successMessage" class="success-msg" style="display: none;">
            <strong>Photo sent successfully!</strong><br>
            Check your messages for your selfie.
        </div>
    </div>

    <script>
        let sessionId = "{{ session_id }}";
        let photoCheckInterval;
        
        // Start checking for photo immediately
        startPhotoCheck();
        
        function startPhotoCheck() {
            photoCheckInterval = setInterval(checkForPhoto, 2000);
        }
        
        function stopPhotoCheck() {
            if (photoCheckInterval) {
                clearInterval(photoCheckInterval);
                photoCheckInterval = null;
            }
        }
        
        async function checkForPhoto() {
            try {
                const response = await fetch(`/selfie_booth/check_photo?session_id=${sessionId}`);
                const result = await response.json();
                
                if (result.photo_ready) {
                    stopPhotoCheck();
                    showPhoto(result.photo_data);
                }
            } catch (error) {
                console.error('Error checking for photo:', error);
            }
        }
        
        function showPhoto(photoData) {
            document.getElementById('waitingStatus').style.display = 'none';
            
            const photoContainer = document.getElementById('photoContainer');
            const photoImage = document.getElementById('photoImage');
            photoImage.src = `data:image/jpeg;base64,${photoData}`;
            photoContainer.style.display = 'block';
            
            document.getElementById('buttonGroup').style.display = 'flex';
        }
        
        // Keep photo button
        document.getElementById('keepBtn').addEventListener('click', async () => {
            const keepBtn = document.getElementById('keepBtn');
            const retakeBtn = document.getElementById('retakeBtn');
            
            keepBtn.disabled = true;
            retakeBtn.disabled = true;
            keepBtn.textContent = 'Sending...';
            
            try {
                const response = await fetch('/selfie_booth/keep_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('buttonGroup').style.display = 'none';
                    document.getElementById('successMessage').style.display = 'block';
                    
                    setTimeout(() => {
                        window.location.href = '/selfie_booth/mobile';
                    }, 3000);
                } else {
                    alert('Error sending photo: ' + result.error);
                    keepBtn.disabled = false;
                    retakeBtn.disabled = false;
                    keepBtn.textContent = '✅ Send to Phone';
                }
            } catch (error) {
                alert('Network error sending photo');
                keepBtn.disabled = false;
                retakeBtn.disabled = false;
                keepBtn.textContent = '✅ Send to Phone';
            }
        });
        
        // Retake photo button
        document.getElementById('retakeBtn').addEventListener('click', async () => {
            const keepBtn = document.getElementById('keepBtn');
            const retakeBtn = document.getElementById('retakeBtn');
            
            keepBtn.disabled = true;
            retakeBtn.disabled = true;
            retakeBtn.textContent = 'Starting Retake...';
            
            try {
                const response = await fetch('/selfie_booth/retake_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('photoContainer').style.display = 'none';
                    document.getElementById('buttonGroup').style.display = 'none';
                    document.getElementById('waitingStatus').style.display = 'block';
                    startPhotoCheck();
                } else {
                    alert('Error starting retake: ' + result.error);
                    keepBtn.disabled = false;
                    retakeBtn.disabled = false;
                    retakeBtn.textContent = '🔄 Retake';
                }
            } catch (error) {
                alert('Error starting retake');
                keepBtn.disabled = false;
                retakeBtn.disabled = false;
                retakeBtn.textContent = '🔄 Retake';
            }
        });
    </script>
</body>
</html>
'''

CAMERA_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Take Your Photo - Selfie Booth</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .greeting {
            background: white;
            padding: 30px 60px;
            border-radius: 25px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        .greeting h1 { color: #667eea; margin: 0; font-size: 48px; }
        .camera-container {
            background: white;
            padding: 40px;
            border-radius: 30px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 900px;
            width: 90%;
        }
        #video {
            width: 100%;
            max-width: 700px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        #canvas { display: none; }
        #photoDisplay {
            display: none;
            max-width: 700px;
            width: 100%;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .countdown {
            font-size: 120px;
            font-weight: bold;
            color: #e74c3c;
            margin: 30px 0;
            min-height: 140px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .controls { margin-top: 30px; }
        .photo-btn {
            padding: 25px 50px;
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 28px;
            cursor: pointer;
            margin: 15px;
            transition: transform 0.2s;
        }
        .photo-btn:hover { transform: translateY(-3px); }
        .photo-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            margin-top: 30px;
            font-size: 28px;
            font-weight: bold;
        }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        
        @media screen and (max-width: 1024px) {
            .greeting h1 { font-size: 36px; }
            .camera-container { padding: 20px; }
            .countdown { font-size: 80px; }
            .photo-btn { 
                padding: 20px 40px;
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="greeting">
        <h1>Hi {{ name }}, smile for the camera! 📸</h1>
    </div>
    
    <div class="camera-container">
        <video id="video" autoplay playsinline muted></video>
        <canvas id="canvas"></canvas>
        <img id="photoDisplay" alt="Your photo">
        <div id="countdown" class="countdown"></div>
        <div class="controls">
            <button id="photoBtn" class="photo-btn">Take Photo</button>
        </div>
        <div id="status" class="status"></div>
    </div>

    <script>
        let video, canvas, ctx, photoDisplay;
        let countdownInterval;
        const sessionId = "{{ session_id }}";
        
        async function initCamera() {
            video = document.getElementById('video');
            canvas = document.getElementById('canvas');
            photoDisplay = document.getElementById('photoDisplay');
            ctx = canvas.getContext('2d');
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        facingMode: 'user'
                    } 
                });
                video.srcObject = stream;
                
                // Auto-start countdown after 2 seconds
                setTimeout(() => {
                    if (!document.getElementById('photoBtn').disabled) {
                        startCountdown();
                    }
                }, 2000);
                
            } catch (err) {
                document.getElementById('status').innerHTML = '<div class="error">Camera access required. Please allow camera access and refresh.</div>';
                console.error('Camera error:', err);
            }
        }
        
        function startCountdown() {
            let count = 5;
            const countdownEl = document.getElementById('countdown');
            const photoBtn = document.getElementById('photoBtn');
            
            photoBtn.disabled = true;
            
            countdownInterval = setInterval(() => {
                if (count > 0) {
                    countdownEl.textContent = count;
                } else {
                    clearInterval(countdownInterval);
                    countdownEl.textContent = 'Say Cheese! 📸';
                    setTimeout(() => {
                        takePhoto();
                    }, 500);
                }
                count--;
            }, 1000);
        }
        
        async function takePhoto() {
            const countdownEl = document.getElementById('countdown');
            const statusEl = document.getElementById('status');
            
            // Set canvas size to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw the frame
            ctx.drawImage(video, 0, 0);
            
            // Get the image data URL
            const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8);
            
            // Hide video and show photo
            video.style.display = 'none';
            photoDisplay.src = imageDataUrl;
            photoDisplay.style.display = 'block';
            
            // Convert to blob for upload
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('photo', blob, 'selfie.jpg');
                formData.append('session_id', sessionId);
                
                countdownEl.textContent = '';
                statusEl.innerHTML = '<div class="success">📱 Processing your photo...</div>';
                
                try {
                    const response = await fetch('/selfie_booth/upload_photo', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusEl.innerHTML = '<div class="success">📱 Photo captured! Check your phone to review and send.</div>';
                        
                        // Return to kiosk after 8 seconds
                        setTimeout(() => {
                            window.location.href = '/selfie_booth/';
                        }, 8000);
                        
                    } else {
                        statusEl.innerHTML = '<div class="error">Failed to capture photo: ' + result.error + '</div>';
                        resetCamera();
                    }
                } catch (error) {
                    statusEl.innerHTML = '<div class="error">Network error. Please try again.</div>';
                    resetCamera();
                }
            }, 'image/jpeg', 0.8);
        }
        
        function resetCamera() {
            video.style.display = 'block';
            photoDisplay.style.display = 'none';
            document.getElementById('photoBtn').disabled = false;
            document.getElementById('countdown').textContent = '';
        }
        
        document.getElementById('photoBtn').addEventListener('click', startCountdown);
        
        // Initialize camera when page loads
        initCamera();
    </script>
</body>
</html>
'''

# Create Flask application
def create_app():
    """Create Flask application for web hosting"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Security headers
    @app.after_request
    def security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    return app

# Create Flask app instance
app = create_app()

# Initialize database
session_manager = CloudSessionManager(
    host=Config.DB_HOST,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD
)

# Routes
@app.route('/')
def kiosk():
    """Kiosk display page with optimized refresh logic"""
    tablet_id = get_tablet_id()
    location = get_location()
    
    session_manager.cleanup_old_sessions()
    
    # Check for verified session ready for photo
    verified_result = session_manager.get_verified_session(tablet_id)
    if verified_result:
        first_name, session_id, created_at = verified_result
        try:
            # Handle both datetime objects and strings
            if isinstance(created_at, datetime):
                created_time = created_at
            else:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_diff = datetime.now() - created_time
            if time_diff < timedelta(minutes=3):
                return render_template_string(CAMERA_PAGE, 
                                            name=first_name, 
                                            session_id=session_id)
        except:
            pass
    
    # Check for unverified session needing verification code
    unverified_result = session_manager.get_unverified_session(tablet_id)
    if unverified_result:
        first_name, verification_code, created_at = unverified_result
        try:
            # Handle both datetime objects and strings
            if isinstance(created_at, datetime):
                created_time = created_at
            else:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            time_diff = datetime.now() - created_time
            if time_diff < timedelta(minutes=2):
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Verification Code</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ 
                            text-align: center; 
                            padding: 100px; 
                            font-family: Arial; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            margin: 0;
                            min-height: 100vh;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            align-items: center;
                        }}
                        .verification-container {{
                            background: white;
                            padding: 80px;
                            border-radius: 30px;
                            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
                            max-width: 800px;
                        }}
                        h1 {{ color: #333; font-size: 42px; margin-bottom: 20px; }}
                        .user-greeting {{ color: #667eea; font-size: 28px; margin-bottom: 40px; }}
                        .code-display {{
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 60px;
                            border-radius: 25px;
                            margin: 40px 0;
                            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                        }}
                        .code {{
                            font-size: 96px;
                            margin: 20px;
                            letter-spacing: 20px;
                            font-weight: bold;
                        }}
                        .code-label {{
                            font-size: 24px;
                            margin-bottom: 10px;
                            opacity: 0.9;
                        }}
                    </style>
                </head>
                <body>
                    <div class="verification-container">
                        <h1>📱 Verification Required</h1>
                        <div class="user-greeting">Hi {first_name}!</div>
                        <div class="code-display">
                            <div class="code-label">Enter this code on your phone:</div>
                            <div class="code">{verification_code}</div>
                        </div>
                    </div>
                    <script>
                        // Smart refresh - check session state instead of full reload
                        setTimeout(() => {{
                            fetch('/selfie_booth/session_check?tablet_id={tablet_id}')
                                .then(r => r.json())
                                .then(data => {{
                                    if (data.session_state !== 'verification') {{
                                        location.reload();
                                    }} else {{
                                        location.reload(); // Still in verification, refresh to check timeout
                                    }}
                                }})
                                .catch(() => location.reload());
                        }}, 5000);
                    </script>
                </body>
                </html>
                """
        except:
            pass
    
    # Show default kiosk page with QR code
    base_url = request.host_url.rstrip('/')
    short_url = get_short_url_for_tablet(tablet_id, base_url)
    
    return render_template_string(KIOSK_PAGE,
                                tablet_id=tablet_id,
                                location=location,
                                mobile_url=short_url)

@app.route('/session_check')
@rate_limit(max_requests=100, window_minutes=1)  # High limit for frequent polling
def session_check():
    """Endpoint for checking session state without full page reload"""
    tablet_id = request.args.get('tablet_id')
    session_state = session_manager.get_session_state(tablet_id)
    
    return jsonify({
        'session_state': session_state,
        'timestamp': datetime.now().isoformat(),
        'tablet_id': tablet_id
    })

@app.route('/mobile')
def mobile():
    """Mobile registration page"""
    tablet_id = request.args.get('tablet_id') or get_tablet_id()
    location = request.args.get('location') or get_location()
    
    session['tablet_id'] = tablet_id
    session['location'] = location
    
    return render_template_string(MOBILE_PAGE, 
                                tablet_id=tablet_id,
                                location=location)

@app.route('/register', methods=['POST'])
@rate_limit(max_requests=50, window_minutes=1)  # Increased for testing
def register():
    """Register new user session"""
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

@app.route('/verify')
def verify_page():
    """Verification code entry page"""
    if 'session_id' not in session:
        return redirect(url_for('mobile'))
    
    return render_template_string(VERIFY_PAGE)

@app.route('/verify', methods=['POST'])
@rate_limit(max_requests=25, window_minutes=1)  # Increased for testing
def verify_code():
    """Verify entered code"""
    if 'session_id' not in session:
        return jsonify({'success': False, 'error': 'Session expired'})
    
    data = request.get_json()
    entered_code = data.get('code', '').strip()
    
    if not entered_code.isdigit() or len(entered_code) != 6:
        return jsonify({'success': False, 'error': 'Invalid code format'})
    
    success, first_name = session_manager.verify_session(session['session_id'], entered_code)
    
    if success:
        print(f"✅ Verification successful for {first_name}")
        return jsonify({'success': True, 'redirect': url_for('photo_session')})
    else:
        return jsonify({'success': False, 'error': 'Invalid code'})

@app.route('/photo_session')
def photo_session():
    """Photo session page for mobile users"""
    if 'session_id' not in session:
        return redirect(url_for('mobile'))
    
    result = session_manager.get_session_by_id(session['session_id'])
    if not result or not result[6]:  # not verified
        return redirect(url_for('verify_page'))
    
    return render_template_string(PHOTO_SESSION_PAGE, 
                                session_id=session['session_id'])

@app.route('/upload_photo', methods=['POST'])
@rate_limit(max_requests=15, window_minutes=1)  # Increased for testing
def upload_photo():
    """Upload photo from tablet camera"""
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo uploaded'})
    
    photo = request.files['photo']
    session_id = request.form.get('session_id') or session.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'No session found'})
    
    # Verify session exists and is verified
    result = session_manager.get_session_by_id(session_id)
    if not result or not result[6]:  # not verified
        return jsonify({'success': False, 'error': 'Session not verified'})
    
    try:
        photo_data = photo.read()
        
        # Basic validation
        if len(photo_data) > 16 * 1024 * 1024:  # 16MB limit
            return jsonify({'success': False, 'error': 'File too large'})
        
        # Convert to base64 for database storage
        photo_data_b64 = base64.b64encode(photo_data).decode('utf-8')
        
        # Store photo in database
        session_manager.update_photo_data(session_id, photo_data_b64)
        
        print(f"📸 Photo uploaded for session: {session_id}")
        return jsonify({'success': True, 'message': 'Photo ready for review'})
        
    except Exception as e:
        app.logger.error(f"Photo upload error: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload failed'})

@app.route('/check_photo')
@rate_limit(max_requests=30, window_minutes=1)
def check_photo():
    """Check if photo is ready for review"""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'photo_ready': False})
    
    result = session_manager.get_photo_data(session_id)
    
    if result and result[0]:  # photo_ready is True
        return jsonify({'photo_ready': True, 'photo_data': result[1]})
    else:
        return jsonify({'photo_ready': False})

@app.route('/keep_photo', methods=['POST'])
@rate_limit(max_requests=10, window_minutes=1)  # Increased for testing
def keep_photo():
    """Send photo to user via messaging service"""
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
        # Decode photo
        photo_data = base64.b64decode(photo_data_b64)
        
        # Send via messaging service (simplified for now)
        service_type, service = get_messaging_service()
        
        if service_type == 'local':
            success, details = service.send_photo(session_id, photo_data, f"Hi {first_name}! Here's your selfie!")
        else:
            # Twilio implementation would go here
            success, details = True, "Photo saved (Twilio not implemented yet)"
        
        if success:
            # Save locally and clean up session
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_filename = f"selfie_{session_id}_{timestamp}.jpg"
            photo_path = os.path.join(Config.UPLOAD_FOLDER, photo_filename)
            
            with open(photo_path, 'wb') as f:
                f.write(photo_data)
            
            session_manager.delete_session(session_id)
            
            print(f"📸 Photo sent successfully for {first_name}")
            return jsonify({'success': True, 'message': details})
        else:
            return jsonify({'success': False, 'error': details})
            
    except Exception as e:
        app.logger.error(f"Photo sending error: {str(e)}")
        return jsonify({'success': False, 'error': 'Sending failed'})

@app.route('/retake_photo', methods=['POST'])
@rate_limit(max_requests=5, window_minutes=1)
def retake_photo():
    """Reset photo for retake"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'No session ID'})
    
    session_manager.reset_photo_for_retake(session_id)
    
    print(f"🔄 Photo retake for session {session_id}")
    return jsonify({'success': True})

@app.route('/admin')
def admin():
    """Admin dashboard"""
    total_count, verified_count, unverified_count = session_manager.get_session_stats()
    recent_sessions = session_manager.get_recent_sessions(10)
    
    sessions_html = ""
    for session_data in recent_sessions:
        sessions_html += f"<tr><td>{session_data[1]}</td><td>{session_data[2]}</td><td>{'✅' if session_data[3] else '⏳'}</td><td>{session_data[4]}</td><td>{session_data[5]}</td></tr>"
    
    # Rate limit info
    rate_limit_count = len(rate_limiter.requests)
    
    return f"""
    <html>
    <head><title>Selfie Booth Admin</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>📸 Selfie Booth Admin Dashboard</h1>
        <p><strong>Stats:</strong> {total_count} total, {verified_count} verified, {unverified_count} pending</p>
        <p><strong>Rate Limits:</strong> {rate_limit_count} IPs tracked - <a href="/selfie_booth/admin/reset_rate_limits" style="color: red;">Reset Rate Limits</a></p>
        
        <div style="margin: 20px 0;">
            <button onclick="resetSessions()" style="background: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">
                🔄 Reset All Sessions
            </button>
            <a href="/selfie_booth/admin/reset_rate_limits" style="background: #f39c12; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                ⚡ Reset Rate Limits
            </a>
        </div>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr><th>Name</th><th>Phone</th><th>Status</th><th>Code</th><th>Created</th></tr>
            {sessions_html}
        </table>
        
        <h3>Quick Links:</h3>
        <ul>
            <li><a href="/selfie_booth/">← Back to Kiosk</a></li>
            <li><a href="/selfie_booth/mobile">Mobile Registration Page</a></li>
            <li><a href="/selfie_booth/debug">Debug Sessions</a></li>
            <li><a href="/selfie_booth/reset">Quick Reset Everything</a></li>
        </ul>
        
        <script>
            async function resetSessions() {{
                if (confirm('Reset all sessions?')) {{
                    try {{
                        const response = await fetch('/selfie_booth/admin/reset_sessions', {{ method: 'POST' }});
                        const result = await response.json();
                        alert(result.success ? 'Sessions reset!' : 'Error: ' + result.error);
                        location.reload();
                    }} catch (error) {{
                        alert('Error resetting sessions');
                    }}
                }}
            }}
            setTimeout(() => location.reload(), 15000); // Auto-refresh every 15 seconds
        </script>
    </body>
    </html>
    """

@app.route('/debug')
def debug_sessions():
    """Debug sessions with tablet IDs and rate limit info"""
    recent_sessions = session_manager.get_recent_sessions(5)
    
    html = "<h2>Recent Sessions</h2>"
    html += "<table border='1'><tr><th>Name</th><th>Phone</th><th>Status</th><th>Code</th><th>Tablet ID</th><th>Location</th></tr>"
    
    for session_data in recent_sessions:
        # session_data[10] = tablet_id, session_data[11] = location
        tablet_id = session_data[10] if len(session_data) > 10 else 'None'
        location = session_data[11] if len(session_data) > 11 else 'None'
        
        html += f"<tr><td>{session_data[1]}</td><td>{session_data[2]}</td><td>{'✅' if session_data[3] else '⏳'}</td><td>{session_data[4]}</td><td>{tablet_id}</td><td>{location}</td></tr>"
    
    html += "</table>"
    
    # Rate limit debug info
    html += "<h2>Rate Limit Debug</h2>"
    html += f"<p><strong>Total IPs tracked:</strong> {len(rate_limiter.requests)}</p>"
    
    # Show current user's IP and request count
    client_ip = request.headers.get('X-Forwarded-For', 
                   request.headers.get('X-Real-IP', 
                   request.remote_addr))
    
    user_requests = len(rate_limiter.requests.get(client_ip, []))
    html += f"<p><strong>Your IP:</strong> {client_ip}</p>"
    html += f"<p><strong>Your recent requests:</strong> {user_requests}</p>"
    
    html += "<p><a href='/selfie_booth/admin/reset_rate_limits'>Reset Rate Limits</a> | <a href='/selfie_booth/admin'>Back to Admin</a></p>"
    
    return html

@app.route('/reset')
def quick_reset():
    """Quick reset for testing"""
    deleted_count = session_manager.reset_all_sessions()
    return f"<h1>Reset Complete!</h1><p>Deleted {deleted_count} sessions</p><p><a href='/selfie_booth/'>Back to Kiosk</a></p>"

@app.route('/admin/reset_sessions', methods=['POST'])
@rate_limit(max_requests=10, window_minutes=1)
def reset_sessions():
    """Reset all sessions"""
    try:
        deleted_count = session_manager.reset_all_sessions()
        return jsonify({'success': True, 'message': f'Reset {deleted_count} sessions'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/reset_rate_limits')
def reset_rate_limits():
    """Reset rate limits for testing"""
    global rate_limiter
    rate_limiter = WebRateLimiter()
    return "<h1>Rate Limits Reset!</h1><p>All rate limits have been cleared.</p><p><a href='/selfie_booth/admin'>Back to Admin</a></p>"

@app.route('/health')
def health():
    """Health check endpoint"""
    db_status = "connected" if session_manager.get_connection() else "disconnected"
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'config': {
            'messaging_service': Config.MESSAGING_SERVICE,
            'twilio_configured': bool(Config.TWILIO_ACCOUNT_SID)
        }
    })

@app.route('/1')
def booth_location_1():
    """Lobby tablet - short URL"""
    return redirect(url_for('mobile', tablet_id='TABLET1', location='lobby'))

@app.route('/2') 
def booth_location_2():
    """Entrance tablet - short URL"""
    return redirect(url_for('mobile', tablet_id='TABLET2', location='entrance'))

@app.route('/3')
def booth_location_3():
    """Event hall tablet - short URL"""
    return redirect(url_for('mobile', tablet_id='TABLET3', location='event_hall'))

@app.route('/4')
def booth_location_4():
    """Party room tablet - short URL"""
    return redirect(url_for('mobile', tablet_id='TABLET4', location='party_room'))
    
if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)