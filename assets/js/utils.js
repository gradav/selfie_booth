/**
 * Utility Functions for Selfie Booth
 * Common utility functions used across the application
 */

// ============ DOM Utilities ============

const DOMUtils = {
    /**
     * Get element by ID with error handling
     */
    getElementById(id) {
        const element = document.getElementById(id);
        if (!element && APP_CONFIG.DEBUG) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    },

    /**
     * Get elements by class name
     */
    getElementsByClassName(className) {
        return Array.from(document.getElementsByClassName(className));
    },

    /**
     * Add event listener with error handling
     */
    addEventListener(elementOrId, event, handler) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.addEventListener(event, handler);
            return true;
        }
        return false;
    },

    /**
     * Remove event listener
     */
    removeEventListener(elementOrId, event, handler) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.removeEventListener(event, handler);
        }
    },

    /**
     * Show element
     */
    show(elementOrId) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.style.display = 'block';
            element.classList.add('active');
        }
    },

    /**
     * Hide element
     */
    hide(elementOrId) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.style.display = 'none';
            element.classList.remove('active');
        }
    },

    /**
     * Toggle element visibility
     */
    toggle(elementOrId) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            if (element.style.display === 'none' || !element.classList.contains('active')) {
                this.show(element);
            } else {
                this.hide(element);
            }
        }
    },

    /**
     * Set text content safely
     */
    setText(elementOrId, text) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.textContent = text;
        }
    },

    /**
     * Set HTML content safely
     */
    setHTML(elementOrId, html) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.innerHTML = html;
        }
    },

    /**
     * Add CSS class
     */
    addClass(elementOrId, className) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.classList.add(className);
        }
    },

    /**
     * Remove CSS class
     */
    removeClass(elementOrId, className) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.classList.remove(className);
        }
    },

    /**
     * Toggle CSS class
     */
    toggleClass(elementOrId, className) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.classList.toggle(className);
        }
    },

    /**
     * Set element value
     */
    setValue(elementOrId, value) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.value = value;
        }
    },

    /**
     * Get element value
     */
    getValue(elementOrId) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        return element ? element.value : '';
    },

    /**
     * Enable/disable element
     */
    setEnabled(elementOrId, enabled) {
        const element = typeof elementOrId === 'string' 
            ? this.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.disabled = !enabled;
        }
    }
};

// ============ Form Utilities ============

const FormUtils = {
    /**
     * Get form data as object
     */
    getFormData(formElementOrId) {
        const form = typeof formElementOrId === 'string' 
            ? DOMUtils.getElementById(formElementOrId) 
            : formElementOrId;
            
        if (!form) return {};

        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    },

    /**
     * Validate form field
     */
    validateField(fieldElement, rules) {
        if (!fieldElement) return { isValid: true };

        const value = fieldElement.value.trim();
        const errors = [];

        // Required validation
        if (rules.required && !value) {
            errors.push(`${rules.label || 'Field'} is required`);
        }

        // Length validation
        if (value && rules.minLength && value.length < rules.minLength) {
            errors.push(`${rules.label || 'Field'} must be at least ${rules.minLength} characters`);
        }

        if (value && rules.maxLength && value.length > rules.maxLength) {
            errors.push(`${rules.label || 'Field'} must be less than ${rules.maxLength} characters`);
        }

        // Pattern validation
        if (value && rules.pattern && !rules.pattern.test(value)) {
            errors.push(rules.patternMessage || `${rules.label || 'Field'} format is invalid`);
        }

        // Custom validation
        if (value && rules.validator) {
            const customResult = rules.validator(value);
            if (!customResult.isValid) {
                errors.push(customResult.message);
            }
        }

        const isValid = errors.length === 0;
        
        // Update field appearance
        this.setFieldValidation(fieldElement, isValid, errors[0]);
        
        return { isValid, errors };
    },

    /**
     * Set field validation state
     */
    setFieldValidation(fieldElement, isValid, errorMessage = '') {
        const formGroup = fieldElement.closest('.form-group');
        
        // Remove existing validation classes
        DOMUtils.removeClass(fieldElement, 'error');
        DOMUtils.removeClass(fieldElement, 'success');
        
        if (formGroup) {
            DOMUtils.removeClass(formGroup, 'error');
            DOMUtils.removeClass(formGroup, 'success');
        }

        // Add appropriate class
        if (isValid) {
            DOMUtils.addClass(fieldElement, 'success');
            if (formGroup) DOMUtils.addClass(formGroup, 'success');
        } else {
            DOMUtils.addClass(fieldElement, 'error');
            if (formGroup) DOMUtils.addClass(formGroup, 'error');
        }

        // Show/hide error message
        if (formGroup) {
            let errorElement = formGroup.querySelector('.validation-message');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'validation-message';
                formGroup.appendChild(errorElement);
            }

            if (isValid) {
                DOMUtils.hide(errorElement);
            } else {
                DOMUtils.setText(errorElement, errorMessage);
                DOMUtils.addClass(errorElement, 'error');
                DOMUtils.show(errorElement);
            }
        }
    },

    /**
     * Clear form validation
     */
    clearValidation(formElementOrId) {
        const form = typeof formElementOrId === 'string' 
            ? DOMUtils.getElementById(formElementOrId) 
            : formElementOrId;
            
        if (!form) return;

        // Remove validation classes from all fields
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            DOMUtils.removeClass(field, 'error');
            DOMUtils.removeClass(field, 'success');
            
            const formGroup = field.closest('.form-group');
            if (formGroup) {
                DOMUtils.removeClass(formGroup, 'error');
                DOMUtils.removeClass(formGroup, 'success');
                
                const errorElement = formGroup.querySelector('.validation-message');
                if (errorElement) {
                    DOMUtils.hide(errorElement);
                }
            }
        });
    },

    /**
     * Reset form
     */
    resetForm(formElementOrId) {
        const form = typeof formElementOrId === 'string' 
            ? DOMUtils.getElementById(formElementOrId) 
            : formElementOrId;
            
        if (form && form.reset) {
            form.reset();
            this.clearValidation(form);
        }
    }
};

