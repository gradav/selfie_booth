/**
 * Mobile Registration Page Handler
 * Simplified version without automatic validation
 */

import { APIClient } from './api.js';
import { FormUtils } from './utils.js';

class MobileRegistration {
    constructor() {
        this.apiClient = new APIClient();
        this.fields = {};
        this.isSubmitting = false;
        
        // Initialize when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        console.log('🎯 Initializing mobile registration...');
        
        try {
            this.setupFormElements();
            this.setupEventListeners();
            this.extractURLParams();
            
            console.log('✅ Mobile registration initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize mobile registration:', error);
            this.showError('Failed to initialize registration form');
        }
    }
    
    setupFormElements() {
        // Get form elements
        this.form = document.getElementById('registration-form');
        this.submitBtn = document.getElementById('submit-btn');
        this.loadingOverlay = document.querySelector('.loading-overlay');
        
        // Get input fields
        this.fields = {
            firstName: document.getElementById('firstName'),
            phone: document.getElementById('phone'),
            email: document.getElementById('email'),
            agreeToSMS: document.getElementById('agreeToSMS')
        };
        
        // Verify all elements exist
        const missingElements = [];
        if (!this.form) missingElements.push('registration-form');
        if (!this.submitBtn) missingElements.push('submit-btn');
        
        Object.entries(this.fields).forEach(([key, element]) => {
            if (!element) missingElements.push(key);
        });
        
        if (missingElements.length > 0) {
            throw new Error(`Missing form elements: ${missingElements.join(', ')}`);
        }
        
        console.log('📝 Form elements found and configured');
    }
    
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // NO automatic validation - removed input/blur listeners
        console.log('🎧 Event listeners configured (no auto-validation)');
    }
    
    extractURLParams() {
        const urlParams = new URLSearchParams(window.location.search);
        this.tabletId = urlParams.get('tablet_id') || 'UNKNOWN';
        this.location = urlParams.get('location') || 'unknown';
        
        console.log(`📍 Registration for tablet: ${this.tabletId} at ${this.location}`);
    }
    
    async handleSubmit(event) {
        event.preventDefault();
        
        if (this.isSubmitting) {
            console.log('⏳ Form already submitting...');
            return;
        }
        
        console.log('📤 Starting form submission...');
        
        try {
            this.isSubmitting = true;
            this.setLoadingState(true);
            this.clearMessages();
            
            // Get form data without validation
            const formData = this.getFormData();
            console.log('📋 Form data collected:', { ...formData, phone: '[HIDDEN]' });
            
            // Submit to API
            const response = await this.apiClient.register(formData);
            console.log('✅ Registration successful:', response);
            
            // Show success and redirect
            this.showSuccess('Registration successful! Look at the kiosk screen for your verification code.');
            
            // Redirect to verification page after short delay
            setTimeout(() => {
                const verifyUrl = `verify.html?tablet_id=${this.tabletId}&location=${this.location}`;
                console.log(`🔄 Redirecting to: ${verifyUrl}`);
                window.location.href = verifyUrl;
            }, 2000);
            
        } catch (error) {
            console.error('❌ Registration failed:', error);
            this.showError(this.getErrorMessage(error));
        } finally {
            this.isSubmitting = false;
            this.setLoadingState(false);
        }
    }
    
    getFormData() {
        return {
            firstName: this.fields.firstName.value.trim(),
            phone: this.fields.phone.value.trim(),
            email: this.fields.email.value.trim(),
            agreeToSMS: this.fields.agreeToSMS.checked,
            tabletId: this.tabletId,
            location: this.location
        };
    }
    
    setLoadingState(loading) {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.toggle('active', loading);
        }
        
        if (this.submitBtn) {
            this.submitBtn.disabled = loading;
            this.submitBtn.textContent = loading ? 'Submitting...' : 'Start Photo Session';
        }
        
        // Disable form inputs
        Object.values(this.fields).forEach(field => {
            if (field) field.disabled = loading;
        });
    }
    
    showError(message) {
        FormUtils.showMessage('error', message);
    }
    
    showSuccess(message) {
        FormUtils.showMessage('success', message);
    }
    
    clearMessages() {
        FormUtils.clearMessages();
    }
    
    getErrorMessage(error) {
        if (error.message) {
            return error.message;
        }
        
        if (error.status) {
            switch (error.status) {
                case 400:
                    return 'Please check your information and try again.';
                case 404:
                    return 'Registration service not available. Please try again later.';
                case 500:
                    return 'Server error. Please try again later.';
                default:
                    return `Request failed (${error.status}). Please try again.`;
            }
        }
        
        return 'Network error. Please check your connection and try again.';
    }
}

// Initialize when script loads
console.log('📱 Loading mobile registration...');
new MobileRegistration();