/**
 * Photo Session Logic for Selfie Booth
 * Handles photo waiting, review, and sending process
 */

class PhotoSessionManager {
    constructor() {
        this.sessionId = SESSION_CONFIG.getSessionId();
        this.currentState = 'waiting'; // waiting, review, sending, success, error
        this.photoCheckInterval = null;
        this.isProcessing = false;
        
        // Screen sections
        this.sections = {
            waiting: DOMUtils.getElementById('waiting-section'),
            review: DOMUtils.getElementById('review-section'),
            success: DOMUtils.getElementById('success-section'),
            error: DOMUtils.getElementById('error-section')
        };
        
        // UI elements
        this.elements = {
            photoImage: DOMUtils.getElementById('photo-image'),
            keepBtn: DOMUtils.getElementById('keep-btn'),
            retakeBtn: DOMUtils.getElementById('retake-btn'),
            newSessionBtn: DOMUtils.getElementById('new-session-btn'),
            retryBtn: DOMUtils.getElementById('retry-btn'),
            restartBtn: DOMUtils.getElementById('restart-btn'),
            errorText: DOMUtils.getElementById('error-text'),
            loadingText: DOMUtils.getElementById('loading-text')
        };
        
        // Initialize
        this.init();
    }

    // ============ Initialization ============

    /**
     * Initialize photo session
     */
    init() {
        console.log('📸 Initializing photo session');
        
        // Check session validity
        if (!this.sessionId) {
            this.redirectToRegistration('No active session found');
            return;
        }
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start in waiting state
        this.setState('waiting');
        
        // Start checking for photo
        this.startPhotoChecking();
        
        console.log('✅ Photo session initialized');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Keep photo button
        if (this.elements.keepBtn) {
            this.elements.keepBtn.addEventListener('click', () => {
                this.handleKeepPhoto();
            });
        }
        
        // Retake photo button
        if (this.elements.retakeBtn) {
            this.elements.retakeBtn.addEventListener('click', () => {
                this.handleRetakePhoto();
            });
        }
        
        // New session button
        if (this.elements.newSessionBtn) {
            this.elements.newSessionBtn.addEventListener('click', () => {
                this.handleNewSession();
            });
        }
        
        // Retry button
        if (this.elements.retryBtn) {
            this.elements.retryBtn.addEventListener('click', () => {
                this.handleRetry();
            });
        }
        
        // Restart button
        if (this.elements.restartBtn) {
            this.elements.restartBtn.addEventListener('click', () => {
                this.handleRestart();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.currentState === 'review' && !this.isProcessing) {
                switch (e.key) {
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        this.handleKeepPhoto();
                        break;
                    case 'Escape':
                    case 'r':
                        e.preventDefault();
                        this.handleRetakePhoto();
                        break;
                }
            }
        });
    }

    // ============ State Management ============

    /**
     * Set current state and update UI
     */
    setState(newState, data = null) {
        if (this.currentState === newState) return;
        
        console.log(`📸 State change: ${this.currentState} → ${newState}`);
        
        // Hide all sections
        Object.values(this.sections).forEach(section => {
            if (section) DOMUtils.removeClass(section, 'active');
        });
        
        // Show target section
        if (this.sections[newState]) {
            DOMUtils.addClass(this.sections[newState], 'active');
        }
        
        this.currentState = newState;
        
        // Handle state-specific logic
        this.handleStateChange(newState, data);
    }

    /**
     * Handle state-specific logic
     */
    handleStateChange(state, data) {
        switch (state) {
            case 'waiting':
                this.handleWaitingState();
                break;
                
            case 'review':
                this.handleReviewState(data);
                break;
                
            case 'success':
                this.handleSuccessState(data);
                break;
                
            case 'error':
                this.handleErrorState(data);
                break;
        }
    }

    /**
     * Handle waiting state
     */
    handleWaitingState() {
        // Start photo checking if not already running
        if (!this.photoCheckInterval) {
            this.startPhotoChecking();
        }
    }

    /**
     * Handle review state
     */
    handleReviewState(data) {
        if (!data || !data.photoData) {
            this.setState('error', { message: 'No photo data received' });
            return;
        }
        
        // Stop photo checking
        this.stopPhotoChecking();
        
        // Display photo
        this.displayPhoto(data.photoData);
        
        // Enable action buttons
        DOMUtils.setEnabled(this.elements.keepBtn, true);
        DOMUtils.setEnabled(this.elements.retakeBtn, true);
        
        console.log('📸 Photo ready for review');
    }

    /**
     * Handle success state
     */
    handleSuccessState(data) {
        // Stop any ongoing processes
        this.stopPhotoChecking();
        this.isProcessing = false;
        
        // Auto-redirect to new session after delay
        setTimeout(() => {
            this.handleNewSession();
        }, 5000);
        
        console.log('✅ Photo session completed successfully');
    }