// ============ Loading/UI Utilities ============

const UIUtils = {
    /**
     * Show loading overlay
     */
    showLoading(message = APP_CONFIG.MESSAGES.INFO.LOADING) {
        let overlay = DOMUtils.getElementById('loading-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="spinner"></div>
                <div class="loading-text">${message}</div>
            `;
            document.body.appendChild(overlay);
        }
        
        const loadingText = overlay.querySelector('.loading-text');
        if (loadingText) {
            DOMUtils.setText(loadingText, message);
        }
        
        DOMUtils.addClass(overlay, 'active');
    },

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = DOMUtils.getElementById('loading-overlay');
        if (overlay) {
            DOMUtils.removeClass(overlay, 'active');
        }
    },

    /**
     * Show message
     */
    showMessage(elementId, message, type = 'info') {
        const element = DOMUtils.getElementById(elementId);
        if (!element) return;

        // Clear existing classes
        DOMUtils.removeClass(element, 'error');
        DOMUtils.removeClass(element, 'success');
        DOMUtils.removeClass(element, 'info');

        // Add appropriate class and content
        DOMUtils.addClass(element, type);
        DOMUtils.setHTML(element, `<div class="${type}">${message}</div>`);
        DOMUtils.show(element);

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                DOMUtils.hide(element);
            }, 5000);
        }
    },

    /**
     * Clear message
     */
    clearMessage(elementId) {
        const element = DOMUtils.getElementById(elementId);
        if (element) {
            DOMUtils.setHTML(element, '');
            DOMUtils.hide(element);
        }
    },

    /**
     * Animate element
     */
    animate(elementOrId, animationClass, duration = 500) {
        const element = typeof elementOrId === 'string' 
            ? DOMUtils.getElementById(elementOrId) 
            : elementOrId;
            
        if (!element) return;

        DOMUtils.addClass(element, animationClass);
        
        setTimeout(() => {
            DOMUtils.removeClass(element, animationClass);
        }, duration);
    },

    /**
     * Scroll to element
     */
    scrollTo(elementOrId, behavior = 'smooth') {
        const element = typeof elementOrId === 'string' 
            ? DOMUtils.getElementById(elementOrId) 
            : elementOrId;
            
        if (element) {
            element.scrollIntoView({ behavior, block: 'center' });
        }
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            return false;
        }
    }
};

// ============ Camera Utilities ============

const CameraUtils = {
    /**
     * Get user media with constraints
     */
    async getUserMedia(constraints = APP_CONFIG.PHOTO.CAMERA_CONSTRAINTS) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            return { success: true, stream };
        } catch (error) {
            console.error('Camera access error:', error);
            return { 
                success: false, 
                error: error.name === 'NotAllowedError' 
                    ? APP_CONFIG.MESSAGES.ERRORS.CAMERA_ACCESS
                    : `Camera error: ${error.message}`
            };
        }
    },

    /**
     * Capture photo from video element
     */
    capturePhoto(videoElement, canvasElement, quality = APP_CONFIG.PHOTO.QUALITY) {
        if (!videoElement || !canvasElement) {
            throw new Error('Video and canvas elements required');
        }

        const canvas = canvasElement;
        const context = canvas.getContext('2d');
        
        // Set canvas size to match video
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        
        // Draw the video frame
        context.drawImage(videoElement, 0, 0);
        
        // Get image data
        const dataURL = canvas.toDataURL(APP_CONFIG.PHOTO.FORMAT, quality);
        
        // Convert to blob
        return new Promise(resolve => {
            canvas.toBlob(resolve, APP_CONFIG.PHOTO.FORMAT, quality);
        });
    },

    /**
     * Stop video stream
     */
    stopStream(stream) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    }
};

// ============ Storage Utilities ============

const StorageUtils = {
    /**
     * Set item in localStorage with error handling
     */
    setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('LocalStorage set error:', error);
            return false;
        }
    },

    /**
     * Get item from localStorage with error handling
     */
    getItem(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('LocalStorage get error:', error);
            return defaultValue;
        }
    },

    /**
     * Remove item from localStorage
     */
    removeItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('LocalStorage remove error:', error);
            return false;
        }
    },

    /**
     * Clear all localStorage
     */
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('LocalStorage clear error:', error);
            return false;
        }
    },

    /**
     * Session storage methods
     */
    session: {
        setItem(key, value) {
            try {
                sessionStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.error('SessionStorage set error:', error);
                return false;
            }
        },

        getItem(key, defaultValue = null) {
            try {
                const item = sessionStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.error('SessionStorage get error:', error);
                return defaultValue;
            }
        },

        removeItem(key) {
            try {
                sessionStorage.removeItem(key);
                return true;
            } catch (error) {
                console.error('SessionStorage remove error:', error);
                return false;
            }
        },

        clear() {
            try {
                sessionStorage.clear();
                return true;
            } catch (error) {
                console.error('SessionStorage clear error:', error);
                return false;
            }
        }
    }
};

// ============ Error Handling Utilities ============

const ErrorUtils = {
    /**
     * Log error with context
     */
    logError(error, context = '', data = null) {
        const errorInfo = {
            message: error.message || error,
            context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href,
            data
        };

        console.error('🚨 Application Error:', errorInfo);
        
        // Could send to error reporting service here
        if (APP_CONFIG.DEBUG) {
            console.trace('Error stack trace:');
        }
    },

    /**
     * Handle API errors consistently
     */
    handleAPIError(error, fallbackMessage = APP_CONFIG.MESSAGES.ERRORS.NETWORK) {
        let message = fallbackMessage;
        
        if (error && typeof error === 'object') {
            if (error.message) {
                message = error.message;
            } else if (error.error) {
                message = error.error;
            }
        } else if (typeof error === 'string') {
            message = error;
        }

        this.logError(error, 'API Error');
        return message;
    },

    /**
     * Create error handler function
     */
    createErrorHandler(context, fallbackMessage) {
        return (error) => {
            const message = this.handleAPIError(error, fallbackMessage);
            this.logError(error, context);
            return message;
        };
    }
};

// ============ Performance Utilities ============

const PerformanceUtils = {
    /**
     * Measure function execution time
     */
    measure(name, fn) {
        return async function(...args) {
            const start = performance.now();
            const result = await fn.apply(this, args);
            const end = performance.now();
            
            if (APP_CONFIG.DEBUG) {
                console.log(`⏱️ ${name} took ${end - start} milliseconds`);
            }
            
            return result;
        };
    },

    /**
     * Create throttled function
     */
    throttle: UTILS.throttle,

    /**
     * Create debounced function
     */
    debounce: UTILS.debounce
};

// ============ Export to Global Scope ============

window.DOMUtils = DOMUtils;
window.FormUtils = FormUtils;
window.UIUtils = UIUtils;
window.CameraUtils = CameraUtils;
window.StorageUtils = StorageUtils;
window.ErrorUtils = ErrorUtils;
window.PerformanceUtils = PerformanceUtils;

if (APP_CONFIG.DEBUG) {
    console.log('🔧 Utility functions loaded');
}