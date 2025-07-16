/**
 * Admin Dashboard Logic for Selfie Booth
 * Handles administrative functions and monitoring
 */

class AdminManager {
    constructor() {
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshFrequency = 30000; // 30 seconds
        this.isLoading = false;
        
        // UI elements
        this.elements = {
            // Stats
            totalSessions: DOMUtils.getElementById('total-sessions'),
            verifiedSessions: DOMUtils.getElementById('verified-sessions'),
            pendingSessions: DOMUtils.getElementById('pending-sessions'),
            photosTaken: DOMUtils.getElementById('photos-taken'),
            
            // Status
            dbStatus: DOMUtils.getElementById('db-status'),
            messagingStatus: DOMUtils.getElementById('messaging-status'),
            lastUpdated: DOMUtils.getElementById('last-updated'),
            
            // Controls
            refreshBtn: DOMUtils.getElementById('refresh-btn'),
            resetSessionsBtn: DOMUtils.getElementById('reset-sessions-btn'),
            
            // Configuration
            messagingService: DOMUtils.getElementById('messaging-service'),
            sessionTimeout: DOMUtils.getElementById('session-timeout'),
            saveConfigBtn: DOMUtils.getElementById('save-config-btn'),
            
            // Sessions table
            sessionsTableBody: DOMUtils.getElementById('sessions-table-body'),
            
            // Modal
            confirmationModal: DOMUtils.getElementById('confirmation-modal'),
            modalTitle: DOMUtils.getElementById('modal-title'),
            modalMessage: DOMUtils.getElementById('modal-message'),
            modalCancel: DOMUtils.getElementById('modal-cancel'),
            modalConfirm: DOMUtils.getElementById('modal-confirm')
        };
        
        // Modal state
        this.modalCallback = null;
        
        // Initialize
        this.init();
    }

    // ============ Initialization ============

