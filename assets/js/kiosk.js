/**
 * Kiosk Display Logic for Selfie Booth
 * Manages the main kiosk interface, QR codes, and screen transitions
 */

class KioskManager {
    constructor() {
        this.currentScreen = 'welcome';
        this.tabletId = TABLET_CONFIG.getTabletId();
        this.location = TABLET_CONFIG.getLocation();
        this.mobileUrl = TABLET_CONFIG.getMobileUrl();
        
        // Screen elements
        this.screens = {
            welcome: DOMUtils.getElementById('welcome-screen'),
            verification: DOMUtils.getElementById('verification-screen'),
            camera: DOMUtils.getElementById('camera-screen')
        };
        
        // UI elements
        this.elements = {
            tabletId: DOMUtils.getElementById('tablet-id'),
            location: DOMUtils.getElementById('location'),
            status: DOMUtils.getElementById('status'),
            mobileUrl: DOMUtils.getElementById('mobile-url'),
            qrCode: DOMUtils.getElementById('qrcode'),
            userGreeting: DOMUtils.getElementById('user-greeting'),
            verificationCode: DOMUtils.getElementById('verification-code'),
            countdown: DOMUtils.getElementById('countdown'),
            cameraGreeting: DOMUtils.getElementById('camera-greeting'),
            video: DOMUtils.getElementById('video'),
            canvas: DOMUtils.getElementById('canvas'),
            photoDisplay: DOMUtils.getElementById('photo-display'),
            cameraCountdown: DOMUtils.getElementById('camera-countdown'),
            photoBtn: DOMUtils.getElementById('photo-btn'),
            cameraStatus: DOMUtils.getElementById('camera-status')
        };
        
        // Camera properties
        this.videoStream = null;
        this.countdownInterval = null;
        this.uploadInProgress = false;
        this.currentSessionId = null;
        
        // Connection status UI
        this.statusUI = new ConnectionStatusUI('status');
        
        // Initialize
        this.init();
    }

    // ============ Initialization ============

    /**
     * Initialize kiosk display
     */
    async init() {
        console.log('🖥️ Initializing kiosk display');
        
        // Update tablet info
        this.updateTabletInfo();
        
        // Generate QR code
        this.generateQRCode();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Connect to real-time updates
        this.setupRealtimeConnection();
        
        // Show welcome screen initially
        this.showScreen('welcome');
        
        // Start monitoring session state
        this.startSessionMonitoring();
        
        console.log('✅ Kiosk display initialized');
    }

    /**
     * Update tablet information display
     */
    updateTabletInfo() {
        DOMUtils.setText(this.elements.tabletId, `Tablet: ${this.tabletId}`);
        DOMUtils.setText(this.elements.location, `Location: ${this.location}`);
        DOMUtils.setText(this.elements.mobileUrl, this.mobileUrl);
    }

    /**
     * Generate QR code for mobile URL
     */
    generateQRCode() {
        if (!this.elements.qrCode || !window.QRious) {
            console.error('❌ QR code generation failed: missing elements or library');
            return;
        }

        try {
            // Clear any existing QR code
            this.elements.qrCode.innerHTML = '';
            
            // Create new QR code
            const qr = new QRious({
                element: document.createElement('canvas'),
                value: this.mobileUrl,
                size: APP_CONFIG.UI.QR_CODE_SIZE,
                level: 'M',
                foreground: '#333',
                background: '#fff'
            });
            
            this.elements.qrCode.appendChild(qr.canvas);
            
            console.log('✅ QR code generated for:', this.mobileUrl);
        } catch (error) {
            console.error('❌ QR code generation error:', error);
            
            // Fallback: show text URL prominently
            DOMUtils.setHTML(this.elements.qrCode, 
                `<div style="padding: 20px; background: #f0f0f0; border-radius: 10px;">
                    <strong>QR Code Error</strong><br>
                    Visit: ${this.mobileUrl}
                </div>`
            );
        }
    }

    // ============ Screen Management ============

    /**
     * Show specific screen
     */
    showScreen(screenName, data = null) {
        if (this.currentScreen === screenName) return;

        console.log(`🖥️ Switching to screen: ${screenName}`);
        
        // Hide all screens
        Object.values(this.screens).forEach(screen => {
            if (screen) DOMUtils.removeClass(screen, 'active');
        });
        
        // Show target screen
        if (this.screens[screenName]) {
            DOMUtils.addClass(this.screens[screenName], 'active');
            this.currentScreen = screenName;
            
            // Handle screen-specific logic
            this.handleScreenShow(screenName, data);
        } else {
            console.error(`❌ Unknown screen: ${screenName}`);
        }
    }

