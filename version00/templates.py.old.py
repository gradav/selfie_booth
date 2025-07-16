#!/usr/bin/env python3
"""
Templates module for Selfie Booth application
Contains all HTML templates for the web interface
"""

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
        .subtitle {
            color: #666;
            font-size: 24px;
            margin-bottom: 40px;
        }
        .qr-section {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 60px;
            margin: 40px 0;
        }
        .qr-code {
            width: 250px;
            height: 250px;
            background: #f8f9fa;
            border: 3px solid #667eea;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: #667eea;
        }
        .instructions {
            max-width: 300px;
        }
        .step {
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 15px;
            border-left: 5px solid #667eea;
        }
        .step-number {
            background: #667eea;
            color: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-weight: bold;
        }
        .url-section {
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 15px;
        }
        .url {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-top: 10px;
        }
        .footer {
            margin-top: 30px;
            color: #888;
            font-size: 16px;
        }
        .trigger-btn {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
            margin: 10px;
        }
        .trigger-btn:hover {
            transform: translateY(-2px);
        }
        .debug-info {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            max-width: 300px;
        }
    </style>
</head>
<body>
    <div class="debug-info">
        Status: {{ debug_status }}<br>
        Last cleanup: {{ last_cleanup }}<br>
        Time: {{ current_time }}
    </div>
    
    <div class="kiosk-container">
        <h1>📸 Selfie Booth</h1>
        <div class="subtitle">Get your photo taken and sent to your phone!</div>
        
        <div class="qr-section">
            <div class="qr-code">
                <div>
                    <div>QR Code</div>
                    <div style="font-size: 14px; margin-top: 10px;">
                        Scan with your phone camera
                    </div>
                </div>
            </div>
            
            <div class="instructions">
                <div class="step">
                    <span class="step-number">1</span>
                    <strong>Scan QR Code</strong><br>
                    Use your phone camera to scan the QR code
                </div>
                <div class="step">
                    <span class="step-number">2</span>
                    <strong>Enter Your Info</strong><br>
                    Fill out the form on your phone
                </div>
                <div class="step">
                    <span class="step-number">3</span>
                    <strong>Enter Code</strong><br>
                    Type the code shown on this screen
                </div>
                <div class="step">
                    <span class="step-number">4</span>
                    <strong>Smile!</strong><br>
                    Look at the camera and smile for your photo
                </div>
            </div>
        </div>
        
        <div class="url-section">
            <div>Or visit directly:</div>
            <div class="url">{{ base_url }}/mobile</div>
        </div>
        
        <div class="footer">
            Photos will be sent to your phone via text message
            <div style="margin-top: 20px;">
                <button id="triggerPhoto" class="trigger-btn">📸 Trigger Photo (Manual)</button>
                <button id="resetSessions" class="trigger-btn" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">🔄 Reset Sessions</button>
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 3 seconds to check for new registrations
        setTimeout(() => {
            location.reload();
        }, 3000);

        // Manual photo trigger
        document.getElementById('triggerPhoto').addEventListener('click', async () => {
            try {
                const response = await fetch('/trigger_photo', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    if (result.redirect) {
                        window.location.href = result.redirect;
                    }
                } else {
                    alert('No verified user ready for photo. Please complete mobile registration first.');
                }
            } catch (error) {
                alert('Error triggering photo');
            }
        });

        // Reset sessions button
        document.getElementById('resetSessions').addEventListener('click', async () => {
            if (confirm('Are you sure you want to reset all sessions? This will clear all pending registrations.')) {
                try {
                    const response = await fetch('/admin/reset_sessions', { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('Sessions reset successfully!');
                        location.reload();
                    } else {
                        alert('Error resetting sessions: ' + result.error);
                    }
                } catch (error) {
                    alert('Error resetting sessions');
                }
            }
        });

        // Manual refresh button for debugging
        function manualRefresh() {
            console.log('Manual refresh triggered');
            location.reload();
        }
        
        // Add manual refresh button for debugging
        document.addEventListener('DOMContentLoaded', () => {
            const debugDiv = document.querySelector('.debug-info');
            if (debugDiv) {
                const refreshBtn = document.createElement('button');
                refreshBtn.textContent = '🔄 Refresh Now';
                refreshBtn.style.cssText = 'background: #667eea; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-top: 10px; display: block; width: 100%;';
                refreshBtn.onclick = manualRefresh;
                debugDiv.appendChild(refreshBtn);
            }
        });
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
    <title>Selfie Booth - Mobile</title>
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
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: bold;
        }
        input[type="text"], input[type="tel"], input[type="email"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="tel"]:focus, input[type="email"]:focus {
            border-color: #667eea;
            outline: none;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .checkbox-group input {
            margin-right: 10px;
        }
        .submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
        }
        .error {
            color: #e74c3c;
            margin-top: 10px;
            text-align: center;
        }
        .instruction {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📸 Selfie Booth</h1>
        <div class="instruction">
            <strong>Step 2:</strong> After submitting this form, look at the kiosk screen - your verification code will appear there.
        </div>
        <form id="userForm">
            <div class="form-group">
                <label for="firstName">First Name *</label>
                <input type="text" id="firstName" name="firstName" required>
            </div>
            <div class="form-group">
                <label for="phone">Phone Number *</label>
                <input type="tel" id="phone" name="phone" placeholder="(555) 123-4567" required>
            </div>
            <div class="form-group">
                <label for="email">Email Address (Optional)</label>
                <input type="email" id="email" name="email">
            </div>
            <div class="checkbox-group">
                <input type="checkbox" id="consent" name="consent" required>
                <label for="consent">I agree to receive text messages</label>
            </div>
            <button type="submit" class="submit-btn">Start Photo Session</button>
            <div id="error" class="error"></div>
        </form>
    </div>

    <script>
        document.getElementById('userForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    window.location.href = '/verify';
                } else {
                    document.getElementById('error').textContent = result.error;
                }
            } catch (error) {
                document.getElementById('error').textContent = 'Something went wrong. Please try again.';
            }
        });
    </script>
