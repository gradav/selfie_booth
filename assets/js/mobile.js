/**
 * Mobile Registration Logic for Selfie Booth
 * Handles user registration form and validation
 */

class MobileRegistrationManager {
    constructor() {
        this.tabletId = TABLET_CONFIG.getTabletId();
        this.location = TABLET_CONFIG.getLocation();
        this.isSubmitting = false;
        
        // Form elements
        this.form = DOMUtils.getElementById('registration-form');
        this.elements = {
            firstName: DOMUtils.getElementById('firstName'),
            phone: DOMUtils.getElementById('phone'),
            email: DOMUtils.getElementById('email'),
            consent: DOMUtils.getElementById('consent'),
            submitBtn: DOMUtils.getElementById('submit-btn'),
            errorMessage: DOMUtils.getElementById('error-message'),
            successMessage: DOMUtils.getElementById('success-message')
        };
        
        // Validation rules
        this.validationRules = {
            firstName: {
                required: true,
                minLength: APP_CONFIG.VALIDATION.FIRST_NAME.MIN_LENGTH,
                maxLength: APP_CONFIG.VALIDATION.FIRST_NAME.MAX_LENGTH,
                pattern: APP_CONFIG.VALIDATION.FIRST_NAME.PATTERN,
                label: 'First name',
                patternMessage: 'First name can only contain letters, spaces, hyphens, apostrophes, and periods'
            },
            phone: {
                required: true,
                pattern: APP_CONFIG.VALIDATION.PHONE.PATTERN,
                label: 'Phone number',
                patternMessage: APP_CONFIG.MESSAGES.ERRORS.INVALID_PHONE
            },
            email: {
                required: false,
                pattern: APP_CONFIG.VALIDATION.EMAIL.PATTERN,
                label: 'Email',
                patternMessage: APP_CONFIG.MESSAGES.ERRORS.INVALID_EMAIL
            },
            consent: {
                required: true,
                label: 'Consent',
                validator: (value) => ({
                    isValid: !!value,
                    message: APP_CONFIG.MESSAGES.ERRORS.CONSENT_REQUIRED
                })
            }
        };
        
        // Initialize
        this.init();
    }

    // ============ Initialization ============

    /**
     * Initialize mobile registration
     */
    init() {
        console.log('📱 Initializing mobile registration');
        
        // Set up form validation
        this.setupFormValidation();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Focus first field
        this.focusFirstField();
        
        // Pre-fill form if returning user
        this.loadPreviousData();
        
        console.log('✅ Mobile registration initialized');
    }

