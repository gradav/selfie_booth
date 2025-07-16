/**
 * Verification Logic for Selfie Booth
 * Handles verification code input and validation
 */

class VerificationManager {
    constructor() {
        this.sessionId = SESSION_CONFIG.getSessionId();
        this.isVerifying = false;
        this.autoSubmitEnabled = true;
        
        // Form elements
        this.form = DOMUtils.getElementById('verification-form');
        this.elements = {
            codeInput: DOMUtils.getElementById('code-input'),
            verifyBtn: DOMUtils.getElementById('verify-btn'),
            backBtn: DOMUtils.getElementById('back-btn'),
            message: DOMUtils.getElementById('message')
        };
        
        // Initialize
        this.init();
    }

    // ============ Initialization ============

    /**
     * Initialize verification page
     */
    init() {
        console.log('🔐 Initializing verification page');
        
        // Check if we have a valid session
        if (!this.sessionId) {
            this.redirectToRegistration('No active session found');
            return;
        }
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Focus code input
        this.focusCodeInput();
        
        // Set up auto-submit
        this.setupAutoSubmit();
        
        console.log('✅ Verification page initialized');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleVerification();
        });
        
        // Code input handling
        this.setupCodeInput();
        
        // Back button
        if (this.elements.backBtn) {
            this.elements.backBtn.addEventListener('click', () => {
                this.handleBackNavigation();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleBackNavigation();
            }
        });
    }

    /**
     * Set up code input behavior
     */
    setupCodeInput() {
        const input = this.elements.codeInput;
        if (!input) return;
        
        // Format input as numbers only
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, ''); // Remove non-digits
            
            // Limit to 6 digits
            if (value.length > 6) {
                value = value.slice(0, 6);
            }
            
            e.target.value = value;
            
            // Add typing animation
            DOMUtils.addClass(e.target, 'typing');
            setTimeout(() => {
                DOMUtils.removeClass(e.target, 'typing');
            }, 100);
            
            // Auto-submit when 6 digits are entered
            if (value.length === 6 && this.autoSubmitEnabled && !this.isVerifying) {
                setTimeout(() => {
                    this.handleVerification();
                }, 300); // Small delay for better UX
            }
            
            // Clear any previous error messages
            if (value.length > 0) {
                this.clearMessage();
            }
        });
        
        // Paste handling
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const digits = pastedText.replace(/\D/g, '').slice(0, 6);
            
            if (digits.length > 0) {
                input.value = digits;
                
                // Trigger input event for auto-submit
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        
        // Select all on focus
        input.addEventListener('focus', () => {
            input.select();
        });
        
        // Prevent non-numeric input
        input.addEventListener('keydown', (e) => {
            // Allow: backspace, delete, tab, escape, enter
            if ([8, 9, 27, 13, 46].indexOf(e.keyCode) !== -1 ||
                // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
                (e.keyCode === 65 && e.ctrlKey === true) ||
                (e.keyCode === 67 && e.ctrlKey === true) ||
                (e.keyCode === 86 && e.ctrlKey === true) ||
                (e.keyCode === 88 && e.ctrlKey === true)) {
                return;
            }
            
            // Ensure that it is a number and stop the keypress
            if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
                e.preventDefault();
            }
        });
    }

    /**
     * Set up auto-submit functionality
     */
    setupAutoSubmit() {
        // Auto-submit is enabled by default
        // Can be disabled if user manually clicks verify button
        this.elements.verifyBtn.addEventListener('click', () => {
            this.autoSubmitEnabled = false; // Disable auto-submit after manual click
        });
    }

    // ============ Verification Logic ============

    /**
     * Handle verification code submission
     */
    async handleVerification() {
        if (this.isVerifying) {
            console.log('🛑 Verification already in progress');
            return;
        }
        
        const code = this.elements.codeInput.value.trim();
        
        console.log('🔐 Attempting verification with code:', code);
        
        // Validate code format
        const validation = ValidationAPI.validateVerificationCode(code);
        if (!validation.isValid) {
            this.showError(validation.error);
            this.focusCodeInput();
            return;
        }
        
        // Clear previous messages
        this.clearMessage();
        
        // Set verifying state
        this.setVerifyingState(true);
        
        try {
            // Submit verification
            const response = await api.verify(code);
            
            if (response.success) {
                // Show success message
                this.showSuccess(APP_CONFIG.MESSAGES.SUCCESS.VERIFICATION);
                
                console.log('✅ Verification successful');
                
                // Redirect to photo session
                setTimeout(() => {
                    const redirectUrl = response.data.redirect || 'photo.html';
                    window.location.href = redirectUrl;
                }, 1000);
                
            } else {
                this.showError(response.error || APP_CONFIG.MESSAGES.ERRORS.VERIFICATION_FAILED);
                this.focusCodeInput();
                this.selectAllCode();
            }
            
        } catch (error) {
            console.error('❌ Verification error:', error);
            this.showError(ErrorUtils.handleAPIError(error, 'Verification failed. Please try again.'));
            this.focusCodeInput();
            this.selectAllCode();
        } finally {
            this.setVerifyingState(false);
        }
    }

    // ============ UI State Management ============

    /**
     * Set verifying state
     */
    setVerifyingState(isVerifying) {
        this.isVerifying = isVerifying;
        
        if (isVerifying) {
            DOMUtils.setEnabled(this.elements.verifyBtn, false);
            DOMUtils.setEnabled(this.elements.codeInput, false);
            DOMUtils.setText(this.elements.verifyBtn, 'Verifying...');
            UIUtils.showLoading('Verifying your code...');
        } else {
            DOMUtils.setEnabled(this.elements.verifyBtn, true);
            DOMUtils.setEnabled(this.elements.codeInput, true);
            DOMUtils.setText(this.elements.verifyBtn, 'Verify Code');
            UIUtils.hideLoading();
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        UIUtils.showMessage('message', message, 'error');
        
        // Add shake animation to input
        UIUtils.animate(this.elements.codeInput, 'shake', 500);
        
        // Re-enable auto-submit for retry
        this.autoSubmitEnabled = true;
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        UIUtils.showMessage('message', message, 'success');
    }

    /**
     * Clear message
     */
    clearMessage() {
        UIUtils.clearMessage('message');
    }

    // ============ Input Management ============

    /**
     * Focus code input
     */
    focusCodeInput() {
        if (this.elements.codeInput && !this.isVerifying) {
            setTimeout(() => {
                this.elements.codeInput.focus();
            }, 100);
        }
    }

    /**
     * Select all text in code input
     */
    selectAllCode() {
        if (this.elements.codeInput) {
            this.elements.codeInput.select();
        }
    }

    /**
     * Clear code input
     */
    clearCode() {
        if (this.elements.codeInput) {
            this.elements.codeInput.value = '';
            this.focusCodeInput();
        }
    }

    // ============ Navigation ============

    /**
     * Handle back navigation
     */
    handleBackNavigation() {
        if (this.isVerifying) {
            // Don't allow navigation during verification
            return;
        }
        
        if (confirm('Go back to registration? You\'ll need to enter your information again.')) {
            // Clear session and go back
            SESSION_CONFIG.clearSession();
            window.location.href = 'mobile.html';
        }
    }

    /**
     * Redirect to registration page
     */
    redirectToRegistration(reason = 'Session expired') {
        console.log('🔄 Redirecting to registration:', reason);
        
        // Clear any existing session
        SESSION_CONFIG.clearSession();
        
        // Show message and redirect
        this.showError(`${reason}. Redirecting to registration...`);
        
        setTimeout(() => {
            window.location.href = 'mobile.html?from_verify=1';
        }, 2000);
    }

    // ============ Session Management ============

    /**
     * Check session validity
     */
    async checkSession() {
        if (!this.sessionId) {
            this.redirectToRegistration('No session found');
            return false;
        }
        
        try {
            // This could check with the server if the session is still valid
            // For now, we'll assume it's valid if we have a session ID
            return true;
        } catch (error) {
            console.error('❌ Session check failed:', error);
            this.redirectToRegistration('Session validation failed');
            return false;
        }
    }

    /**
     * Refresh session (extend timeout)
     */
    refreshSession() {
        // This could make an API call to extend the session timeout
        console.log('🔄 Session refreshed');
    }

    // ============ Utility Methods ============

    /**
     * Get current verification status
     */
    getStatus() {
        return {
            sessionId: this.sessionId,
            isVerifying: this.isVerifying,
            autoSubmitEnabled: this.autoSubmitEnabled,
            currentCode: this.elements.codeInput ? this.elements.codeInput.value : '',
            hasValidSession: !!this.sessionId
        };
    }

    /**
     * Reset verification form
     */
    reset() {
        this.clearCode();
        this.clearMessage();
        this.setVerifyingState(false);
        this.autoSubmitEnabled = true;
        this.focusCodeInput();
    }
}

