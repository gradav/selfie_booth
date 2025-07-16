#!/usr/bin/env python3
"""
Templates module for Selfie Booth application
Contains all HTML templates with optimizations for web hosting and tablet use
"""

# Optimized Kiosk Page with Client-Side QR Generation
KIOSK_PAGE_OPTIMIZED = '''
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
                const response = await fetch('session_check?tablet_id={{ tablet_id }}');
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

# Optimized Mobile Page
MOBILE_PAGE_OPTIMIZED = '''
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
                const response = await fetch('register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    submitBtn.textContent = 'Success! Redirecting...';
                    window.location.href = 'verify';
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

# Optimized Verify Page
VERIFY_PAGE_OPTIMIZED = '''
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
        let verificationInProgress = false;
        
        // Auto-focus on input
        codeInput.focus();
        
        // Format input as numbers only
        codeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
        
        document.getElementById('verifyForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            console.log('🔐 Verification form submitted at:', new Date().toISOString());
            
            if (verificationInProgress) {
                console.log('🛑 Verification already in progress, skipping duplicate request');
                return;
            }
            
            const code = codeInput.value;
            
            if (code.length !== 6) {
                messageDiv.innerHTML = '<div class="error">Please enter a 6-digit code</div>';
                return;
            }
            
            verificationInProgress = true;
            verifyBtn.disabled = true;
            verifyBtn.textContent = 'Verifying...';
            messageDiv.innerHTML = '';
            
            try {
                console.log('📤 Sending verification request at:', new Date().toISOString());
                const response = await fetch('verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                
                console.log('📬 Verification response received at:', new Date().toISOString(), 'Status:', response.status);
                const result = await response.json();
                console.log('📋 Verification result:', result);
                
                if (result.success) {
                    messageDiv.innerHTML = '<div class="success">✅ Verified! Redirecting...</div>';
                    setTimeout(() => {
                        window.location.href = result.redirect || 'photo_session';
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
            } finally {
                verificationInProgress = false;
            }
        });
    </script>
</body>
</html>
'''

# Verification Display Page (for Kiosk)
VERIFICATION_DISPLAY_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code - Selfie Booth</title>
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
        .verification-container {
            background: white;
            padding: 80px;
            border-radius: 30px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
            max-width: 800px;
            width: 90%;
        }
        h1 {
            color: #333;
            font-size: 42px;
            margin-bottom: 20px;
        }
        .user-greeting {
            color: #667eea;
            font-size: 28px;
            margin-bottom: 40px;
        }
        .code-display {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px;
            border-radius: 25px;
            margin: 40px 0;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        .code {
            font-size: 96px;
            font-weight: bold;
            letter-spacing: 20px;
            margin: 20px 0;
        }
        .code-label {
            font-size: 24px;
            margin-bottom: 10px;
            opacity: 0.9;
        }
        .instructions {
            font-size: 24px;
            color: #555;
            margin-top: 40px;
            line-height: 1.6;
        }
        .highlight {
            background: #fff3cd;
            padding: 4px 8px;
            border-radius: 5px;
            color: #856404;
        }
        .expires-in {
            font-size: 18px;
            color: #e74c3c;
            margin-top: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="verification-container">
        <h1>📱 Verification Required</h1>
        <div class="user-greeting">Hi {{ name }}!</div>
        
        <div class="code-display">
            <div class="code-label">Enter this code on your phone:</div>
            <div class="code">{{ code }}</div>
            <div class="expires-in" id="countdown">Expires in 2:00</div>
        </div>
        
        <div class="instructions">
            <p>📱 Go to your phone and enter the <span class="highlight">6-digit code</span> shown above</p>
            <p>⏰ This code will expire in 2 minutes</p>
        </div>
    </div>

    <script>
        // Countdown timer
        let timeLeft = 120; // 2 minutes in seconds
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownEl.textContent = `Expires in ${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                countdownEl.textContent = 'Code expired';
                countdownEl.style.color = '#e74c3c';
                // Auto-refresh to go back to start
                setTimeout(() => {
                    window.location.href = './';
                }, 2000);
            }
            timeLeft--;
        }, 1000);
        
        // Smart refresh - check session state instead of full reload
        setTimeout(() => {
            fetch('session_check?tablet_id={{ tablet_id }}')
                .then(r => r.json())
                .then(data => {
                    if (data.session_state !== 'verification') {
                        location.reload();
                    } else {
                        location.reload(); // Still in verification, refresh to check timeout
                    }
                })
                .catch(() => location.reload());
        }, 5000);
    </script>
</body>
</html>
'''

# Optimized Photo Session Page
PHOTO_SESSION_PAGE_OPTIMIZED = '''
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
                const response = await fetch(`check_photo?session_id=${sessionId}`);
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
                        window.location.href = 'mobile';
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

# Optimized Camera Page
CAMERA_PAGE_OPTIMIZED = '''
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
        let uploadInProgress = false;
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
            console.log('🚀 takePhoto() called at:', new Date().toISOString());
            
            if (uploadInProgress) {
                console.log('🛑 Upload already in progress, skipping duplicate request');
                return;
            }
            
            uploadInProgress = true;
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
                
                console.log('📤 About to send upload request at:', new Date().toISOString());
                try {
                    const response = await fetch('/selfie_booth/upload_photo', {
                        method: 'POST',
                        body: formData
                    });
                    
                    console.log('📬 Upload response received at:', new Date().toISOString(), 'Status:', response.status);
                    const result = await response.json();
                    console.log('📋 Upload result:', result);
                    
                    if (result.success) {
                        statusEl.innerHTML = '<div class="success">📱 Photo captured! Check your phone to review and send.</div>';
                        
                        // Return to kiosk after 8 seconds
                        setTimeout(() => {
                            window.location.href = './';
                        }, 8000);
                        
                    } else {
                        statusEl.innerHTML = '<div class="error">Failed to capture photo: ' + result.error + '</div>';
                        resetCamera();
                    }
                } catch (error) {
                    statusEl.innerHTML = '<div class="error">Network error. Please try again.</div>';
                    resetCamera();
                } finally {
                    uploadInProgress = false;
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

# Legacy templates for backwards compatibility
KIOSK_PAGE = KIOSK_PAGE_OPTIMIZED
MOBILE_PAGE = MOBILE_PAGE_OPTIMIZED
KIOSK_VERIFICATION_PAGE = VERIFICATION_DISPLAY_PAGE
KIOSK_CAMERA_PAGE = CAMERA_PAGE_OPTIMIZED
PHOTO_SESSION_PAGE = PHOTO_SESSION_PAGE_OPTIMIZED
VERIFY_PAGE = VERIFY_PAGE_OPTIMIZED