    /**
     * Set up form validation
     */
    setupFormValidation() {
        // Real-time validation for each field
        Object.keys(this.validationRules).forEach(fieldName => {
            const element = this.elements[fieldName];
            if (!element) return;
            
            const rules = this.validationRules[fieldName];
            
            // Validate on blur (when user leaves field)
            element.addEventListener('blur', () => {
                this.validateField(fieldName);
            });
            
            // For text inputs, also validate on input with debouncing
            if (element.type === 'text' || element.type === 'tel' || element.type === 'email') {
                const debouncedValidation = UTILS.debounce(() => {
                    this.validateField(fieldName);
                }, 500);
                
                element.addEventListener('input', debouncedValidation);
            }
            
            // For checkbox, validate on change
            if (element.type === 'checkbox') {
                element.addEventListener('change', () => {
                    this.validateField(fieldName);
                });
            }
        });
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // Phone number formatting
        this.elements.phone.addEventListener('input', (e) => {
            this.formatPhoneNumber(e.target);
        });
        
        // Prevent double-tap zoom on iOS
        this.elements.firstName.addEventListener('touchend', (e) => {
            e.preventDefault();
            e.target.focus();
        });
        
        // Enter key handling
        Object.values(this.elements).forEach(element => {
            if (element && element.type !== 'checkbox') {
                element.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.handleEnterKey(element);
                    }
                });
            }
        });
    }

    // ============ Form Handling ============

    /**
     * Handle form submission
     */
    async handleSubmit() {
        if (this.isSubmitting) return;
        
        console.log('📝 Processing registration...');
        
        // Clear previous messages
        this.clearMessages();
        
        // Validate entire form
        const isValid = this.validateForm();
        if (!isValid) {
            this.showError('Please fix the errors above');
            return;
        }
        
        // Get form data
        const formData = this.getFormData();
        
        // Show loading state
        this.setSubmittingState(true);
        
        try {
            // Submit registration
            const response = await api.register(formData);
            
            if (response.success) {
                // Store session ID
                SESSION_CONFIG.setSessionId(response.data.session_id);
                SESSION_CONFIG.setUserData(formData);
                
                // Show success message
                this.showSuccess(APP_CONFIG.MESSAGES.SUCCESS.REGISTRATION);
                
                // Redirect to verification page
                setTimeout(() => {
                    window.location.href = 'verify.html';
                }, 1500);
                
                console.log('✅ Registration successful');
                
            } else {
                this.showError(response.error || APP_CONFIG.MESSAGES.ERRORS.REGISTRATION_FAILED);
            }
            
        } catch (error) {
            console.error('❌ Registration error:', error);
            this.showError(ErrorUtils.handleAPIError(error));
        } finally {
            this.setSubmittingState(false);
        }
    }

    /**
     * Get form data
     */
    getFormData() {
        return {
            firstName: this.elements.firstName.value.trim(),
            phone: this.elements.phone.value.trim(),
            email: this.elements.email.value.trim(),
            consent: this.elements.consent.checked,
            tabletId: this.tabletId,
            location: this.location
        };
    }

    /**
     * Validate entire form
     */
    validateForm() {
        let isValid = true;
        
        // Validate each field
        Object.keys(this.validationRules).forEach(fieldName => {
            const fieldValid = this.validateField(fieldName);
            if (!fieldValid) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * Validate individual field
     */
    validateField(fieldName) {
        const element = this.elements[fieldName];
        const rules = this.validationRules[fieldName];
        
        if (!element || !rules) return true;
        
        const value = element.type === 'checkbox' ? element.checked : element.value.trim();
        const result = FormUtils.validateField(element, rules);
        
        return result.isValid;
    }

    // ============ UI State Management ============

    /**
     * Set submitting state
     */
    setSubmittingState(isSubmitting) {
        this.isSubmitting = isSubmitting;
        
        if (isSubmitting) {
            DOMUtils.setEnabled(this.elements.submitBtn, false);
            DOMUtils.setText(this.elements.submitBtn, 'Registering...');
            UIUtils.showLoading('Creating your session...');
        } else {
            DOMUtils.setEnabled(this.elements.submitBtn, true);
            DOMUtils.setText(this.elements.submitBtn, 'Start Photo Session');
            UIUtils.hideLoading();
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        UIUtils.showMessage('error-message', message, 'error');
        UIUtils.clearMessage('success-message');
        
        // Scroll to error message
        UIUtils.scrollTo(this.elements.errorMessage);
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        UIUtils.showMessage('success-message', message, 'success');
        UIUtils.clearMessage('error-message');
    }

    /**
     * Clear all messages
     */
    clearMessages() {
        UIUtils.clearMessage('error-message');
        UIUtils.clearMessage('success-message');
    }

    // ============ Input Formatting ============

    /**
     * Format phone number as user types
     */
    formatPhoneNumber(input) {
        let value = input.value.replace(/\D/g, ''); // Remove all non-digits
        
        // Apply formatting
        if (value.length >= 6) {
            value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
        } else if (value.length >= 3) {
            value = value.replace(/(\d{3})(\d{0,3})/, '($1) $2');
        }
        
        input.value = value;
    }

    /**
     * Handle Enter key navigation
     */
    handleEnterKey(currentElement) {
        // Find next focusable element
        const focusableElements = [
            this.elements.firstName,
            this.elements.phone,
            this.elements.email,
            this.elements.consent,
            this.elements.submitBtn
        ].filter(el => el && !el.disabled);
        
        const currentIndex = focusableElements.indexOf(currentElement);
        
        if (currentIndex >= 0 && currentIndex < focusableElements.length - 1) {
            // Focus next element
            focusableElements[currentIndex + 1].focus();
        } else {
            // Submit form if on last element
            this.handleSubmit();
        }
    }

    /**
     * Focus first field
     */
    focusFirstField() {
        if (this.elements.firstName) {
            // Delay focus to ensure page is fully loaded
            setTimeout(() => {
                this.elements.firstName.focus();
            }, 100);
        }
    }

    // ============ Data Persistence ============

    /**
     * Load previous data if available
     */
    loadPreviousData() {
        const userData = SESSION_CONFIG.getUserData();
        if (!userData) return;
        
        // Pre-fill form fields (except consent)
        if (userData.firstName) {
            DOMUtils.setValue(this.elements.firstName, userData.firstName);
        }
        if (userData.phone) {
            DOMUtils.setValue(this.elements.phone, UTILS.formatPhoneNumber(userData.phone));
        }
        if (userData.email) {
            DOMUtils.setValue(this.elements.email, userData.email);
        }
        
        console.log('📋 Pre-filled form with previous data');
    }

    /**
     * Save form data for later use
     */
    saveFormData() {
        const formData = this.getFormData();
        SESSION_CONFIG.setUserData(formData);
    }

    // ============ Utility Methods ============

    /**
     * Reset form to initial state
     */
    reset() {
        FormUtils.resetForm(this.form);
        this.clearMessages();
        this.focusFirstField();
        SESSION_CONFIG.clearSession();
    }

    /**
     * Get registration status
     */
    getStatus() {
        return {
            isSubmitting: this.isSubmitting,
            tabletId: this.tabletId,
            location: this.location,
            hasUserData: !!SESSION_CONFIG.getUserData(),
            sessionId: SESSION_CONFIG.getSessionId()
        };
    }
}

// ============ Utility Functions ============

/**
 * Handle back navigation
 */
function handleBackNavigation() {
    if (confirm('Are you sure you want to go back? Your information will be lost.')) {
        SESSION_CONFIG.clearSession();
        window.history.back();
    }
}

/**
 * Check for registration parameters in URL
 */
function checkURLParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check for tablet_id and location
    const tabletId = urlParams.get('tablet_id');
    const location = urlParams.get('location');
    
    if (tabletId) {
        SESSION_CONFIG.setSessionId('tablet_id', tabletId);
    }
    if (location) {
        SESSION_CONFIG.setSessionId('location', location);
    }
    
    // Check for pre-filled data
    const firstName = urlParams.get('firstName');
    const phone = urlParams.get('phone');
    const email = urlParams.get('email');
    
    if (firstName || phone || email) {
        SESSION_CONFIG.setUserData({
            firstName: firstName || '',
            phone: phone || '',
            email: email || ''
        });
    }
}

// ============ Initialize on Page Load ============

let mobileManager;

document.addEventListener('DOMContentLoaded', () => {
    // Check URL parameters first
    checkURLParameters();
    
    // Initialize mobile registration
    mobileManager = new MobileRegistrationManager();
    
    // Export to global scope for debugging
    window.mobileManager = mobileManager;
    
    // Add back button functionality if needed
    const backBtn = DOMUtils.getElementById('back-btn');
    if (backBtn) {
        DOMUtils.addEventListener(backBtn, 'click', handleBackNavigation);
    }
    
    if (APP_CONFIG.DEBUG) {
        console.log('🔧 Mobile manager available globally as mobileManager');
        
        // Add debug commands
        window.mobileDebug = {
            fillTestData: () => {
                DOMUtils.setValue(mobileManager.elements.firstName, 'Test User');
                DOMUtils.setValue(mobileManager.elements.phone, '(555) 123-4567');
                DOMUtils.setValue(mobileManager.elements.email, 'test@example.com');
                mobileManager.elements.consent.checked = true;
            },
            validateForm: () => mobileManager.validateForm(),
            reset: () => mobileManager.reset(),
            status: () => mobileManager.getStatus(),
            submit: () => mobileManager.handleSubmit()
        };
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && mobileManager) {
        // Page became visible, focus first field if form is empty
        const formData = mobileManager.getFormData();
        if (!formData.firstName && !formData.phone) {
            mobileManager.focusFirstField();
        }
    }
});