/**
 * API Functions for Selfie Booth
 * Handles all communication with the backend API
 */

class APIClient {
    constructor() {
        this.baseUrl = APP_CONFIG.API_BASE;
        this.defaultTimeout = APP_CONFIG.TIMEOUTS.API_REQUEST;
    }

    /**
     * Make a generic API request with error handling and timeouts
     */
    async request(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        
        const defaultOptions = {
            timeout: this.defaultTimeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        const requestOptions = { ...defaultOptions, ...options };
        
        // Handle timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), requestOptions.timeout);
        requestOptions.signal = controller.signal;

        try {
            if (APP_CONFIG.DEBUG) {
                console.log(`🔄 API Request: ${requestOptions.method || 'GET'} ${url}`, 
                           requestOptions.body ? JSON.parse(requestOptions.body) : 'No body');
            }

            const response = await fetch(url, requestOptions);
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (APP_CONFIG.DEBUG) {
                console.log(`✅ API Response: ${url}`, data);
            }

            return { success: true, data };

        } catch (error) {
            clearTimeout(timeoutId);
            
            let errorMessage = APP_CONFIG.MESSAGES.ERRORS.NETWORK;
            
            if (error.name === 'AbortError') {
                errorMessage = APP_CONFIG.MESSAGES.ERRORS.TIMEOUT;
            } else if (error.message) {
                errorMessage = error.message;
            }

            console.error(`❌ API Error: ${url}`, error);
            
            return { 
                success: false, 
                error: errorMessage,
                originalError: error 
            };
        }
    }

    /**
     * POST request helper
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * GET request helper
     */
    async get(endpoint) {
        return this.request(endpoint, {
            method: 'GET'
        });
    }

    /**
     * Upload file with FormData
     */
    async upload(endpoint, formData, timeout = 30000) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            timeout,
            headers: {} // Let browser set multipart headers
        });
    }

    // ============ User Registration & Verification ============

    /**
     * Register a new user session
     */
    async register(userData) {
        const { firstName, phone, email, consent, tabletId, location } = userData;
        
        return this.post('/register', {
            firstName: firstName?.trim(),
            phone: UTILS.cleanPhoneNumber(phone),
            email: email?.trim() || '',
            consent: !!consent,
            tablet_id: tabletId || TABLET_CONFIG.getTabletId(),
            location: location || TABLET_CONFIG.getLocation()
        });
    }

    /**
     * Verify user session with code
     */
    async verify(code) {
        return this.post('/verify', {
            code: code.toString().padStart(6, '0')
        });
    }

    // ============ Photo Management ============

    /**
     * Upload photo from camera
     */
    async uploadPhoto(photoBlob, sessionId) {
        const formData = new FormData();
        formData.append('photo', photoBlob, 'selfie.jpg');
        formData.append('session_id', sessionId || SESSION_CONFIG.getSessionId());
        
        return this.upload('/upload_photo', formData);
    }

    /**
     * Check if photo is ready for review
     */
    async checkPhoto(sessionId) {
        const id = sessionId || SESSION_CONFIG.getSessionId();
        return this.get(`/check_photo?session_id=${id}`);
    }

    /**
     * Keep photo and send to user
     */
    async keepPhoto(sessionId) {
        return this.post('/keep_photo', {
            session_id: sessionId || SESSION_CONFIG.getSessionId()
        });
    }

    /**
     * Request photo retake
     */
    async retakePhoto(sessionId) {
        return this.post('/retake_photo', {
            session_id: sessionId || SESSION_CONFIG.getSessionId()
        });
    }

    // ============ Session Management ============

    /**
     * Check current session state for kiosk display
     */
    async checkSessionState(tabletId) {
        const id = tabletId || TABLET_CONFIG.getTabletId();
        return this.get(`/session_check?tablet_id=${id}`);
    }

    // ============ Admin Functions ============

    /**
     * Get session statistics
     */
    async getSessionStats() {
        return this.get('/admin/stats');
    }

    /**
     * Get recent sessions
     */
    async getRecentSessions(limit = 10) {
        return this.get(`/admin/sessions?limit=${limit}`);
    }

    /**
     * Reset all sessions
     */
    async resetAllSessions() {
        return this.post('/admin/reset');
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.get('/health');
    }
}

// ============ Real-time Communication ============

class RealtimeClient {
    constructor() {
        this.eventSource = null;
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = APP_CONFIG.REALTIME.MAX_RETRIES;
        this.retryInterval = APP_CONFIG.REALTIME.RETRY_INTERVAL;
        this.listeners = new Map();
    }

    /**
     * Connect to server-sent events stream
     */
    connect(tabletId, onMessage, onError) {
        if (this.eventSource) {
            this.disconnect();
        }

        const url = `${APP_CONFIG.REALTIME.SSE_ENDPOINT}/${tabletId || TABLET_CONFIG.getTabletId()}`;
        
        try {
            this.eventSource = new EventSource(url);
            
            this.eventSource.onopen = () => {
                this.isConnected = true;
                this.retryCount = 0;
                console.log('🔗 Real-time connection established');
            };

            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (APP_CONFIG.DEBUG) {
                        console.log('📨 Real-time message:', data);
                    }
                    if (onMessage) onMessage(data);
                } catch (error) {
                    console.error('Error parsing real-time message:', error);
                }
            };