// ============ Utility Functions ============

/**
 * Format verification code for display
 */
function formatVerificationCode(code) {
    if (typeof code !== 'string') return '';
    
    // Add spaces between digits for better readability
    return code.replace(/(\d{3})(\d{3})/, '$1 $2');
}

/**
 * Generate random verification code (for testing)
 */
function generateTestCode() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// ============ Initialize on Page Load ============

let verificationManager;

document.addEventListener('DOMContentLoaded', () => {
    verificationManager = new VerificationManager();
    
    // Export to global scope for debugging
    window.verificationManager = verificationManager;
    
    if (APP_CONFIG.DEBUG) {
        console.log('🔧 Verification manager available globally as verificationManager');
        
        // Add debug commands
        window.verifyDebug = {
            fillTestCode: () => {
                if (verificationManager.elements.codeInput) {
                    verificationManager.elements.codeInput.value = generateTestCode();
                }
            },
            clearCode: () => verificationManager.clearCode(),
            verify: () => verificationManager.handleVerification(),
            reset: () => verificationManager.reset(),
            status: () => verificationManager.getStatus(),
            checkSession: () => verificationManager.checkSession()
        };
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && verificationManager) {
        // Page became visible, focus input and refresh session
        verificationManager.focusCodeInput();
        verificationManager.refreshSession();
    }
});

// Handle browser back button
window.addEventListener('beforeunload', () => {
    if (verificationManager && verificationManager.isVerifying) {
        // Don't allow leaving during verification
        return 'Verification in progress. Are you sure you want to leave?';
    }
});