</body>
</html>
'''

KIOSK_VERIFICATION_PAGE = '''
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
        .back-link {
            position: absolute;
            top: 30px;
            left: 30px;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 16px;
        }
        .back-link:hover {
            background: rgba(255,255,255,0.3);
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
    <a href="/" class="back-link">← Back to Start</a>
    
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
                    window.location.href = '/';
                }, 2000);
            }
            timeLeft--;
        }, 1000);
        
        // Auto-refresh every 5 seconds to check verification status
        setTimeout(() => {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
'''

KIOSK_CAMERA_PAGE = '''
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
        .greeting h1 {
            color: #667eea;
            margin: 0;
            font-size: 48px;
        }
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
        #canvas {
            display: none;
        }
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
        .controls {
            margin-top: 30px;
        }
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
        .photo-btn:hover {
            transform: translateY(-3px);
        }
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
        .success {
            color: #27ae60;
        }
        .error {
            color: #e74c3c;
        }
        .photo-countdown {
            font-size: 32px;
            color: #667eea;
            margin-top: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="greeting">
        <h1>Hi {{ name }}, smile for the camera! 📸</h1>
    </div>
    
    <div class="camera-container">
        <video id="video" autoplay playsinline></video>
        <canvas id="canvas"></canvas>
        <img id="photoDisplay" alt="Your photo">
        <div id="countdown" class="countdown"></div>
        <div class="controls">
            <button id="photoBtn" class="photo-btn">Take Photo</button>
        </div>
        <div id="status" class="status"></div>
        <div id="photoCountdown" class="photo-countdown"></div>
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
                    video: { width: 1280, height: 720 } 
                });
                video.srcObject = stream;
            } catch (err) {
                document.getElementById('status').innerHTML = '<div class="error">Camera access denied. Please allow camera access and refresh.</div>';
            }
        }
        
        function startCountdown() {
            let count = 5;
            const countdownEl = document.getElementById('countdown');
            const photoBtn = document.getElementById('photoBtn');
            
            photoBtn.disabled = true;
            
            countdownInterval = setInterval(() => {
                countdownEl.textContent = count;
                
                if (count === 0) {
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
            const photoCountdownEl = document.getElementById('photoCountdown');
            
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
                statusEl.innerHTML = '<div class="success">📱 Sending your photo...</div>';
                
                try {
                    const response = await fetch('/upload_photo', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusEl.innerHTML = '<div class="success">📱 Photo captured! Check your mobile device to review and decide if you want to keep or retake it.</div>';
                        
                        // Start 10-second countdown before returning to kiosk
                        let photoCount = 10;
                        const photoCountdownInterval = setInterval(() => {
                            photoCountdownEl.textContent = `Returning to start in ${photoCount} seconds... (unless you choose to retake)`;
                            
                            if (photoCount === 0) {
                                clearInterval(photoCountdownInterval);
                                window.location.href = '/';
                            }
                            photoCount--;
                        }, 1000);
                        
                    } else {
                        statusEl.innerHTML = '<div class="error">Failed to send photo: ' + result.error + '</div>';
                        // Reset to camera view on error
                        video.style.display = 'block';
                        photoDisplay.style.display = 'none';
                        document.getElementById('photoBtn').disabled = false;
                    }
                } catch (error) {
                    statusEl.innerHTML = '<div class="error">Something went wrong. Please try again.</div>';
                    // Reset to camera view on error
                    video.style.display = 'block';
                    photoDisplay.style.display = 'none';
                    document.getElementById('photoBtn').disabled = false;
                }
            }, 'image/jpeg', 0.8);
        }
        
        document.getElementById('photoBtn').addEventListener('click', startCountdown);
        
        // Initialize camera when page loads
        initCamera();
        
        // Auto-start photo after 3 seconds
        setTimeout(() => {
            if (!document.getElementById('photoBtn').disabled) {
                startCountdown();
            }
        }, 3000);
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
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
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
        .btn:hover {
            transform: translateY(-2px);
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
        .countdown {
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
            margin: 15px 0;
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
            <button id="keepBtn" class="btn btn-keep">✅ Keep Photo</button>
            <button id="retakeBtn" class="btn btn-retake">🔄 Retake</button>
        </div>
        
        <div id="successMessage" class="success-msg" style="display: none;">
            <strong>Photo sent successfully!</strong><br>
            Check your messages for your selfie.
        </div>
        
        <div id="retakeCountdown" class="countdown" style="display: none;"></div>
    </div>

    <script>
        let sessionId = "{{ session_id }}";
        let photoCheckInterval;
        let countdownInterval;
        
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
                const response = await fetch(`/check_photo?session_id=${sessionId}`);
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
            try {
                const response = await fetch('/keep_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('buttonGroup').style.display = 'none';
                    document.getElementById('successMessage').style.display = 'block';
                    
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 5000);
                } else {
                    alert('Error sending photo: ' + result.error);
                }
            } catch (error) {
                alert('Error sending photo');
            }
        });
        
        // Retake photo button
        document.getElementById('retakeBtn').addEventListener('click', async () => {
            try {
                const response = await fetch('/retake_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('photoContainer').style.display = 'none';
                    document.getElementById('buttonGroup').style.display = 'none';
                    
                    const countdownEl = document.getElementById('retakeCountdown');
                    countdownEl.style.display = 'block';
                    
                    let count = 5;
                    countdownInterval = setInterval(() => {
                        countdownEl.textContent = `New photo session starting in ${count} seconds...`;
                        count--;
                        
                        if (count < 0) {
                            clearInterval(countdownInterval);
                            countdownEl.style.display = 'none';
                            document.getElementById('waitingStatus').style.display = 'block';
                            startPhotoCheck();
                        }
                    }, 1000);
                } else {
                    alert('Error starting retake: ' + result.error);
                }
            } catch (error) {
                alert('Error starting retake');
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
    <title>Enter Verification Code - Selfie Booth</title>
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
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        .instruction {
            background: #e8f4f8;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
            font-size: 16px;
            text-align: left;
        }
        .kiosk-icon {
            font-size: 48px;
            margin: 20px 0;
        }
        .code-input {
            font-size: 32px;
            text-align: center;
            padding: 20px;
            border: 3px solid #ddd;
            border-radius: 15px;
            width: 250px;
            margin: 30px 0;
            letter-spacing: 8px;
            font-weight: bold;
        }
        .code-input:focus {
            border-color: #667eea;
            outline: none;
        }
        .verify-btn {
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
            margin: 20px 0;
            transition: transform 0.2s;
        }
        .verify-btn:hover {
            transform: translateY(-2px);
        }
        .verify-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
        }
        .error {
            color: #e74c3c;
            margin-top: 15px;
            font-weight: bold;
        }
        .success {
            color: #27ae60;
            margin-top: 15px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Enter Verification Code</h1>
        
        <div class="kiosk-icon">🖥️</div>
        
        <div class="instruction">
            <strong>Look at the kiosk screen now</strong> - your 6-digit verification code should be displayed there. Enter it below.
        </div>
        
        <form id="verifyForm">
            <input type="text" 
                   id="codeInput" 
                   class="code-input" 
                   maxlength="6" 
                   placeholder="000000" 
                   required
                   autocomplete="off">
            <br>
            <button type="submit" class="verify-btn" id="verifyBtn">Verify Code</button>
            <div id="message"></div>
        </form>
    </div>

    <script>
        const codeInput = document.getElementById('codeInput');
        const verifyBtn = document.getElementById('verifyBtn');
        const form = document.getElementById('verifyForm');
        
        // Auto-focus on input
        codeInput.focus();
        
        // Format input as user types
        codeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\\D/g, '');
            
            // Auto-submit when 6 digits are entered
            if (e.target.value.length === 6) {
                form.dispatchEvent(new Event('submit'));
            }
        });
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const code = codeInput.value;
            
            if (code.length !== 6) {
                document.getElementById('message').innerHTML = '<div class="error">Please enter a 6-digit code</div>';
                return;
            }
            
            verifyBtn.disabled = true;
            verifyBtn.textContent = 'Verifying...';
            
            try {
                const response = await fetch('/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('message').innerHTML = '<div class="success">✅ Code verified! Redirecting to photo session...</div>';
                    setTimeout(() => {
                        if (result.redirect) {
                            window.location.href = result.redirect;
                        }
                    }, 1000);
                } else {
                    document.getElementById('message').innerHTML = '<div class="error">❌ ' + result.error + '</div>';
                    verifyBtn.disabled = false;
                    verifyBtn.textContent = 'Verify Code';
                    codeInput.focus();
                    codeInput.select();
                }
            } catch (error) {
                document.getElementById('message').innerHTML = '<div class="error">❌ Something went wrong. Please try again.</div>';
                verifyBtn.disabled = false;
                verifyBtn.textContent = 'Verify Code';
            }
        });
    </script>
</body>
</html>
'''