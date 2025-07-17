/**
 * Utility Functions for Selfie Booth
 * Simplified version without validation styling
 */

export class FormUtils {
    /**
     * Show a message to the user
     */
    static showMessage(type, message) {
        // Clear any existing messages first
        FormUtils.clearMessages();
        
        // Find or create message container
        let messageContainer = document.querySelector(`.${type}`);
        
        if (!messageContainer) {
            // Create message container if it doesn't exist
            messageContainer = document.createElement('div');
            messageContainer.className = type;
            
            // Insert after the form
            const form = document.querySelector('form');
            if (form && form.parentNode) {
                form.parentNode.insertBefore(messageContainer, form.nextSibling);
            } else {
                document.body.appendChild(messageContainer);
            }
        }
        
        messageContainer.textContent = message;
        messageContainer.style.display = 'block';
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                FormUtils.clearMessages();
            }, 5000);
        }
    }
    
    /**
     * Clear all messages
     */
    static clearMessages() {
        const messageTypes = ['error', 'success', 'info', 'warning'];
        messageTypes.forEach(type => {
            const messages = document.querySelectorAll(`.${type}`);
            messages.forEach(msg => {
                msg.textContent = '';
                msg.style.display = 'none';
            });
        });
    }
    
    /**
     * Sanitize input to prevent XSS
     */
    static sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');
    }
    
    /**
     * Format phone number for display
     */
    static formatPhoneNumber(phone) {
        // Remove all non-digits
        const cleaned = phone.replace(/\D/g, '');
        
        // Format as (XXX) XXX-XXXX for US numbers
        if (cleaned.length === 10) {
            return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
        }
        
        // Format as +1 (XXX) XXX-XXXX for US numbers with country code
        if (cleaned.length === 11 && cleaned.startsWith('1')) {
            return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
        }
        
        // Return original if not a standard US format
        return phone;
    }
    
    /**
     * Validate email format (basic check)
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    /**
     * Validate phone number format
     */
    static isValidPhone(phone) {
        const cleaned = phone.replace(/\D/g, '');
        return cleaned.length >= 10 && cleaned.length <= 11;
    }
    
    /**
     * Get form data as object
     */
    static getFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    }
    
    /**
     * Debounce function calls
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Scroll element into view smoothly
     */
    static scrollToElement(element, offset = 0) {
        if (!element) return;
        
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
    
    /**
     * Copy text to clipboard
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                textArea.remove();
                return true;
            } catch (err) {
                textArea.remove();
                return false;
            }
        }
    }
    
    /**
     * Generate a random ID
     */
    static generateId(prefix = 'id') {
        return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Check if element is in viewport
     */
    static isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    /**
     * Add event listener that automatically removes itself
     */
    static addOneTimeListener(element, event, handler) {
        const wrappedHandler = (e) => {
            handler(e);
            element.removeEventListener(event, wrappedHandler);
        };
        element.addEventListener(event, wrappedHandler);
    }
    
    /**
     * Simple loading state manager
     */
    static setLoadingState(element, loading = true) {
        if (!element) return;
        
        if (loading) {
            element.classList.add('loading');
            element.disabled = true;
            element.setAttribute('data-original-text', element.textContent);
            element.textContent = 'Loading...';
        } else {
            element.classList.remove('loading');
            element.disabled = false;
            const originalText = element.getAttribute('data-original-text');
            if (originalText) {
                element.textContent = originalText;
                element.removeAttribute('data-original-text');
            }
        }
    }
}

// Export for use in other modules
window.FormUtils = FormUtils;