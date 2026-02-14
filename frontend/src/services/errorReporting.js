/**
 * Enhanced Error Reporting Service
 * ==================================
 * Auto error correction with smart retry, circuit breaker, and self-healing.
 */

import { toast } from 'sonner';

// Circuit Breaker State
const circuitBreakers = new Map();

class CircuitBreaker {
  constructor(name, options = {}) {
    this.name = name;
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 30000; // 30 seconds
    this.halfOpenRequests = options.halfOpenRequests || 3;
    
    this.failures = 0;
    this.successes = 0;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.lastFailureTime = null;
    this.halfOpenAttempts = 0;
  }

  canExecute() {
    if (this.state === 'CLOSED') return true;
    
    if (this.state === 'OPEN') {
      // Check if we should transition to half-open
      if (Date.now() - this.lastFailureTime > this.resetTimeout) {
        this.state = 'HALF_OPEN';
        this.halfOpenAttempts = 0;
        console.log(`[CircuitBreaker:${this.name}] Transitioning to HALF_OPEN`);
        return true;
      }
      return false;
    }
    
    // HALF_OPEN - allow limited requests
    return this.halfOpenAttempts < this.halfOpenRequests;
  }

  recordSuccess() {
    this.failures = 0;
    this.successes++;
    
    if (this.state === 'HALF_OPEN') {
      this.halfOpenAttempts++;
      if (this.halfOpenAttempts >= this.halfOpenRequests) {
        this.state = 'CLOSED';
        console.log(`[CircuitBreaker:${this.name}] Circuit CLOSED - recovered`);
        toast.success(`Connection to ${this.name} restored`);
      }
    }
  }

  recordFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.state === 'HALF_OPEN') {
      this.state = 'OPEN';
      console.log(`[CircuitBreaker:${this.name}] Circuit re-OPENED from HALF_OPEN`);
      return;
    }
    
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      console.warn(`[CircuitBreaker:${this.name}] Circuit OPENED after ${this.failures} failures`);
      toast.warning(`Service ${this.name} temporarily unavailable. Auto-retry in ${this.resetTimeout/1000}s`);
    }
  }

  getState() {
    return {
      name: this.name,
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      lastFailure: this.lastFailureTime ? new Date(this.lastFailureTime).toISOString() : null,
    };
  }
}

// Get or create circuit breaker for a service
export const getCircuitBreaker = (serviceName) => {
  if (!circuitBreakers.has(serviceName)) {
    circuitBreakers.set(serviceName, new CircuitBreaker(serviceName));
  }
  return circuitBreakers.get(serviceName);
};

// Error Classification
export const classifyError = (error) => {
  const status = error?.response?.status;
  const message = error?.message?.toLowerCase() || '';
  
  if (!error.response) {
    if (message.includes('network') || message.includes('timeout')) {
      return { type: 'NETWORK', retryable: true, severity: 'warning' };
    }
    return { type: 'NETWORK', retryable: true, severity: 'error' };
  }
  
  switch (status) {
    case 400:
      return { type: 'VALIDATION', retryable: false, severity: 'warning' };
    case 401:
    case 403:
      return { type: 'AUTH', retryable: false, severity: 'error' };
    case 404:
      return { type: 'NOT_FOUND', retryable: false, severity: 'info' };
    case 408:
    case 504:
      return { type: 'TIMEOUT', retryable: true, severity: 'warning' };
    case 429:
      return { type: 'RATE_LIMIT', retryable: true, severity: 'warning' };
    case 500:
    case 502:
    case 503:
      return { type: 'SERVER', retryable: true, severity: 'error' };
    default:
      return { type: 'UNKNOWN', retryable: true, severity: 'error' };
  }
};