            this.eventSource.onerror = (error) => {
                this.isConnected = false;
                console.error('❌ Real-time connection error:', error);
                
                if (onError) onError(error);
                
                // Auto-retry with exponential backoff
                if (this.retryCount < this.maxRetries) {
                    this.retryCount++;
                    const delay = this.retryInterval * Math.pow(2, this.retryCount - 1);
                    console.log(`🔄 Retrying connection in ${delay}ms (attempt ${this.retryCount})`);
                    
                    setTimeout(() => {
                        this.connect(tabletId, onMessage, onError);
                    }, delay);
                } else {
                    console.error('❌ Max retries reached, falling back to polling');
                }
            };

        } catch (error) {
            console.error('Failed to create EventSource:', error);
            if (onError) onError(error);
        }
    }

    /**
     * Disconnect from real-time stream
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.isConnected = false;
            console.log('🔌 Real-time connection closed');
        }
    }

    /**
     * Send message to server (if using WebSocket in future)
     */
    send(message) {
        // For SSE, we don't send messages back
        // Could be implemented with WebSocket upgrade
        console.warn('Sending messages not supported with SSE');
    }
}

// ============ Polling Fallback ============

class PollingClient {
    constructor() {
        this.intervalId = null;
        this.isPolling = false;
        this.interval = APP_CONFIG.REALTIME.POLL_INTERVAL;
    }

    /**
     * Start polling for session state changes
     */
    startPolling(tabletId, onUpdate, onError) {
        if (this.isPolling) {
            this.stopPolling();
        }

        this.isPolling = true;
        let lastState = null;

        const poll = async () => {
            if (!this.isPolling) return;

            try {
                const response = await api.checkSessionState(tabletId);
                
                if (response.success) {
                    const currentState = response.data.session_state;
                    
                    // Only notify if state changed
                    if (lastState !== null && lastState !== currentState) {
                        if (onUpdate) {
                            onUpdate({
                                type: 'session_state_change',
                                old_state: lastState,
                                new_state: currentState,
                                data: response.data
                            });
                        }
                    }
                    
                    lastState = currentState;
                } else {
                    if (onError) onError(response.error);
                }
            } catch (error) {
                if (onError) onError(error);
            }
        };

        // Initial poll
        poll();
        
        // Set up interval
        this.intervalId = setInterval(poll, this.interval);
        
        console.log(`🔄 Started polling every ${this.interval}ms`);
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isPolling = false;
        console.log('⏹️ Stopped polling');
    }
}

// ============ Validation Functions ============

const ValidationAPI = {
    /**
     * Validate registration data
     */
    validateRegistration(data) {
        const errors = {};

        // First name validation
        if (!data.firstName || data.firstName.trim().length === 0) {
            errors.firstName = 'First name is required';
        } else if (data.firstName.trim().length > APP_CONFIG.VALIDATION.FIRST_NAME.MAX_LENGTH) {
            errors.firstName = `First name must be less than ${APP_CONFIG.VALIDATION.FIRST_NAME.MAX_LENGTH} characters`;
        } else if (!APP_CONFIG.VALIDATION.FIRST_NAME.PATTERN.test(data.firstName.trim())) {
            errors.firstName = 'First name contains invalid characters';
        }

        // Phone validation
        if (!data.phone || data.phone.trim().length === 0) {
            errors.phone = 'Phone number is required';
        } else if (!APP_CONFIG.VALIDATION.PHONE.PATTERN.test(data.phone)) {
            errors.phone = APP_CONFIG.MESSAGES.ERRORS.INVALID_PHONE;
        }

        // Email validation (optional)
        if (data.email && data.email.trim().length > 0) {
            if (!APP_CONFIG.VALIDATION.EMAIL.PATTERN.test(data.email)) {
                errors.email = APP_CONFIG.MESSAGES.ERRORS.INVALID_EMAIL;
            }
        }

        // Consent validation
        if (!data.consent) {
            errors.consent = APP_CONFIG.MESSAGES.ERRORS.CONSENT_REQUIRED;
        }

        return {
            isValid: Object.keys(errors).length === 0,
            errors
        };
    },

    /**
     * Validate verification code
     */
    validateVerificationCode(code) {
        if (!code || code.length !== APP_CONFIG.VALIDATION.VERIFICATION_CODE.LENGTH) {
            return {
                isValid: false,
                error: 'Code must be 6 digits'
            };
        }

        if (!APP_CONFIG.VALIDATION.VERIFICATION_CODE.PATTERN.test(code)) {
            return {
                isValid: false,
                error: 'Code must contain only numbers'
            };
        }

        return { isValid: true };
    }
};

// ============ Initialize and Export ============

// Create global instances
const api = new APIClient();
const realtime = new RealtimeClient();
const polling = new PollingClient();

// Export to global scope
window.api = api;
window.realtime = realtime;
window.polling = polling;
window.ValidationAPI = ValidationAPI;

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
    realtime.disconnect();
    polling.stopPolling();
});

if (APP_CONFIG.DEBUG) {
    console.log('🔧 API client initialized');
}