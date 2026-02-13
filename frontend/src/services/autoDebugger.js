/**
 * Auto-Debugging & Self-Healing System
 * Automatically detects, reports, and recovers from application errors
 */

class AutoDebugger {
  constructor() {
    this.errorLog = [];
    this.maxErrors = 100;
    this.recoveryAttempts = new Map();
    this.maxRecoveryAttempts = 3;
    this.initialized = false;
  }

  init() {
    if (this.initialized) return;
    
    // Global error handler
    window.onerror = (message, source, lineno, colno, error) => {
      this.handleError({
        type: 'runtime',
        message,
        source,
        lineno,
        colno,
        stack: error?.stack,
        timestamp: new Date().toISOString()
      });
      return false; // Don't suppress default handling
    };

    // Unhandled promise rejection handler
    window.onunhandledrejection = (event) => {
      this.handleError({
        type: 'promise',
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
        timestamp: new Date().toISOString()
      });
    };

    // Network error interceptor
    this.interceptFetch();
    
    this.initialized = true;
    console.log('[AutoDebugger] Initialized');
  }

  interceptFetch() {
    const originalFetch = window.fetch;
    const self = this;

    window.fetch = async function(...args) {
      const startTime = Date.now();
      const url = typeof args[0] === 'string' ? args[0] : args[0]?.url;
      
      try {
        const response = await originalFetch.apply(this, args);
        
        // Log slow requests
        const duration = Date.now() - startTime;
        if (duration > 5000) {
          self.logWarning({
            type: 'slow_request',
            url,
            duration,
            timestamp: new Date().toISOString()
          });
        }

        // Auto-retry on 5xx errors
        if (response.status >= 500 && self.shouldRetry(url)) {
          console.log(`[AutoDebugger] Retrying failed request: ${url}`);
          await new Promise(r => setTimeout(r, 1000));
          return originalFetch.apply(this, args);
        }

        return response;
      } catch (error) {
        self.handleError({
          type: 'network',
          message: error.message,
          url,
          timestamp: new Date().toISOString()
        });

        // Auto-retry network errors
        if (self.shouldRetry(url)) {
          console.log(`[AutoDebugger] Retrying network error: ${url}`);
          await new Promise(r => setTimeout(r, 2000));
          return originalFetch.apply(this, args);
        }

        throw error;
      }
    };
  }

  shouldRetry(url) {
    const attempts = this.recoveryAttempts.get(url) || 0;
    if (attempts >= this.maxRecoveryAttempts) {
      return false;
    }
    this.recoveryAttempts.set(url, attempts + 1);
    
    // Clear retry count after 60 seconds
    setTimeout(() => this.recoveryAttempts.delete(url), 60000);
    
    return true;
  }

  handleError(error) {
    // Add to log
    this.errorLog.push(error);
    if (this.errorLog.length > this.maxErrors) {
      this.errorLog.shift();
    }

    // Log to console with styling
    console.group(`%c[AutoDebugger] ${error.type} Error`, 'color: #ff4444; font-weight: bold;');
    console.error('Message:', error.message);
    if (error.source) console.error('Source:', error.source);
    if (error.stack) console.error('Stack:', error.stack);
    console.groupEnd();

    // Attempt auto-recovery based on error type
    this.attemptRecovery(error);

    // Report to backend
    this.reportError(error);
  }

  logWarning(warning) {
    console.warn(`[AutoDebugger] ${warning.type}:`, warning);
  }

  attemptRecovery(error) {
    const errorKey = `${error.type}:${error.message}`;
    const attempts = this.recoveryAttempts.get(errorKey) || 0;

    if (attempts >= this.maxRecoveryAttempts) {
      console.log('[AutoDebugger] Max recovery attempts reached for:', errorKey);
      return;
    }

    this.recoveryAttempts.set(errorKey, attempts + 1);

    // Recovery strategies based on error type
    if (error.type === 'network') {
      this.recoverFromNetworkError(error);
    } else if (error.message?.includes('ChunkLoadError') || error.message?.includes('Loading chunk')) {
      this.recoverFromChunkError();
    } else if (error.message?.includes('is not defined')) {
      this.recoverFromUndefinedError(error);
    }
  }

  recoverFromNetworkError(error) {
    console.log('[AutoDebugger] Attempting network recovery...');
    // Clear any cached failed requests
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => {
          if (name.includes('api')) {
            caches.delete(name);
          }
        });
      });
    }
  }

  recoverFromChunkError() {
    console.log('[AutoDebugger] Chunk load error detected, reloading page...');
    // Clear service worker cache and reload
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(registrations => {
        registrations.forEach(reg => reg.unregister());
      });
    }
    // Reload after short delay
    setTimeout(() => window.location.reload(), 1000);
  }

  recoverFromUndefinedError(error) {
    console.log('[AutoDebugger] Undefined reference error detected');
    // This usually requires a page reload to fix module issues
    const shouldReload = this.recoveryAttempts.get('undefined_reload') !== true;
    if (shouldReload) {
      this.recoveryAttempts.set('undefined_reload', true);
      console.log('[AutoDebugger] Scheduling page reload...');
      setTimeout(() => window.location.reload(), 2000);
    }
  }

  async reportError(error) {
    try {
      // Safely get API URL
      let API_URL = '';
      try {
        API_URL = import.meta.env?.REACT_APP_BACKEND_URL || '';
      } catch (e) {
        // import.meta not available
      }
      await fetch(`${API_URL}/api/error-tracking/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...error,
          userAgent: navigator.userAgent,
          url: window.location.href,
          userId: localStorage.getItem('user_id') || 'anonymous'
        })
      }).catch(() => {}); // Silently fail if reporting fails
    } catch (e) {
      // Don't let error reporting cause more errors
    }
  }

  getErrorLog() {
    return [...this.errorLog];
  }

  clearErrorLog() {
    this.errorLog = [];
    this.recoveryAttempts.clear();
  }

  getStats() {
    const errorTypes = {};
    this.errorLog.forEach(e => {
      errorTypes[e.type] = (errorTypes[e.type] || 0) + 1;
    });

    return {
      totalErrors: this.errorLog.length,
      errorTypes,
      lastError: this.errorLog[this.errorLog.length - 1],
      recoveryAttempts: Object.fromEntries(this.recoveryAttempts)
    };
  }
}

// Create singleton instance
const autoDebugger = new AutoDebugger();

// Auto-initialize on import
if (typeof window !== 'undefined') {
  autoDebugger.init();
}

export default autoDebugger;
export { AutoDebugger };
