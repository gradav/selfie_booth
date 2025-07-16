/**
 * Selfie Booth Configuration
 * Central configuration for API endpoints, settings, and constants
 */

// Determine if we're in a development environment
const isDevelopment = window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1' ||
                     window.location.hostname.includes('dev');

// Base configuration
const APP_CONFIG = {
    // API Configuration
    API_BASE: '/api',
    
    // Endpoints
    ENDPOINTS: {
        REGISTER: '/api/register',
        VERIFY: '/api/verify',
        UPLOAD_PHOTO: '/api/upload_photo',
        CHECK_PHOTO: '/api/check_photo',
        KEEP_PHOTO: '/api/keep_photo',
        RETAKE_PHOTO: '/api/retake_photo',
        SESSION_CHECK: '/api/session_check',
        ADMIN_STATS: '/api/admin/stats',
        ADMIN_SESSIONS: '/api/admin/sessions',
        ADMIN_RESET: '/api/admin/reset',
        HEALTH: '/api/health'
    },
    
    // Real-time Configuration
    REALTIME: {
        // Use Server-Sent Events for real-time updates
        SSE_ENDPOINT: '/api/stream',
        // Polling fallback interval (milliseconds)
        POLL_INTERVAL: 3000,
        // Connection retry settings
        RETRY_INTERVAL: 5000,
        MAX_RETRIES: 10
    },
    
    // Timing Configuration
    TIMEOUTS: {
        REGISTRATION: 30000,    // 30 seconds
        VERIFICATION: 120000,   // 2 minutes
        PHOTO_SESSION: 180000,  // 3 minutes
        PHOTO_CHECK: 2000,      // 2 seconds
        API_REQUEST: 10000      // 10 seconds
    },
    
    // UI Configuration
    UI: {
        REFRESH_INTERVAL: 3000,
        PHOTO_CHECK_INTERVAL: 2000,
        QR_CODE_SIZE: 200,
        ANIMATION_DURATION: 300
    },
    
    // Photo Configuration
    PHOTO: {
        MAX_SIZE: 16 * 1024 * 1024, // 16MB
        QUALITY: 0.8,
        FORMAT: 'image/jpeg',
        CAMERA_CONSTRAINTS: {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            }
        }
    },
    
    // Validation Rules
    VALIDATION: {
        FIRST_NAME: {
            MIN_LENGTH: 1,
            MAX_LENGTH: 50,
            PATTERN: /^[a-zA-Z\s\-'\.]+$/
        },
        PHONE: {
            PATTERN: /^[\+]?[1]?[\s\-\.]?\(?[0-9]{3}\)?[\s\-\.]?[0-9]{3}[\s\-\.]?[0-9]{4}$/
        },
        EMAIL: {
            PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        },
        VERIFICATION_CODE: {
            LENGTH: 6,
            PATTERN: /^[0-9]{6}$/
        }
    },
    
    // Error Messages
    MESSAGES: {
        ERRORS: {
            NETWORK: 'Network error. Please check your connection and try again.',
            TIMEOUT: 'Request timed out. Please try again.',
            INVALID_PHONE: 'Please enter a valid phone number (e.g., 555-123-4567)',
            INVALID_EMAIL: 'Please enter a valid email address',
            INVALID_NAME: 'Please enter a valid first name',
            INVALID_CODE: 'Please enter a valid 6-digit code',
            CONSENT_REQUIRED: 'You must agree to receive your photo via text',
            SESSION_EXPIRED: 'Your session has expired. Please start over.',
            CAMERA_ACCESS: 'Camera access required. Please allow camera access and refresh.',
            PHOTO_UPLOAD_FAILED: 'Failed to upload photo. Please try again.',
            VERIFICATION_FAILED: 'Invalid verification code. Please try again.',
            REGISTRATION_FAILED: 'Registration failed. Please try again.'
        },
        SUCCESS: {
            REGISTRATION: 'Registration successful! Look at the kiosk for your verification code.',
            VERIFICATION: 'Verification successful! Your photo session is starting.',
            PHOTO_SENT: 'Photo sent successfully! Check your messages.',
            RETAKE_STARTED: 'Starting retake. Look at the kiosk screen.'
        },
        INFO: {
            LOADING: 'Loading...',
            PROCESSING: 'Processing...',
            WAITING_PHOTO: 'Waiting for photo to be taken...',
            UPLOADING: 'Uploading photo...',
            SENDING: 'Sending photo...'
        }
    },
    
    // Development/Debug Configuration
    DEBUG: isDevelopment,
    
    // Feature Flags
    FEATURES: {
        ENABLE_QR_CODE: true,
        ENABLE_REALTIME: true,
        ENABLE_PHOTO_RETAKE: true,
        ENABLE_EMAIL_OPTION: true,
        ENABLE_ADMIN_PANEL: true
    }
};

