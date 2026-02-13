/**
 * Error Reporting Service
 * Centralized error tracking, reporting, and analytics
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

// Error queue for batch reporting
let errorQueue = [];
let flushTimer = null;
const FLUSH_INTERVAL = 5000; // 5 seconds
const MAX_QUEUE_SIZE = 10;

// Error severity levels
export const ErrorSeverity = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical',
};

// Error categories
export const ErrorCategory = {
  UI_CRASH: 'ui_crash',
  API_ERROR: 'api_error',
  NETWORK_ERROR: 'network_error',
  VALIDATION_ERROR: 'validation_error',
  AUTH_ERROR: 'auth_error',
  DATA_ERROR: 'data_error',
  UNKNOWN: 'unknown',
};

/**
 * Generate unique error ID
 */
const generateErrorId = () => {
  return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Get browser and device info
 */
const getDeviceInfo = () => {
  return {
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    viewportWidth: window.innerWidth,
    viewportHeight: window.innerHeight,
    online: navigator.onLine,
    memory: navigator.deviceMemory || 'unknown',
  };
};

/**
 * Get current app state for context
 */
const getAppContext = () => {
  return {
    url: window.location.href,
    pathname: window.location.pathname,
    search: window.location.search,
    referrer: document.referrer,
    timestamp: new Date().toISOString(),
    sessionId: sessionStorage.getItem('sessionId') || 'unknown',
    userId: localStorage.getItem('user_id') || 'anonymous',
  };
};

/**
 * Determine error severity based on error type and context
 */
const determineSeverity = (error, category) => {
  if (category === ErrorCategory.UI_CRASH) return ErrorSeverity.HIGH;
  if (category === ErrorCategory.AUTH_ERROR) return ErrorSeverity.MEDIUM;
  if (category === ErrorCategory.NETWORK_ERROR) return ErrorSeverity.LOW;
  if (error?.message?.includes('ChunkLoadError')) return ErrorSeverity.MEDIUM;
  if (error?.status === 500) return ErrorSeverity.HIGH;
  if (error?.status === 503) return ErrorSeverity.HIGH;
  return ErrorSeverity.MEDIUM;
};

/**
 * Categorize error based on its properties
 */
const categorizeError = (error) => {
  if (!error) return ErrorCategory.UNKNOWN;
  
  const message = error.message?.toLowerCase() || '';
  const name = error.name?.toLowerCase() || '';
  
  if (message.includes('network') || message.includes('fetch') || name === 'networkerror') {
    return ErrorCategory.NETWORK_ERROR;
  }
  if (message.includes('401') || message.includes('unauthorized') || message.includes('authentication')) {
    return ErrorCategory.AUTH_ERROR;
  }
  if (message.includes('validation') || message.includes('invalid')) {
    return ErrorCategory.VALIDATION_ERROR;
  }
  if (error.response?.status >= 400 && error.response?.status < 500) {
    return ErrorCategory.API_ERROR;
  }
  if (error.response?.status >= 500) {
    return ErrorCategory.API_ERROR;
  }
  if (error.componentStack) {
    return ErrorCategory.UI_CRASH;
  }
  
  return ErrorCategory.UNKNOWN;
};

/**
 * Format error for reporting
 */
const formatError = (error, additionalContext = {}) => {
  const category = categorizeError(error);
  
  return {
    id: generateErrorId(),
    category,
    severity: determineSeverity(error, category),
    message: error?.message || 'Unknown error',
    name: error?.name || 'Error',
    stack: error?.stack || '',
    componentStack: error?.componentStack || '',
    response: error?.response ? {
      status: error.response.status,
      statusText: error.response.statusText,
      data: error.response.data,
    } : null,
    request: error?.config ? {
      url: error.config.url,
      method: error.config.method,
      params: error.config.params,
    } : null,
    device: getDeviceInfo(),
    context: {
      ...getAppContext(),
      ...additionalContext,
    },
    fingerprint: generateFingerprint(error),
  };
};

/**
 * Generate error fingerprint for deduplication
 */
const generateFingerprint = (error) => {
  const parts = [
    error?.name || 'Error',
    error?.message?.substring(0, 100) || '',
    window.location.pathname,
  ];
  return parts.join('|').replace(/\d+/g, 'X'); // Replace numbers for better grouping
};

/**
 * Send error to backend
 */
const sendToBackend = async (errors) => {
  try {
    await fetch(`${API}/monitoring/errors/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ errors }),
    });
  } catch (e) {
    // Silently fail - don't cause more errors
    console.warn('[ErrorReporting] Failed to send errors:', e.message);
  }
};

/**
 * Flush error queue to backend
 */
const flushQueue = async () => {
  if (errorQueue.length === 0) return;
  
  const errors = [...errorQueue];
  errorQueue = [];
  
  await sendToBackend(errors);
};

/**
 * Schedule queue flush
 */
const scheduleFlush = () => {
  if (flushTimer) return;
  
  flushTimer = setTimeout(() => {
    flushTimer = null;
    flushQueue();
  }, FLUSH_INTERVAL);
};

/**
 * Report an error
 * @param {Error} error - The error object
 * @param {Object} context - Additional context
 */
export const reportError = (error, context = {}) => {
  const formattedError = formatError(error, context);
  
  // Log to console in development
  if (import.meta.env.DEV) {
    console.group(`🚨 Error Reported: ${formattedError.id}`);
    console.error('Error:', error);
    console.log('Category:', formattedError.category);
    console.log('Severity:', formattedError.severity);
    console.log('Context:', formattedError.context);
    console.groupEnd();
  }
  
  // Add to queue
  errorQueue.push(formattedError);
  
  // Flush immediately for critical errors
  if (formattedError.severity === ErrorSeverity.CRITICAL || 
      formattedError.severity === ErrorSeverity.HIGH) {
    flushQueue();
  } else if (errorQueue.length >= MAX_QUEUE_SIZE) {
    flushQueue();
  } else {
    scheduleFlush();
  }
  
  return formattedError.id;
};

/**
 * Report API error with retry info
 */
export const reportApiError = (error, endpoint, retryCount = 0) => {
  return reportError(error, {
    type: 'api_error',
    endpoint,
    retryCount,
    httpStatus: error?.response?.status,
  });
};

/**
 * Report UI crash from Error Boundary
 */
export const reportUICrash = (error, errorInfo, componentName = 'Unknown') => {
  return reportError(
    { ...error, componentStack: errorInfo?.componentStack },
    {
      type: 'ui_crash',
      componentName,
      componentStack: errorInfo?.componentStack,
    }
  );
};

/**
 * Create a wrapped function that reports errors
 */
export const withErrorReporting = (fn, context = {}) => {
  return async (...args) => {
    try {
      return await fn(...args);
    } catch (error) {
      reportError(error, context);
      throw error;
    }
  };
};

/**
 * Track user action for error context
 */
let lastUserAction = null;
export const trackUserAction = (action, details = {}) => {
  lastUserAction = {
    action,
    details,
    timestamp: new Date().toISOString(),
  };
};

/**
 * Get last user action for error context
 */
export const getLastUserAction = () => lastUserAction;

// Flush queue before page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    if (errorQueue.length > 0) {
      // Use sendBeacon for reliability on page close
      const data = JSON.stringify({ errors: errorQueue });
      navigator.sendBeacon?.(`${API}/monitoring/errors/batch`, data);
    }
  });
  
  // Track unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    reportError(event.reason, { type: 'unhandled_promise_rejection' });
  });
  
  // Generate session ID if not exists
  if (!sessionStorage.getItem('sessionId')) {
    sessionStorage.setItem('sessionId', `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  }
}

export default {
  reportError,
  reportApiError,
  reportUICrash,
  withErrorReporting,
  trackUserAction,
  ErrorSeverity,
  ErrorCategory,
};