    /**
     * Handle screen-specific initialization
     */
    handleScreenShow(screenName, data) {
        switch (screenName) {
            case 'welcome':
                this.handleWelcomeScreen();
                break;
                
            case 'verification':
                this.handleVerificationScreen(data);
                break;
                
            case 'camera':
                this.handleCameraScreen(data);
                break;
        }
    }

    /**
     * Handle welcome screen display
     */
    handleWelcomeScreen() {
        // Regenerate QR code in case URL changed
        this.generateQRCode();
        
        // Clear any existing camera streams
        this.stopCamera();
        
        // Reset countdown
        this.clearCountdown();
    }

    /**
     * Handle verification screen display
     */
    handleVerificationScreen(data) {
        if (!data) return;
        
        const { code, user_name, expires_at } = data;
        
        // Update display
        DOMUtils.setText(this.elements.userGreeting, `Hi ${user_name}!`);
        DOMUtils.setText(this.elements.verificationCode, code);
        
        // Start countdown timer
        this.startVerificationCountdown(expires_at);
        
        console.log(`🔢 Showing verification code: ${code} for ${user_name}`);
    }

    /**
     * Handle camera screen display
     */
    async handleCameraScreen(data) {
        if (!data) return;
        
        const { user_name, session_id } = data;
        this.currentSessionId = session_id;
        
        // Update greeting
        DOMUtils.setText(this.elements.cameraGreeting, `Hi ${user_name}, smile for the camera! 📸`);
        
        // Initialize camera
        await this.initCamera();
        
        // Auto-start countdown after 2 seconds
        setTimeout(() => {
            if (this.currentScreen === 'camera' && !this.uploadInProgress) {
                this.startPhotoCountdown();
            }
        }, 2000);
        
        console.log(`📸 Camera screen for: ${user_name} (${session_id})`);
    }

    // ============ Event Listeners ============

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Photo button click
        DOMUtils.addEventListener(this.elements.photoBtn, 'click', () => {
            this.startPhotoCountdown();
        });
        