// Environment-specific overrides
if (isDevelopment) {
    APP_CONFIG.DEBUG = true;
    APP_CONFIG.UI.REFRESH_INTERVAL = 1000; // Faster refresh in dev
    console.log('🔧 Development mode enabled');
}

// Tablet ID Management
const TABLET_CONFIG = {
    // Get tablet ID from URL params, session storage, or generate new one
    getTabletId() {
        const urlParams = new URLSearchParams(window.location.search);
        let tabletId = urlParams.get('tablet_id') || 
                      sessionStorage.getItem('tablet_id') ||
                      this.generateTabletId();
        
        sessionStorage.setItem('tablet_id', tabletId);
        return tabletId;
    },
    
    // Generate a unique tablet ID
    generateTabletId() {
        return 'tablet_' + Math.random().toString(36).substr(2, 9);
    },
    
    // Get location from URL params or session storage
    getLocation() {
        const urlParams = new URLSearchParams(window.location.search);
        let location = urlParams.get('location') || 
                      sessionStorage.getItem('location') ||
                      'default';
        
        sessionStorage.setItem('location', location);
        return location;
    },
    
    // Short URL mapping for different tablet configurations
    TABLET_MAPPING: {
        'TABLET1': { location: 'lobby', shortCode: '1' },
        'TABLET2': { location: 'entrance', shortCode: '2' },
        'TABLET3': { location: 'event_hall', shortCode: '3' },
        'TABLET4': { location: 'party_room', shortCode: '4' }
    },
    
    // Generate mobile URL for current tablet
    getMobileUrl() {
        const baseUrl = window.location.origin;
        const tabletId = this.getTabletId();
        const location = this.getLocation();
        
        // Check if this is a known tablet configuration
        const mapping = Object.entries(this.TABLET_MAPPING)
            .find(([id, config]) => id === tabletId);
        
        if (mapping) {
            return `${baseUrl}/${mapping[1].shortCode}`;
        }
        
        // Default URL with parameters
        return `${baseUrl}/mobile.html?tablet_id=${tabletId}&location=${location}`;
    }
};

// Session Management
const SESSION_CONFIG = {
    // Session storage keys
    KEYS: {
        SESSION_ID: 'selfie_session_id',
        TABLET_ID: 'tablet_id',
        LOCATION: 'location',
        USER_DATA: 'user_data',
        PHOTO_DATA: 'photo_data'
    },
    
    // Get session ID
    getSessionId() {
        return sessionStorage.getItem(this.KEYS.SESSION_ID);
    },
    
    // Set session ID
    setSessionId(sessionId) {
        sessionStorage.setItem(this.KEYS.SESSION_ID, sessionId);
    },
    
    // Clear session data
    clearSession() {
        Object.values(this.KEYS).forEach(key => {
            sessionStorage.removeItem(key);
        });
    },
    
    // Store user data
    setUserData(userData) {
        sessionStorage.setItem(this.KEYS.USER_DATA, JSON.stringify(userData));
    },
    
    // Get user data
    getUserData() {
        const data = sessionStorage.getItem(this.KEYS.USER_DATA);
        return data ? JSON.parse(data) : null;
    }
};

// Utility functions
const UTILS = {
    // Format phone number for display
    formatPhoneNumber(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
        }
        if (cleaned.length === 11 && cleaned[0] === '1') {
            return `+1 (${cleaned.slice(1,4)}) ${cleaned.slice(4,7)}-${cleaned.slice(7)}`;
        }
        return phone;
    },
    
    // Clean phone number for API
    cleanPhoneNumber(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            return `1${cleaned}`;
        }
        return cleaned;
    },
    
    // Format timestamp for display
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    },
    
    // Generate verification code
    generateVerificationCode() {
        return Math.floor(100000 + Math.random() * 900000).toString();
    },
    
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
};

// Export configuration objects to global scope
window.APP_CONFIG = APP_CONFIG;
window.TABLET_CONFIG = TABLET_CONFIG;
window.SESSION_CONFIG = SESSION_CONFIG;
window.UTILS = UTILS;

// Debug logging
if (APP_CONFIG.DEBUG) {
    console.log('📋 Configuration loaded:', {
        tabletId: TABLET_CONFIG.getTabletId(),
        location: TABLET_CONFIG.getLocation(),
        mobileUrl: TABLET_CONFIG.getMobileUrl(),
        sessionId: SESSION_CONFIG.getSessionId()
    });
}