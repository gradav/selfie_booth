/**
 * Real-time Communication Handler for Selfie Booth
 * Manages Server-Sent Events and polling fallback for live updates
 */

class RealtimeManager {
    constructor() {
        this.isConnected = false;
        this.connectionType = null; // 'sse' or 'polling'
        this.tabletId = null;
        this.eventHandlers = new Map();
        this.connectionStatus = 'disconnected';
        this.lastSessionState = null;
        
        // SSE properties
        this.eventSource = null;
        this.retryCount = 0;
        this.maxRetries = APP_CONFIG.REALTIME.MAX_RETRIES;
        this.retryInterval = APP_CONFIG.REALTIME.RETRY_INTERVAL;
        
        // Polling properties
        this.pollingInterval = null;
        this.pollFrequency = APP_CONFIG.REALTIME.POLL_INTERVAL;
        
        // Auto-cleanup on page unload
        window.addEventListener('beforeunload', () => this.disconnect());
    }

    // ============ Connection Management ============

    /**
     * Initialize real-time connection
     */
    async connect(tabletId = null) {
        this.tabletId = tabletId || TABLET_CONFIG.getTabletId();
        
        if (APP_CONFIG.DEBUG) {
            console.log(`🔗 Connecting real-time for tablet: ${this.tabletId}`);
        }

        // Try SSE first, fallback to polling
        if (APP_CONFIG.FEATURES.ENABLE_REALTIME) {
            const sseSuccess = await this.connectSSE();
            if (!sseSuccess) {
                this.connectPolling();
            }
        } else {
            this.connectPolling();
        }
    }

    /**
     * Connect using Server-Sent Events
     */
    async connectSSE() {
        try {
            const url = `${APP_CONFIG.REALTIME.SSE_ENDPOINT}/${this.tabletId}`;
            this.eventSource = new EventSource(url);
            
            this.eventSource.onopen = () => {
                this.isConnected = true;
                this.connectionType = 'sse';
                this.connectionStatus = 'connected';
                this.retryCount = 0;
                
                console.log('✅ SSE connection established');
                this.emit('connected', { type: 'sse' });
            };

            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('❌ Error parsing SSE message:', error);
                }
            };

            this.eventSource.onerror = (error) => {
                console.error('❌ SSE connection error:', error);
                this.connectionStatus = 'error';
                this.isConnected = false;
                
                this.emit('error', { error, type: 'sse' });
                
                // Auto-retry with exponential backoff
                if (this.retryCount < this.maxRetries) {
                    this.retryCount++;
                    const delay = Math.min(
                        this.retryInterval * Math.pow(2, this.retryCount - 1),
                        30000 // Max 30 seconds
                    );
                    
                    console.log(`🔄 Retrying SSE connection in ${delay}ms (attempt ${this.retryCount})`);
                    
                    setTimeout(() => {
                        if (!this.isConnected) {
                            this.connectSSE();
                        }
                    }, delay);
                } else {
                    console.log('❌ Max SSE retries reached, falling back to polling');
                    this.connectPolling();
                }
            };