    /**
     * Handle error state
     */
    handleErrorState(data) {
        const errorMessage = data?.message || 'An error occurred. Please try again.';
        
        if (this.elements.errorText) {
            DOMUtils.setText(this.elements.errorText, errorMessage);
        }
        
        // Stop any ongoing processes
        this.stopPhotoChecking();
        this.isProcessing = false;
        
        console.error('❌ Photo session error:', errorMessage);
    }

    // ============ Photo Management ============

    /**
     * Start checking for photo
     */
    startPhotoChecking() {
        if (this.photoCheckInterval) return;
        
        console.log('🔍 Starting photo check');
        
        this.photoCheckInterval = setInterval(() => {
            this.checkForPhoto();
        }, APP_CONFIG.UI.PHOTO_CHECK_INTERVAL);
        
        // Initial check
        this.checkForPhoto();
    }

    /**
     * Stop checking for photo
     */
    stopPhotoChecking() {
        if (this.photoCheckInterval) {
            clearInterval(this.photoCheckInterval);
            this.photoCheckInterval = null;
            console.log('⏹️ Stopped photo checking');
        }
    }

    /**
     * Check if photo is ready
     */
    async checkForPhoto() {
        if (this.currentState !== 'waiting' || this.isProcessing) return;
        
        try {
            const response = await api.checkPhoto(this.sessionId);
            
            if (response.success && response.data.photo_ready) {
                this.setState('review', {
                    photoData: response.data.photo_data
                });
            }
        } catch (error) {
            console.error('❌ Photo check error:', error);
            // Don't show error for check failures, keep trying
        }
    }

    /**
     * Display photo for review
     */
    displayPhoto(photoData) {
        if (!this.elements.photoImage || !photoData) return;
        
        try {
            // Set photo source
            this.elements.photoImage.src = `data:image/jpeg;base64,${photoData}`;
            
            // Add load event listener
            this.elements.photoImage.onload = () => {
                console.log('📸 Photo displayed successfully');
            };
            
            this.elements.photoImage.onerror = () => {
                console.error('❌ Failed to display photo');
                this.setState('error', { message: 'Failed to display photo' });
            };
            
        } catch (error) {
            console.error('❌ Photo display error:', error);
            this.setState('error', { message: 'Error displaying photo' });
        }
    }

    // ============ Action Handlers ============

    /**
     * Handle keep photo action
     */
    async handleKeepPhoto() {
        if (this.isProcessing) return;
        
        console.log('✅ Keeping photo...');
        
        // Set processing state
        this.setProcessingState(true, 'Sending your photo...');
        
        try {
            const response = await api.keepPhoto(this.sessionId);
            
            if (response.success) {
                this.setState('success', { message: response.data.message });
            } else {
                this.setState('error', { 
                    message: response.error || 'Failed to send photo' 
                });
            }
            
        } catch (error) {
            console.error('❌ Keep photo error:', error);
            this.setState('error', { 
                message: ErrorUtils.handleAPIError(error, 'Failed to send photo') 
            });
        } finally {
            this.setProcessingState(false);
        }
    }

    /**
     * Handle retake photo action
     */
    async handleRetakePhoto() {
        if (this.isProcessing) return;
        
        console.log('🔄 Requesting photo retake...');
        
        // Set processing state
        this.setProcessingState(true, 'Setting up retake...');
        
        try {
            const response = await api.retakePhoto(this.sessionId);
            
            if (response.success) {
                // Go back to waiting state
                this.setState('waiting');
                console.log('🔄 Retake started, waiting for new photo');
            } else {
                this.setState('error', { 
                    message: response.error || 'Failed to start retake' 
                });
            }
            
        } catch (error) {
            console.error('❌ Retake photo error:', error);
            this.setState('error', { 
                message: ErrorUtils.handleAPIError(error, 'Failed to start retake') 
            });
        } finally {
            this.setProcessingState(false);
        }
    }

    /**
     * Handle new session action
     */
    handleNewSession() {
        console.log('🔄 Starting new session...');
        
        // Clear current session
        SESSION_CONFIG.clearSession();
        
        // Redirect to registration
        window.location.href = 'mobile.html';
    }

    /**
     * Handle retry action
     */
    handleRetry() {
        console.log('🔄 Retrying...');
        
        // Go back to waiting state
        this.setState('waiting');
    }

    /**
     * Handle restart action
     */
    handleRestart() {
        console.log('🔄 Restarting session...');
        
        // Clear session and restart
        this.handleNewSession();
    }

