/**
 * Auto-Debugging & Self-Healing System
 * Automatically detects, reports, and recovers from application errors
 * Enhanced with AI-powered error analysis and predictive recovery
 */

class AutoDebugger {
  constructor() {
    this.errorLog = [];
    this.maxErrors = 100;
    this.recoveryAttempts = new Map();
    this.maxRecoveryAttempts = 3;
    this.initialized = false;
    
    // Enhanced features
    this.errorPatterns = new Map();
    this.autoFixSuccess = new Map();
    this.autoFixFailures = new Map();
    this.healthCheckInterval = null;
    this.predictiveMode = true;
    
    // State recovery mechanisms
    this.stateSnapshots = [];
    this.maxSnapshots = 10;
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
    
    // Start periodic health checks
    this.startHealthMonitoring();
    
    // Take initial state snapshot
    this.captureStateSnapshot();
    
    this.initialized = true;
    console.log('[AutoDebugger] Enhanced Auto-Debugger Initialized with AI capabilities');
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

    // Track error patterns
    this.trackErrorPattern(error);

    // Attempt auto-recovery based on error type
    this.attemptRecovery(error);

    // Report to backend with AI analysis
    this.reportErrorWithAnalysis(error);
  }
  
  trackErrorPattern(error) {
    const pattern = `${error.type}:${error.message.substring(0, 50)}`;
    const count = (this.errorPatterns.get(pattern) || 0) + 1;
    this.errorPatterns.set(pattern, count);
    
    // Alert if pattern becomes frequent (5+ occurrences)
    if (count === 5) {
      console.warn(
        `%c[AutoDebugger] Pattern Detected!`,
        'color: #ff9900; font-weight: bold;',
        `Error "${pattern}" occurred ${count} times`
      );
      this.triggerPredictiveFix(pattern);
    }
  }
  
  async triggerPredictiveFix(pattern) {
    if (!this.predictiveMode) return;
    
    console.log('[AutoDebugger] Triggering predictive fix for pattern:', pattern);
    
    // Get AI analysis from backend
    try {
      const BACKEND_URL = import.meta.env?.VITE_BACKEND_URL || window.location.origin;
      const response = await fetch(`${BACKEND_URL}/api/ai-error/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error_type: pattern.split(':')[0],
          message: pattern.split(':')[1],
          context: {
            frequency: this.errorPatterns.get(pattern),
            detected_pattern: true
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('[AutoDebugger] AI Analysis:', result.analysis);
        
        // Apply auto-fix if available
        if (result.analysis?.auto_fix_available) {
          await this.applyAutoFix(pattern, result.analysis);
        }
      }
    } catch (e) {
      console.warn('[AutoDebugger] Could not get AI analysis:', e.message);
    }
  }
  
  async applyAutoFix(pattern, analysis) {
    console.log('[AutoDebugger] Applying auto-fix for:', pattern);
    
    try {
      const BACKEND_URL = import.meta.env?.VITE_BACKEND_URL || window.location.origin;
      const response = await fetch(`${BACKEND_URL}/api/ai-error/auto-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error_type: pattern.split(':')[0],
          message: pattern.split(':')[1],
          context: analysis
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.fixed) {
          this.autoFixSuccess.set(pattern, (this.autoFixSuccess.get(pattern) || 0) + 1);
          console.log('%c[AutoDebugger] ✅ Auto-fix successful!', 'color: #00ff00; font-weight: bold;');
        } else {
          this.autoFixFailures.set(pattern, (this.autoFixFailures.get(pattern) || 0) + 1);
        }
      }
    } catch (e) {
      this.autoFixFailures.set(pattern, (this.autoFixFailures.get(pattern) || 0) + 1);
      console.warn('[AutoDebugger] Auto-fix failed:', e.message);
    }
  }
  
  captureStateSnapshot() {
    try {
      const snapshot = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        localStorage: { ...localStorage },
        sessionStorage: { ...sessionStorage },
        errorCount: this.errorLog.length,
        recoveryAttempts: this.recoveryAttempts.size
      };
      
      this.stateSnapshots.push(snapshot);
      if (this.stateSnapshots.length > this.maxSnapshots) {
        this.stateSnapshots.shift();
      }
    } catch (e) {
      console.warn('[AutoDebugger] Could not capture state snapshot:', e.message);
    }
  }
  
  restorePreviousState(stepsBack = 1) {
    try {
      const snapshot = this.stateSnapshots[this.stateSnapshots.length - stepsBack - 1];
      if (!snapshot) {
        console.warn('[AutoDebugger] No snapshot available to restore');
        return false;
      }
      
      console.log('[AutoDebugger] Restoring state from:', snapshot.timestamp);
      
      // Restore storage (carefully - don't break authentication)
      Object.keys(snapshot.localStorage).forEach(key => {
        if (!key.includes('auth') && !key.includes('token')) {
          localStorage.setItem(key, snapshot.localStorage[key]);
        }
      });
      
      return true;
    } catch (e) {
      console.error('[AutoDebugger] State restoration failed:', e);
      return false;
    }
  }
  
  startHealthMonitoring() {
    // Check health every 5 minutes
    this.healthCheckInterval = setInterval(() => {
      this.performHealthCheck();
    }, 5 * 60 * 1000);
    
    // Initial health check
    this.performHealthCheck();
  }
  
  async performHealthCheck() {
    try {
      const BACKEND_URL = import.meta.env?.VITE_BACKEND_URL || window.location.origin;
      const response = await fetch(`${BACKEND_URL}/api/ai-error/health-report`, {
        method: 'GET',
      });
      
      if (response.ok) {
        const result = await response.json();
        const health = result.report;
        
        if (health.status === 'critical') {
          console.error('%c[AutoDebugger] 🚨 CRITICAL: System health is critical!', 
            'color: #ff0000; font-weight: bold; font-size: 14px;');
          console.log('Health Report:', health);
          
          // Take snapshot before potential issues
          this.captureStateSnapshot();
        } else if (health.status === 'degraded') {
          console.warn('[AutoDebugger] ⚠️ System health is degraded');
        } else {
          console.log('[AutoDebugger] ✅ System health is good');
        }
      }
    } catch (e) {
      console.warn('[AutoDebugger] Health check failed:', e.message);
    }
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
        API_URL = import.meta.env?.VITE_BACKEND_URL || window.location.origin;
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
  
  async reportErrorWithAnalysis(error) {
    // Report to standard error tracking
    await this.reportError(error);
    
    // Also report for AI analysis (non-blocking)
    try {
      const BACKEND_URL = import.meta.env?.VITE_BACKEND_URL || window.location.origin;
      fetch(`${BACKEND_URL}/api/ai-error/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error_type: error.type,
          message: error.message,
          stack_trace: error.stack,
          context: {
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: error.timestamp
          }
        })
      }).catch(() => {}); // Fire and forget
    } catch (e) {
      // Don't block on AI analysis
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
      recoveryAttempts: Object.fromEntries(this.recoveryAttempts),
      errorPatterns: Object.fromEntries(this.errorPatterns),
      autoFixSuccess: Object.fromEntries(this.autoFixSuccess),
      autoFixFailures: Object.fromEntries(this.autoFixFailures),
      stateSnapshots: this.stateSnapshots.length,
      healthMonitoring: this.healthCheckInterval !== null
    };
  }
  
  enablePredictiveMode() {
    this.predictiveMode = true;
    console.log('[AutoDebugger] Predictive mode enabled');
  }
  
  disablePredictiveMode() {
    this.predictiveMode = false;
    console.log('[AutoDebugger] Predictive mode disabled');
  }
  
  destroy() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    this.initialized = false;
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