// Smart Error Messages
const ERROR_MESSAGES = {
  NETWORK: {
    title: 'Connection Issue',
    message: 'Unable to connect to the server. Please check your internet connection.',
    action: 'Retrying automatically...'
  },
  TIMEOUT: {
    title: 'Request Timeout',
    message: 'The server is taking too long to respond.',
    action: 'We\'ll try again shortly.'
  },
  RATE_LIMIT: {
    title: 'Too Many Requests',
    message: 'Please slow down. Too many requests sent.',
    action: 'Waiting before retry...'
  },
  SERVER: {
    title: 'Server Error',
    message: 'Something went wrong on our end.',
    action: 'Our team has been notified.'
  },
  AUTH: {
    title: 'Authentication Required',
    message: 'Please check your API credentials.',
    action: 'Go to Settings to update credentials.'
  },
  VALIDATION: {
    title: 'Invalid Request',
    message: 'Please check your input and try again.',
    action: null
  },
  NOT_FOUND: {
    title: 'Not Found',
    message: 'The requested resource was not found.',
    action: null
  },
  UNKNOWN: {
    title: 'Unexpected Error',
    message: 'An unexpected error occurred.',
    action: 'Please try again later.'
  }
};

// Error Statistics
const errorStats = {
  total: 0,
  byType: {},
  byEndpoint: {},
  lastErrors: [],
  maxHistory: 50,
};

// Report API Error
export const reportApiError = (error, endpoint, retryCount = 0) => {
  const classification = classifyError(error);
  const errorInfo = ERROR_MESSAGES[classification.type];
  
  // Update statistics
  errorStats.total++;
  errorStats.byType[classification.type] = (errorStats.byType[classification.type] || 0) + 1;
  errorStats.byEndpoint[endpoint] = (errorStats.byEndpoint[endpoint] || 0) + 1;
  
  // Add to history
  errorStats.lastErrors.unshift({
    timestamp: new Date().toISOString(),
    endpoint,
    type: classification.type,
    status: error?.response?.status,
    message: error?.message,
    retryCount,
  });
  
  if (errorStats.lastErrors.length > errorStats.maxHistory) {
    errorStats.lastErrors = errorStats.lastErrors.slice(0, errorStats.maxHistory);
  }
  
  // Update circuit breaker
  const serviceName = getServiceName(endpoint);
  const breaker = getCircuitBreaker(serviceName);
  breaker.recordFailure();
  
  // Show user-friendly toast (but not for every retry)
  if (retryCount === 0 || !classification.retryable) {
    const description = errorInfo.action 
      ? `${errorInfo.message} ${errorInfo.action}`
      : errorInfo.message;
    
    if (classification.severity === 'error') {
      toast.error(errorInfo.title, { description });
    } else if (classification.severity === 'warning') {
      toast.warning(errorInfo.title, { description });
    }
  }
  
  // Log for debugging
  console.error(`[API Error] ${endpoint}:`, {
    type: classification.type,
    status: error?.response?.status,
    retryCount,
    message: error?.message,
  });
};

// Report Success (for circuit breaker recovery)
export const reportApiSuccess = (endpoint) => {
  const serviceName = getServiceName(endpoint);
  const breaker = getCircuitBreaker(serviceName);
  breaker.recordSuccess();
};

// Get service name from endpoint
const getServiceName = (endpoint) => {
  if (!endpoint) return 'unknown';
  const parts = endpoint.split('/');
  // Return first meaningful segment (e.g., /api/kraken/status -> kraken)
  for (const part of parts) {
    if (part && part !== 'api') return part;
  }
  return 'default';
};

// Check if endpoint should be attempted
export const canAttemptRequest = (endpoint) => {
  const serviceName = getServiceName(endpoint);
  const breaker = getCircuitBreaker(serviceName);
  return breaker.canExecute();
};

// Get error statistics
export const getErrorStats = () => ({
  ...errorStats,
  circuitBreakers: Array.from(circuitBreakers.values()).map(cb => cb.getState()),
});

// Clear error statistics
export const clearErrorStats = () => {
  errorStats.total = 0;
  errorStats.byType = {};
  errorStats.byEndpoint = {};
  errorStats.lastErrors = [];
};

// Self-healing: Auto-clear old errors
setInterval(() => {
  const oneHourAgo = new Date(Date.now() - 3600000).toISOString();
  errorStats.lastErrors = errorStats.lastErrors.filter(
    e => e.timestamp > oneHourAgo
  );
}, 300000); // Clean up every 5 minutes

export default {
  reportApiError,
  reportApiSuccess,
  classifyError,
  getCircuitBreaker,
  canAttemptRequest,
  getErrorStats,
  clearErrorStats,
};