    // ============ UI State Management ============

    /**
     * Set processing state
     */
    setProcessingState(isProcessing, message = 'Processing...') {
        this.isProcessing = isProcessing;
        
        if (isProcessing) {
            // Disable action buttons
            DOMUtils.setEnabled(this.elements.keepBtn, false);
            DOMUtils.setEnabled(this.elements.retakeBtn, false);
            
            // Show loading overlay
            UIUtils.showLoading(message);
            
            // Update loading text if element exists
            if (this.elements.loadingText) {
                DOMUtils.setText(this.elements.loadingText, message);
            }
        } else {
            // Re-enable action buttons
            DOMUtils.setEnabled(this.elements.keepBtn, true);
            DOMUtils.setEnabled(this.elements.retakeBtn, true);
            
            // Hide loading overlay
            UIUtils.hideLoading();
        }
    }

    // ============ Navigation ============

    /**
     * Redirect to registration page
     */
    redirectToRegistration(reason = 'Session expired') {
        console.log('🔄 Redirecting to registration:', reason);
        
        // Clear session
        SESSION_CONFIG.clearSession();
        
        // Show error and redirect
        this.setState('error', { 
            message: `${reason}. Redirecting to registration...` 
        });
        
        setTimeout(() => {
            window.location.href = 'mobile.html?from_photo=1';
        }, 3000);
    }

    // ============ Session Management ============

    /**
     * Check session validity
     */
    checkSessionValidity() {
        if (!this.sessionId) {
            this.redirectToRegistration('No session found');
            return false;
        }
        
        // Could add server-side session validation here
        return true;
    }

    /**
     * Refresh session
     */
    refreshSession() {
        // Extend session timeout
        console.log('🔄 Session refreshed');
    }

    // ============ Utility Methods ============

    /**
     * Get current session status
     */
    getStatus() {
        return {
            sessionId: this.sessionId,
            currentState: this.currentState,
            isProcessing: this.isProcessing,
            isCheckingPhoto: !!this.photoCheckInterval,
            hasValidSession: !!this.sessionId
        };
    }

    /**
     * Reset photo session
     */
    reset() {
        this.stopPhotoChecking();
        this.isProcessing = false;
        this.setState('waiting');
        
        // Clear photo display
        if (this.elements.photoImage) {
            this.elements.photoImage.src = '';
        }
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        this.stopPhotoChecking();
        
        // Clear photo blob URL if exists
        if (this.elements.photoImage && this.elements.photoImage.src.startsWith('blob:')) {
            URL.revokeObjectURL(this.elements.photoImage.src);
        }
    }
}

// ============ Utility Functions ============

/**
 * Check if user came from verification page
 */
function checkPreviousPage() {
    const urlParams = new URLSearchParams(window.location.search);
    const fromPhoto = urlParams.get('from_photo');
    
    if (fromPhoto) {
        // User was redirected here due to an error, show message
        console.log('📋 User redirected from photo session');
    }
}

/**
 * Handle browser refresh
 */
function handlePageRefresh() {
    // Check if we still have a valid session
    const sessionId = SESSION_CONFIG.getSessionId();
    
    if (!sessionId) {
        // No session, redirect to registration
        window.location.href = 'mobile.html?session_expired=1';
    }
}

// ============ Initialize on Page Load ============

let photoSessionManager;

document.addEventListener('DOMContentLoaded', () => {
    // Check previous page and session
    checkPreviousPage();
    handlePageRefresh();
    
    // Initialize photo session
    photoSessionManager = new PhotoSessionManager();
    
    // Export to global scope for debugging
    window.photoSessionManager = photoSessionManager;
    
    if (APP_CONFIG.DEBUG) {
        console.log('🔧 Photo session manager available globally as photoSessionManager');
        
        // Add debug commands
        window.photoDebug = {
            setState: (state, data) => photoSessionManager.setState(state, data),
            showReview: () => photoSessionManager.setState('review', {
                photoData: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==' // 1x1 pixel
            }),
            showSuccess: () => photoSessionManager.setState('success'),
            showError: (msg) => photoSessionManager.setState('error', { message: msg || 'Test error' }),
            keepPhoto: () => photoSessionManager.handleKeepPhoto(),
            retakePhoto: () => photoSessionManager.handleRetakePhoto(),
            reset: () => photoSessionManager.reset(),
            status: () => photoSessionManager.getStatus()
        };
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && photoSessionManager) {
        // Page became visible, refresh session and check photo
        photoSessionManager.refreshSession();
        
        if (photoSessionManager.currentState === 'waiting') {
            photoSessionManager.checkForPhoto();
        }
    }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (photoSessionManager) {
        photoSessionManager.cleanup();
    }
});