            return true;
        } catch (error) {
            console.error('❌ Failed to create SSE connection:', error);
            return false;
        }
    }

    /**
     * Connect using polling fallback
     */
    connectPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.connectionType = 'polling';
        this.connectionStatus = 'connected';
        this.isConnected = true;
        
        console.log(`🔄 Started polling every ${this.pollFrequency}ms`);
        this.emit('connected', { type: 'polling' });

        // Start polling
        this.pollingInterval = setInterval(() => {
            this.pollSessionState();
        }, this.pollFrequency);

        // Initial poll
        this.pollSessionState();
    }

    /**
     * Disconnect real-time connection
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }

        this.isConnected = false;
        this.connectionType = null;
        this.connectionStatus = 'disconnected';
        
        console.log('🔌 Real-time connection closed');
        this.emit('disconnected');
    }

    // ============ Message Handling ============

    /**
     * Handle incoming real-time messages
     */
    handleMessage(data) {
        if (APP_CONFIG.DEBUG) {
            console.log('📨 Real-time message received:', data);
        }

        // Update last session state
        if (data.session_state) {
            this.lastSessionState = data.session_state;
        }

        // Emit specific event types
        if (data.type) {
            this.emit(data.type, data);
        }

        // Generic message event
        this.emit('message', data);

        // Handle common message types
        this.handleCommonMessages(data);
    }

    /**
     * Handle common message types
     */
    handleCommonMessages(data) {
        switch (data.type) {
            case 'session_state_change':
                this.handleSessionStateChange(data);
                break;
                
            case 'verification_code':
                this.handleVerificationCode(data);
                break;
                
            case 'photo_ready':
                this.handlePhotoReady(data);
                break;
                
            case 'session_complete':
                this.handleSessionComplete(data);
                break;
        }
    }

    /**
     * Handle session state changes
     */
    handleSessionStateChange(data) {
        const { old_state, new_state, session_data } = data;
        
        console.log(`🔄 Session state changed: ${old_state} → ${new_state}`);
        
        // Emit specific state events
        this.emit(`state_${new_state}`, { ...data, session_data });
        
        // Update UI based on state
        this.updateUIForState(new_state, session_data);
    }

    /**
     * Handle verification code display
     */
    handleVerificationCode(data) {
        const { code, user_name, expires_at } = data;
        console.log(`🔢 Verification code for ${user_name}: ${code}`);
        
        this.emit('show_verification', { code, user_name, expires_at });
    }

    /**
     * Handle photo ready notification
     */
    handlePhotoReady(data) {
        const { session_id, photo_data } = data;
        console.log(`📸 Photo ready for session: ${session_id}`);
        
        this.emit('photo_captured', { session_id, photo_data });
    }

    /**
     * Handle session completion
     */
    handleSessionComplete(data) {
        console.log('✅ Session completed');
        this.emit('session_reset');
    }

    // ============ Polling Implementation ============

    /**
     * Poll for session state changes
     */
    async pollSessionState() {
        try {
            const response = await api.checkSessionState(this.tabletId);
            
            if (response.success) {
                const currentState = response.data.session_state;
                
                // Check if state changed
                if (this.lastSessionState !== null && this.lastSessionState !== currentState) {
                    const stateChangeData = {
                        type: 'session_state_change',
                        old_state: this.lastSessionState,
                        new_state: currentState,
                        session_data: response.data,
                        timestamp: new Date().toISOString()
                    };
                    
                    this.handleMessage(stateChangeData);
                }
                
                this.lastSessionState = currentState;
                
                // Emit periodic update
                this.emit('poll_update', response.data);
                
            } else {
                console.error('❌ Polling error:', response.error);
                this.emit('poll_error', response.error);
            }
        } catch (error) {
            console.error('❌ Polling exception:', error);
            this.emit('poll_error', error);
        }
    }

    // ============ UI State Management ============

    /**
     * Update UI based on session state
     */
    updateUIForState(state, sessionData = null) {
        // This will be implemented by specific page handlers
        // Each page (kiosk, mobile, etc.) can override this behavior
        this.emit('ui_update', { state, sessionData });
    }

    // ============ Event System ============

    /**
     * Add event listener
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Remove all event listeners for an event
     */
    removeAllListeners(event) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.delete(event);
        }
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data = null) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`❌ Error in event handler for '${event}':`, error);
                }
            });
        }
    }

    // ============ Connection Status ============

    /**
     * Get current connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            connectionType: this.connectionType,
            status: this.connectionStatus,
            tabletId: this.tabletId,
            lastSessionState: this.lastSessionState,
            retryCount: this.retryCount
        };
    }

    /**
     * Force reconnection
     */
    reconnect() {
        console.log('🔄 Forcing reconnection...');
        this.disconnect();
        setTimeout(() => {
            this.connect(this.tabletId);
        }, 1000);
    }

    // ============ Utility Methods ============

    /**
     * Send ping (for testing connection)
     */
    async ping() {
        try {
            const response = await api.checkSessionState(this.tabletId);
            return response.success;
        } catch (error) {
            return false;
        }
    }

    /**
     * Get connection latency
     */
    async getLatency() {
        const start = performance.now();
        const success = await this.ping();
        const end = performance.now();
        
        return success ? end - start : -1;
    }
}

// ============ Connection Status UI Helper ============

class ConnectionStatusUI {
    constructor(statusElementId = 'status') {
        this.statusElement = DOMUtils.getElementById(statusElementId);
        this.lastStatus = null;
    }

    /**
     * Update status display
     */
    updateStatus(status, state = null) {
        if (!this.statusElement) return;

        let statusText = 'Unknown';
        let statusClass = '';

        switch (status) {
            case 'connected':
                statusText = state === 'verification' ? 'Verifying' :
                           state === 'camera' ? 'Photo Session' : 'Ready';
                statusClass = state === 'verification' ? 'verifying' :
                            state === 'camera' ? 'camera' : '';
                break;
            case 'error':
                statusText = 'Offline';
                statusClass = 'error';
                break;
            case 'disconnected':
                statusText = 'Disconnected';
                statusClass = 'error';
                break;
        }

        // Remove previous status classes
        this.statusElement.className = this.statusElement.className
            .replace(/\b(verifying|camera|error)\b/g, '');

        // Add new status class
        if (statusClass) {
            DOMUtils.addClass(this.statusElement, statusClass);
        }

        DOMUtils.setText(this.statusElement, statusText);
    }
}

// ============ Initialize and Export ============

// Create global realtime manager instance
const realtimeManager = new RealtimeManager();

// Export to global scope
window.realtimeManager = realtimeManager;
window.ConnectionStatusUI = ConnectionStatusUI;

if (APP_CONFIG.DEBUG) {
    console.log('🔧 Real-time manager initialized');
    
    // Add debug commands to window
    window.realtimeDebug = {
        connect: () => realtimeManager.connect(),
        disconnect: () => realtimeManager.disconnect(),
        reconnect: () => realtimeManager.reconnect(),
        status: () => realtimeManager.getStatus(),
        ping: () => realtimeManager.ping(),
        latency: () => realtimeManager.getLatency()
    };
}