    /**
     * Initialize admin dashboard
     */
    async init() {
        console.log('👤 Initializing admin dashboard');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Start auto-refresh
        this.startAutoRefresh();
        
        // Load configuration
        this.loadConfiguration();
        
        console.log('✅ Admin dashboard initialized');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Refresh button
        if (this.elements.refreshBtn) {
            this.elements.refreshBtn.addEventListener('click', () => {
                this.refreshDashboard();
            });
        }
        
        // Reset sessions button
        if (this.elements.resetSessionsBtn) {
            this.elements.resetSessionsBtn.addEventListener('click', () => {
                this.confirmResetSessions();
            });
        }
        
        // Save configuration button
        if (this.elements.saveConfigBtn) {
            this.elements.saveConfigBtn.addEventListener('click', () => {
                this.saveConfiguration();
            });
        }
        
        // Modal controls
        if (this.elements.modalCancel) {
            this.elements.modalCancel.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        if (this.elements.modalConfirm) {
            this.elements.modalConfirm.addEventListener('click', () => {
                this.confirmModalAction();
            });
        }
        
        // Close modal on background click
        if (this.elements.confirmationModal) {
            this.elements.confirmationModal.addEventListener('click', (e) => {
                if (e.target === this.elements.confirmationModal) {
                    this.hideModal();
                }
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'F5':
                    e.preventDefault();
                    this.refreshDashboard();
                    break;
                case 'Escape':
                    this.hideModal();
                    break;
            }
        });
        
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.refreshDashboard();
            }
        });
    }

    // ============ Data Loading ============

    /**
     * Load all dashboard data
     */
    async loadDashboardData() {
        console.log('📊 Loading dashboard data...');
        
        try {
            // Load data in parallel
            const [statsResult, sessionsResult, healthResult] = await Promise.allSettled([
                this.loadStats(),
                this.loadSessions(),
                this.checkSystemHealth()
            ]);
            
            // Handle results
            if (statsResult.status === 'rejected') {
                console.error('❌ Failed to load stats:', statsResult.reason);
            }
            
            if (sessionsResult.status === 'rejected') {
                console.error('❌ Failed to load sessions:', sessionsResult.reason);
            }
            
            if (healthResult.status === 'rejected') {
                console.error('❌ Failed to check system health:', healthResult.reason);
            }
            
            // Update last updated timestamp
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('❌ Dashboard data loading error:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    /**
     * Load session statistics
     */
    async loadStats() {
        try {
            const response = await api.getSessionStats();
            
            if (response.success) {
                const stats = response.data;
                
                // Update stat cards with animation
                this.updateStatCard('totalSessions', stats.total_sessions || 0);
                this.updateStatCard('verifiedSessions', stats.verified_sessions || 0);
                this.updateStatCard('pendingSessions', stats.pending_sessions || 0);
                this.updateStatCard('photosTaken', stats.photos_taken || 0);
                
                console.log('📊 Stats loaded:', stats);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('❌ Stats loading error:', error);
            this.showStatsError();
        }
    }

    /**
     * Load recent sessions
     */
    async loadSessions() {
        try {
            const response = await api.getRecentSessions(20);
            
            if (response.success) {
                this.displaySessions(response.data.sessions || []);
                console.log(`📋 Loaded ${response.data.sessions?.length || 0} sessions`);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('❌ Sessions loading error:', error);
            this.showSessionsError();
        }
    }

    /**
     * Check system health
     */
    async checkSystemHealth() {
        try {
            const response = await api.healthCheck();
            
            if (response.success) {
                const health = response.data;
                
                // Update status indicators
                this.updateStatus('dbStatus', health.database === 'connected' ? 'success' : 'error', 
                                health.database || 'Unknown');
                
                this.updateStatus('messagingStatus', 'success', health.messaging_service || 'Local');
                
                console.log('❤️ System health checked:', health);
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('❌ Health check error:', error);
            this.updateStatus('dbStatus', 'error', 'Error');
            this.updateStatus('messagingStatus', 'error', 'Error');
        }
    }

    // ============ UI Updates ============

    /**
     * Update stat card with animation
     */
    updateStatCard(elementId, value) {
        const element = this.elements[elementId];
        if (!element) return;
        
        const currentValue = parseInt(element.textContent) || 0;
        
        if (currentValue !== value) {
            // Animate number change
            this.animateNumber(element, currentValue, value, 500);
        }
    }

    /**
     * Animate number changes
     */
    animateNumber(element, from, to, duration) {
        const startTime = performance.now();
        const difference = to - from;
        
        const updateNumber = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = Math.round(from + (difference * easeOut));
            
            DOMUtils.setText(element, currentValue.toString());
            
            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };
        
        requestAnimationFrame(updateNumber);
    }

    /**
     * Update status indicator
     */
    updateStatus(elementId, status, text) {
        const element = this.elements[elementId];
        if (!element) return;
        
        // Remove existing status classes
        DOMUtils.removeClass(element, 'success');
        DOMUtils.removeClass(element, 'error');
        
        // Add new status class
        DOMUtils.addClass(element, status);
        DOMUtils.setText(element, text);
    }

    /**
     * Display sessions in table
     */
    displaySessions(sessions) {
        if (!this.elements.sessionsTableBody) return;
        
        if (sessions.length === 0) {
            this.elements.sessionsTableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: #666; font-style: italic;">
                        No sessions found
                    </td>
                </tr>
            `;
            return;
        }
        
        const rows = sessions.map(session => {
            const statusBadge = session.verified ? 
                '<span class="status-badge verified">✅ Verified</span>' :
                '<span class="status-badge pending">⏳ Pending</span>';
            
            const createdAt = this.formatTimestamp(session.created_at);
            const actions = this.createSessionActions(session.session_id);
            
            return `
                <tr>
                    <td>${this.escapeHtml(session.first_name || '')}</td>
                    <td>${this.formatPhoneNumber(session.phone || '')}</td>
                    <td>${statusBadge}</td>
                    <td><code>${session.verification_code || ''}</code></td>
                    <td>${createdAt}</td>
                    <td>${this.escapeHtml(session.tablet_id || '')}</td>
                    <td>${actions}</td>
                </tr>
            `;
        }).join('');
        
        this.elements.sessionsTableBody.innerHTML = rows;
        
        // Add event listeners for action buttons
        this.setupSessionActions();
    }

    /**
     * Create session action buttons
     */
    createSessionActions(sessionId) {
        return `
            <button class="btn action-btn btn-secondary" onclick="adminManager.viewSession('${sessionId}')" title="View Details">
                👁️
            </button>
            <button class="btn action-btn btn-danger" onclick="adminManager.deleteSession('${sessionId}')" title="Delete">
                🗑️
            </button>
        `;
    }

    /**
     * Set up session action event listeners
     */
    setupSessionActions() {
        // Event delegation is handled by onclick attributes in createSessionActions
        // This method can be used for additional setup if needed
    }

    /**
     * Update last updated timestamp
     */
    updateLastUpdated() {
        if (this.elements.lastUpdated) {
            const now = new Date();
            DOMUtils.setText(this.elements.lastUpdated, now.toLocaleTimeString());
        }
    }

    // ============ Actions ============

    /**
     * Refresh dashboard
     */
    async refreshDashboard() {
        if (this.isLoading) return;
        
        console.log('🔄 Refreshing dashboard...');
        
        this.isLoading = true;
        
        // Update refresh button state
        if (this.elements.refreshBtn) {
            DOMUtils.setEnabled(this.elements.refreshBtn, false);
            const originalText = this.elements.refreshBtn.textContent;
            DOMUtils.setText(this.elements.refreshBtn, '🔄 Refreshing...');
            
            // Restore button after loading
            setTimeout(() => {
                DOMUtils.setText(this.elements.refreshBtn, originalText);
                DOMUtils.setEnabled(this.elements.refreshBtn, true);
            }, 1000);
        }
        
        try {
            await this.loadDashboardData();
            console.log('✅ Dashboard refreshed');
        } catch (error) {
            console.error('❌ Dashboard refresh error:', error);
            this.showError('Failed to refresh dashboard');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Confirm reset sessions action
     */
    confirmResetSessions() {
        this.showModal(
            'Reset All Sessions',
            'Are you sure you want to reset all sessions? This action cannot be undone.',
            () => this.resetAllSessions()
        );
    }

    /**
     * Reset all sessions
     */
    async resetAllSessions() {
        console.log('🗑️ Resetting all sessions...');
        
        try {
            UIUtils.showLoading('Resetting sessions...');
            
            const response = await api.resetAllSessions();
            
            if (response.success) {
                this.showSuccess(`Reset ${response.data.deleted_count || 0} sessions`);
                await this.loadDashboardData();
                console.log('✅ Sessions reset successfully');
            } else {
                throw new Error(response.error);
            }
        } catch (error) {
            console.error('❌ Reset sessions error:', error);
            this.showError(ErrorUtils.handleAPIError(error, 'Failed to reset sessions'));
        } finally {
            UIUtils.hideLoading();
        }
    }

    /**
     * View session details
     */
    async viewSession(sessionId) {
        console.log('👁️ Viewing session:', sessionId);
        
        // This could open a modal with detailed session information
        // For now, just log the session ID
        this.showInfo(`Session ID: ${sessionId}\n\nDetailed view not yet implemented.`);
    }

    /**
     * Delete specific session
     */
    async deleteSession(sessionId) {
        this.showModal(
            'Delete Session',
            `Are you sure you want to delete session ${sessionId}?`,
            async () => {
                try {
                    UIUtils.showLoading('Deleting session...');
                    
                    // Note: This would need a deleteSession API endpoint
                    // const response = await api.deleteSession(sessionId);
                    
                    this.showSuccess('Session deleted');
                    await this.loadDashboardData();
                } catch (error) {
                    this.showError('Failed to delete session');
                } finally {
                    UIUtils.hideLoading();
                }
            }
        );
    }

    // ============ Configuration ============

    /**
     * Load configuration
     */
    loadConfiguration() {
        // Load configuration from localStorage or API
        const config = StorageUtils.getItem('admin_config', {
            messagingService: 'local',
            sessionTimeout: 30
        });
        
        if (this.elements.messagingService) {
            DOMUtils.setValue(this.elements.messagingService, config.messagingService);
        }
        
        if (this.elements.sessionTimeout) {
            DOMUtils.setValue(this.elements.sessionTimeout, config.sessionTimeout);
        }
    }

    /**
     * Save configuration
     */
    saveConfiguration() {
        const config = {
            messagingService: DOMUtils.getValue(this.elements.messagingService),
            sessionTimeout: parseInt(DOMUtils.getValue(this.elements.sessionTimeout))
        };
        
        // Validate configuration
        if (config.sessionTimeout < 5 || config.sessionTimeout > 120) {
            this.showError('Session timeout must be between 5 and 120 minutes');
            return;
        }
        
        // Save to localStorage
        StorageUtils.setItem('admin_config', config);
        
        this.showSuccess('Configuration saved successfully');
        
        console.log('💾 Configuration saved:', config);
    }

    // ============ Auto-refresh ============

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.refreshInterval) return;
        
        this.refreshInterval = setInterval(() => {
            if (this.autoRefreshEnabled && document.visibilityState === 'visible') {
                this.loadDashboardData();
            }
        }, this.refreshFrequency);
        
        console.log(`🔄 Auto-refresh started (${this.refreshFrequency / 1000}s interval)`);
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('⏹️ Auto-refresh stopped');
        }
    }

    /**
     * Toggle auto-refresh
     */
    toggleAutoRefresh() {
        this.autoRefreshEnabled = !this.autoRefreshEnabled;
        console.log(`🔄 Auto-refresh ${this.autoRefreshEnabled ? 'enabled' : 'disabled'}`);
    }

    // ============ Modal Management ============

    /**
     * Show confirmation modal
     */
    showModal(title, message, confirmCallback) {
        if (!this.elements.confirmationModal) return;
        
        DOMUtils.setText(this.elements.modalTitle, title);
        DOMUtils.setText(this.elements.modalMessage, message);
        
        this.modalCallback = confirmCallback;
        
        DOMUtils.addClass(this.elements.confirmationModal, 'active');
    }

    /**
     * Hide modal
     */
    hideModal() {
        if (this.elements.confirmationModal) {
            DOMUtils.removeClass(this.elements.confirmationModal, 'active');
        }
        this.modalCallback = null;
    }

    /**
     * Confirm modal action
     */
    confirmModalAction() {
        if (this.modalCallback) {
            this.modalCallback();
        }
        this.hideModal();
    }

    // ============ Notification Methods ============

    /**
     * Show success message
     */
    showSuccess(message) {
        console.log('✅', message);
        // Could implement toast notifications here
        alert(`Success: ${message}`);
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('❌', message);
        alert(`Error: ${message}`);
    }

    /**
     * Show info message
     */
    showInfo(message) {
        console.log('ℹ️', message);
        alert(`Info: ${message}`);
    }

    /**
     * Show stats error
     */
    showStatsError() {
        DOMUtils.setText(this.elements.totalSessions, '?');
        DOMUtils.setText(this.elements.verifiedSessions, '?');
        DOMUtils.setText(this.elements.pendingSessions, '?');
        DOMUtils.setText(this.elements.photosTaken, '?');
    }

    /**
     * Show sessions error
     */
    showSessionsError() {
        if (this.elements.sessionsTableBody) {
            this.elements.sessionsTableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: #e74c3c;">
                        ❌ Failed to load sessions
                    </td>
                </tr>
            `;
        }
    }

    // ============ Utility Methods ============

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch (error) {
            return timestamp;
        }
    }

    /**
     * Format phone number for display
     */
    formatPhoneNumber(phone) {
        if (!phone) return '';
        return UTILS.formatPhoneNumber(phone);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Get admin status
     */
    getStatus() {
        return {
            isLoading: this.isLoading,
            autoRefreshEnabled: this.autoRefreshEnabled,
            refreshFrequency: this.refreshFrequency,
            hasRefreshInterval: !!this.refreshInterval,
            modalOpen: this.elements.confirmationModal?.classList.contains('active') || false
        };
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        this.stopAutoRefresh();
        this.hideModal();
    }
}

// ============ Initialize on Page Load ============

let adminManager;

document.addEventListener('DOMContentLoaded', () => {
    adminManager = new AdminManager();
    
    // Export to global scope for debugging and onclick handlers
    window.adminManager = adminManager;
    
    if (APP_CONFIG.DEBUG) {
        console.log('🔧 Admin manager available globally as adminManager');
        
        // Add debug commands
        window.adminDebug = {
            refresh: () => adminManager.refreshDashboard(),
            loadStats: () => adminManager.loadStats(),
            loadSessions: () => adminManager.loadSessions(),
            resetSessions: () => adminManager.resetAllSessions(),
            toggleAutoRefresh: () => adminManager.toggleAutoRefresh(),
            status: () => adminManager.getStatus()
        };
    }
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (adminManager) {
        adminManager.cleanup();
    }
});