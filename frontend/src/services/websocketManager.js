/**
 * WebSocket Manager
 * =================
 * Manages WebSocket connections for real-time data updates.
 * Provides automatic reconnection, heartbeat, and event handling.
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong to keep connection alive
 * - Event-based subscription system
 * - Message queuing for offline periods
 * - Connection state management
 * - Integration with BackgroundLoader for fallback polling
 */

class WebSocketManager {
  constructor() {
    this.ws = null;
    this.url = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.heartbeatInterval = 30000; // 30s
    this.heartbeatTimer = null;
    this.reconnectTimer = null;
    
    this.subscriptions = new Map();
    this.messageQueue = [];
    this.maxQueueSize = 100;
    
    this.connectionState = 'DISCONNECTED';
    this.lastConnectedAt = null;
    this.lastMessageAt = null;
    
    this.stats = {
      messagesReceived: 0,
      messagesSent: 0,
      reconnections: 0,
      errors: 0,
    };
    
    this.eventHandlers = {
      onOpen: [],
      onClose: [],
      onError: [],
      onMessage: [],
    };
    
    console.log('[WebSocketManager] Initialized');
  }
  
  /**
   * Connect to WebSocket server
   * @param {string} url - WebSocket URL
   * @param {Object} options - Connection options
   */
  connect(url, options = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WebSocketManager] Already connected');
      return;
    }
    
    this.url = url;
    const protocols = options.protocols || [];
    
    try {
      this.ws = new WebSocket(url, protocols);
      this.connectionState = 'CONNECTING';
      
      this.ws.onopen = this._handleOpen.bind(this);
      this.ws.onclose = this._handleClose.bind(this);
      this.ws.onerror = this._handleError.bind(this);
      this.ws.onmessage = this._handleMessage.bind(this);
      
      console.log('[WebSocketManager] Connecting to:', url);
    } catch (error) {
      console.error('[WebSocketManager] Connection error:', error);
      this._handleError(error);
    }
  }
  
  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.connectionState = 'DISCONNECTED';
    console.log('[WebSocketManager] Disconnected');
  }
  
  /**
   * Send message to server
   * @param {Object|string} data - Data to send
   * @returns {boolean} - Success status
   */
  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      // Queue message for later
      if (this.messageQueue.length < this.maxQueueSize) {
        this.messageQueue.push(data);
        console.log('[WebSocketManager] Message queued (offline)');
      } else {
        console.warn('[WebSocketManager] Message queue full');
      }
      return false;
    }
    
    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.ws.send(message);
      this.stats.messagesSent++;
      return true;
    } catch (error) {
      console.error('[WebSocketManager] Send error:', error);
      this.stats.errors++;
      return false;
    }
  }
  
  /**
   * Subscribe to a data channel
   * @param {string} channel - Channel name
   * @param {Function} callback - Callback for messages
   * @returns {Function} - Unsubscribe function
   */
  subscribe(channel, callback) {
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set());
    }
    
    this.subscriptions.get(channel).add(callback);
    
    // Send subscription message if connected
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send({
        type: 'subscribe',
        channel
      });
    }
    
    console.log(`[WebSocketManager] Subscribed to channel: ${channel}`);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.subscriptions.get(channel);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.subscriptions.delete(channel);
          
          // Send unsubscribe message if connected
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.send({
              type: 'unsubscribe',
              channel
            });
          }
        }
      }
      console.log(`[WebSocketManager] Unsubscribed from channel: ${channel}`);
    };
  }
  
  /**
   * Register event handler
   * @param {string} event - Event name (onOpen, onClose, onError, onMessage)
   * @param {Function} handler - Event handler
   * @returns {Function} - Unregister function
   */
  on(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].push(handler);
      
      return () => {
        const index = this.eventHandlers[event].indexOf(handler);
        if (index > -1) {
          this.eventHandlers[event].splice(index, 1);
        }
      };
    }
    
    console.warn(`[WebSocketManager] Unknown event: ${event}`);
    return () => {};
  }
  
  /**
   * Get connection state
   * @returns {string} - Connection state
   */
  getState() {
    return this.connectionState;
  }
  
  /**
   * Check if connected
   * @returns {boolean} - Connected status
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
  
  /**
   * Get statistics
   * @returns {Object} - Connection statistics
   */
  getStats() {
    return {
      ...this.stats,
      connectionState: this.connectionState,
      reconnectAttempts: this.reconnectAttempts,
      subscriptions: this.subscriptions.size,
      queuedMessages: this.messageQueue.length,
      lastConnectedAt: this.lastConnectedAt,
      lastMessageAt: this.lastMessageAt,
      uptime: this.lastConnectedAt ? Date.now() - this.lastConnectedAt : 0,
    };
  }
  
  // Private methods
  
  _handleOpen(event) {
    console.log('[WebSocketManager] Connected');
    this.connectionState = 'CONNECTED';
    this.lastConnectedAt = Date.now();
    this.reconnectAttempts = 0;
    
    // Start heartbeat
    this._startHeartbeat();
    
    // Resubscribe to all channels
    this.subscriptions.forEach((_, channel) => {
      this.send({
        type: 'subscribe',
        channel
      });
    });
    
    // Send queued messages
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
    
    // Trigger event handlers
    this.eventHandlers.onOpen.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('[WebSocketManager] onOpen handler error:', error);
      }
    });
  }
  
  _handleClose(event) {
    console.log('[WebSocketManager] Disconnected:', event.code, event.reason);
    this.connectionState = 'DISCONNECTED';
    
    // Stop heartbeat
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    // Trigger event handlers
    this.eventHandlers.onClose.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('[WebSocketManager] onClose handler error:', error);
      }
    });
    
    // Attempt reconnection
    if (event.code !== 1000) { // Not a normal closure
      this._scheduleReconnect();
    }
  }
  
  _handleError(event) {
    console.error('[WebSocketManager] Error:', event);
    this.stats.errors++;
    
    // Trigger event handlers
    this.eventHandlers.onError.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('[WebSocketManager] onError handler error:', error);
      }
    });
  }
  
  _handleMessage(event) {
    this.lastMessageAt = Date.now();
    this.stats.messagesReceived++;
    
    try {
      const data = JSON.parse(event.data);
      
      // Handle heartbeat/pong
      if (data.type === 'pong') {
        return;
      }
      
      // Route to channel subscribers
      if (data.channel) {
        const callbacks = this.subscriptions.get(data.channel);
        if (callbacks) {
          callbacks.forEach(callback => {
            try {
              callback(data);
            } catch (error) {
              console.error('[WebSocketManager] Subscriber callback error:', error);
            }
          });
        }
      }
      
      // Trigger general message handlers
      this.eventHandlers.onMessage.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('[WebSocketManager] onMessage handler error:', error);
        }
      });
    } catch (error) {
      console.error('[WebSocketManager] Message parsing error:', error);
    }
  }
  
  _startHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping', timestamp: Date.now() });
      }
    }, this.heartbeatInterval);
  }
  
  _scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocketManager] Max reconnection attempts reached');
      return;
    }
    
    // Exponential backoff with jitter
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts) + Math.random() * 1000,
      this.maxReconnectDelay
    );
    
    this.reconnectAttempts++;
    this.stats.reconnections++;
    
    console.log(
      `[WebSocketManager] Reconnecting in ${(delay / 1000).toFixed(1)}s ` +
      `(attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );
    
    this.reconnectTimer = setTimeout(() => {
      if (this.url) {
        this.connect(this.url);
      }
    }, delay);
  }
}

// Singleton instance
let wsManager = null;

export const getWebSocketManager = () => {
  if (!wsManager) {
    wsManager = new WebSocketManager();
  }
  return wsManager;
};

/**
 * React hook for WebSocket subscription
 * @param {string} channel - Channel to subscribe to
 * @param {Function} onMessage - Message handler
 * @param {Object} options - Hook options
 */
export const useWebSocket = (channel, onMessage, options = {}) => {
  const { enabled = true, autoConnect = true } = options;
  const wsManager = getWebSocketManager();
  
  // Auto-connect if requested
  if (autoConnect && !wsManager.isConnected()) {
    const wsUrl = import.meta.env.VITE_WS_URL || 
                  (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
                  window.location.host + '/ws';
    wsManager.connect(wsUrl);
  }
  
  // Subscribe to channel
  if (enabled && channel && onMessage) {
    const unsubscribe = wsManager.subscribe(channel, onMessage);
    
    // Cleanup on unmount
    return () => {
      unsubscribe();
    };
  }
  
  return wsManager;
};

export default getWebSocketManager;