        // Keyboard shortcuts for testing
        document.addEventListener('keydown', (e) => {
            if (APP_CONFIG.DEBUG) {
                switch (e.key) {
                    case '1':
                        this.showScreen('welcome');
                        break;
                    case '2':
                        this.showScreen('verification', {
                            code: '123456',
                            user_name: 'Test User',
                            expires_at: new Date(Date.now() + 120000).toISOString()
                        });
                        break;
                    case '3':
                        this.showScreen('camera', {
                            user_name: 'Test User',
                            session_id: 'test-session'
                        });
                        break;
                    case 'Escape':
                        this.showScreen('welcome');
                        break;
                }
            }
        });
    }

    // ============ Real-time Connection ============

    /**
     * Set up real-time connection for updates
     */
    setupRealtimeConnection() {
        // Connection status updates
        realtimeManager.on('connected', (data) => {
            console.log('🔗 Real-time connected:', data.type);
            this.statusUI.updateStatus('connected', this.getSessionStateFromScreen());
        });

        realtimeManager.on('disconnected', () => {
            console.log('🔌 Real-time disconnected');
            this.statusUI.updateStatus('disconnected');
        });

        realtimeManager.on('error', (data) => {
            console.error('❌ Real-time error:', data.error);
            this.statusUI.updateStatus('error');
        });

        // Session state changes
        realtimeManager.on('session_state_change', (data) => {
            this.handleSessionStateChange(data);
        });

        // Specific state events
        realtimeManager.on('show_verification', (data) => {
            this.showScreen('verification', data);
        });

        realtimeManager.on('photo_session_start', (data) => {
            this.showScreen('camera', data);
        });

        realtimeManager.on('session_reset', () => {
            this.showScreen('welcome');
        });

        // Connect
        realtimeManager.connect(this.tabletId);
    }

    /**
     * Handle session state changes from real-time updates
     */
    handleSessionStateChange(data) {
        const { new_state, session_data } = data;
        
        console.log(`🔄 Session state change: ${data.old_state} → ${new_state}`);
        
        // Update status UI
        this.statusUI.updateStatus('connected', new_state);
        
        // Handle state-specific logic
        switch (new_state) {
            case 'default':
                this.showScreen('welcome');
                break;
                
            case 'verification':
                if (session_data && session_data.verification_code) {
                    this.showScreen('verification', {
                        code: session_data.verification_code,
                        user_name: session_data.user_name,
                        expires_at: session_data.expires_at
                    });
                }
                break;
                
            case 'camera':
                if (session_data && session_data.session_id) {
                    this.showScreen('camera', {
                        user_name: session_data.user_name,
                        session_id: session_data.session_id
                    });
                }
                break;
        }
    }

    // ============ Session Monitoring ============

    /**
     * Start monitoring session state
     */
    startSessionMonitoring() {
        // Initial state check
        this.checkSessionState();
        
        // Set up periodic checking as backup
        setInterval(() => {
            if (!realtimeManager.isConnected) {
                this.checkSessionState();
            }
        }, APP_CONFIG.UI.REFRESH_INTERVAL);
    }

    /**
     * Check current session state
     */
    async checkSessionState() {
        try {
            const response = await api.checkSessionState(this.tabletId);
            
            if (response.success) {
                const state = response.data.session_state;
                
                // Only update if we're not getting real-time updates
                if (!realtimeManager.isConnected) {
                    this.handleSessionStateChange({
                        old_state: this.getSessionStateFromScreen(),
                        new_state: state,
                        session_data: response.data
                    });
                }
            }
        } catch (error) {
            console.error('❌ Session state check failed:', error);
        }
    }

    /**
     * Get session state from current screen
     */
    getSessionStateFromScreen() {
        switch (this.currentScreen) {
            case 'verification': return 'verification';
            case 'camera': return 'camera';
            default: return 'default';
        }
    }

    // ============ Countdown Timers ============

    /**
     * Start verification code countdown
     */
    startVerificationCountdown(expiresAt) {
        this.clearCountdown();
        
        const expirationTime = new Date(expiresAt).getTime();
        
        const updateCountdown = () => {
            const now = new Date().getTime();
            const timeLeft = Math.max(0, expirationTime - now);
            
            if (timeLeft > 0) {
                const minutes = Math.floor(timeLeft / 60000);
                const seconds = Math.floor((timeLeft % 60000) / 1000);
                
                DOMUtils.setText(this.elements.countdown, 
                    `Expires in ${minutes}:${seconds.toString().padStart(2, '0')}`);
            } else {
                DOMUtils.setText(this.elements.countdown, 'Code expired');
                DOMUtils.addClass(this.elements.countdown, 'expired');
                
                // Auto-return to welcome screen
                setTimeout(() => {
                    this.showScreen('welcome');
                }, 2000);
                
                this.clearCountdown();
            }
        };
        
        // Update immediately and then every second
        updateCountdown();
        this.countdownInterval = setInterval(updateCountdown, 1000);
    }

    /**
     * Start photo countdown
     */
    startPhotoCountdown() {
        if (this.uploadInProgress) return;
        
        let count = 5;
        DOMUtils.setEnabled(this.elements.photoBtn, false);
        
        const countdown = () => {
            if (count > 0) {
                DOMUtils.setText(this.elements.cameraCountdown, count);
                count--;
                setTimeout(countdown, 1000);
            } else {
                DOMUtils.setText(this.elements.cameraCountdown, 'Say Cheese! 📸');
                setTimeout(() => {
                    this.takePhoto();
                }, 500);
            }
        };
        
        countdown();
    }

    /**
     * Clear countdown timer
     */
    clearCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
        
        if (this.elements.countdown) {
            DOMUtils.removeClass(this.elements.countdown, 'expired');
        }
    }

    // ============ Camera Functions ============

    /**
     * Initialize camera
     */
    async initCamera() {
        try {
            const result = await CameraUtils.getUserMedia();
            
            if (result.success) {
                this.videoStream = result.stream;
                this.elements.video.srcObject = this.videoStream;
                
                // Enable photo button once video is ready
                this.elements.video.addEventListener('loadedmetadata', () => {
                    DOMUtils.setEnabled(this.elements.photoBtn, true);
                    console.log('📹 Camera initialized successfully');
                });
                
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('❌ Camera initialization failed:', error);
            DOMUtils.setText(this.elements.cameraStatus, 
                `<div class="error">${error.message || 'Camera access required'}</div>`);
        }
    }

    /**
     * Take photo
     */
    async takePhoto() {
        if (this.uploadInProgress || !this.videoStream) return;
        
        console.log('📸 Taking photo...');
        this.uploadInProgress = true;
        
        try {
            // Show video and hide photo initially
            DOMUtils.show(this.elements.video);
            DOMUtils.hide(this.elements.photoDisplay);
            
            // Capture photo
            const photoBlob = await CameraUtils.capturePhoto(
                this.elements.video, 
                this.elements.canvas
            );
            
            // Show captured photo
            const photoUrl = URL.createObjectURL(photoBlob);
            this.elements.photoDisplay.src = photoUrl;
            DOMUtils.hide(this.elements.video);
            DOMUtils.show(this.elements.photoDisplay);
            
            // Update status
            DOMUtils.setText(this.elements.cameraCountdown, '');
            DOMUtils.setText(this.elements.cameraStatus, 
                '<div class="success">📱 Processing your photo...</div>');
            
            // Upload photo
            const uploadResponse = await api.uploadPhoto(photoBlob, this.currentSessionId);
            
            if (uploadResponse.success) {
                DOMUtils.setText(this.elements.cameraStatus, 
                    '<div class="success">📱 Photo captured! Check your phone to review and send.</div>');
                
                console.log('✅ Photo uploaded successfully');
                
                // Return to welcome screen after delay
                setTimeout(() => {
                    this.showScreen('welcome');
                }, 8000);
                
            } else {
                throw new Error(uploadResponse.error || 'Upload failed');
            }
            
        } catch (error) {
            console.error('❌ Photo capture failed:', error);
            DOMUtils.setText(this.elements.cameraStatus, 
                `<div class="error">Failed to capture photo: ${error.message}</div>`);
            
            // Reset camera
            this.resetCamera();
        } finally {
            this.uploadInProgress = false;
        }
    }

    /**
     * Reset camera state
     */
    resetCamera() {
        DOMUtils.show(this.elements.video);
        DOMUtils.hide(this.elements.photoDisplay);
        DOMUtils.setEnabled(this.elements.photoBtn, true);
        DOMUtils.setText(this.elements.cameraCountdown, '');
    }

    /**
     * Stop camera stream
     */
    stopCamera() {
        if (this.videoStream) {
            CameraUtils.stopStream(this.videoStream);
            this.videoStream = null;
        }
    }

    // ============ Utility Methods ============

    /**
     * Force refresh of kiosk display
     */
    refresh() {
        console.log('🔄 Refreshing kiosk display');
        
        // Regenerate QR code
        this.generateQRCode();
        
        // Check session state
        this.checkSessionState();
        
        // Reconnect real-time if needed
        if (!realtimeManager.isConnected) {
            realtimeManager.reconnect();
        }
    }

    /**
     * Get current kiosk status
     */
    getStatus() {
        return {
            currentScreen: this.currentScreen,
            tabletId: this.tabletId,
            location: this.location,
            mobileUrl: this.mobileUrl,
            hasCamera: !!this.videoStream,
            uploadInProgress: this.uploadInProgress,
            currentSessionId: this.currentSessionId,
            realtime: realtimeManager.getStatus()
        };
    }
}

// ============ Initialize on Page Load ============

let kioskManager;

document.addEventListener('DOMContentLoaded', () => {
    kioskManager = new KioskManager();
    
    // Export to global scope for debugging
    window.kioskManager = kioskManager;
    
    if (APP_CONFIG.DEBUG) {
        console.log('🔧 Kiosk manager available globally as kioskManager');
        
        // Add debug commands
        window.kioskDebug = {
            showWelcome: () => kioskManager.showScreen('welcome'),
            showVerification: () => kioskManager.showScreen('verification', {
                code: '123456',
                user_name: 'Debug User',
                expires_at: new Date(Date.now() + 120000).toISOString()
            }),
            showCamera: () => kioskManager.showScreen('camera', {
                user_name: 'Debug User',
                session_id: 'debug-session'
            }),
            refresh: () => kioskManager.refresh(),
            status: () => kioskManager.getStatus()
        };
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && kioskManager) {
        // Page became visible, refresh kiosk
        setTimeout(() => {
            kioskManager.refresh();
        }, 1000);
    }
});