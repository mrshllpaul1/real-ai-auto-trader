/**
 * Enhanced Error Handling & Reporting
 * =====================================
 * Provides error boundary, error tracking, and user-friendly error displays.
 */

import React, { Component } from 'react';
import { AlertTriangle, RefreshCw, Bug, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '../services/api';

/**
 * Error tracking service
 */
class ErrorTracker {
  static errors = [];
  static maxErrors = 100;

  static track(error, context = {}) {
    const errorRecord = {
      id: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      message: error.message || String(error),
      stack: error.stack,
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        ...context,
      },
      reported: false,
    };

    this.errors.unshift(errorRecord);
    
    // Keep only recent errors
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(0, this.maxErrors);
    }

    // Log to console in development
    console.error('[ErrorTracker]', errorRecord);

    // Report to backend
    this.reportToBackend(errorRecord);

    return errorRecord;
  }

  static async reportToBackend(errorRecord) {
    try {
      await api.post('/monitoring/errors', {
        frontend_error: true,
        ...errorRecord,
      });
      errorRecord.reported = true;
    } catch (e) {
      console.warn('Failed to report error to backend:', e);
    }
  }

  static getRecentErrors(limit = 10) {
    return this.errors.slice(0, limit);
  }

  static clearErrors() {
    this.errors = [];
  }
}

// Global error handler
window.onerror = (message, source, lineno, colno, error) => {
  ErrorTracker.track(error || new Error(message), {
    source,
    lineno,
    colno,
    type: 'uncaught_error',
  });
};

// Unhandled promise rejection handler
window.onunhandledrejection = (event) => {
  ErrorTracker.track(event.reason || new Error('Unhandled Promise Rejection'), {
    type: 'unhandled_rejection',
  });
};

/**
 * User-friendly error display component
 */
export const ErrorDisplay = ({ 
  error, 
  title = 'Something went wrong',
  showDetails = true,
  onRetry = null,
  onDismiss = null,
}) => {
  const [expanded, setExpanded] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const errorMessage = error?.message || String(error);
  const errorId = error?.id || `err_${Date.now()}`;

  const copyErrorInfo = () => {
    const info = `Error ID: ${errorId}\nMessage: ${errorMessage}\nURL: ${window.location.href}\nTime: ${new Date().toISOString()}`;
    navigator.clipboard.writeText(info);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Error info copied to clipboard');
  };

  return (
    <Card className="bg-red-500/10 border-red-500/30">
      <CardHeader className="pb-2">
        <CardTitle className="text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-gray-300">{errorMessage}</p>
        
        <div className="flex flex-wrap gap-2">
          {onRetry && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onRetry}
              className="border-red-500/30 hover:bg-red-500/20"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          )}
          
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={copyErrorInfo}
            className="text-gray-400"
          >
            {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
            {copied ? 'Copied!' : 'Copy Error Info'}
          </Button>

          {showDetails && error?.stack && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setExpanded(!expanded)}
              className="text-gray-400"
            >
              <Bug className="w-4 h-4 mr-2" />
              {expanded ? 'Hide' : 'Show'} Details
              {expanded ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
            </Button>
          )}

          {onDismiss && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onDismiss}
              className="text-gray-400 ml-auto"
            >
              Dismiss
            </Button>
          )}
        </div>

        {expanded && error?.stack && (
          <div className="mt-3 p-3 bg-black/30 rounded-lg overflow-x-auto">
            <pre className="text-xs text-gray-400 whitespace-pre-wrap">
              {error.stack}
            </pre>
          </div>
        )}

        <p className="text-xs text-gray-500">
          Error ID: {errorId}
        </p>
      </CardContent>
    </Card>
  );
};

/**
 * Error Boundary Component
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Track the error
    ErrorTracker.track(error, {
      componentStack: errorInfo.componentStack,
      type: 'react_error_boundary',
    });

    this.setState({ errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleRetry);
      }

      return (
        <div className="min-h-[200px] flex items-center justify-center p-6">
          <ErrorDisplay 
            error={this.state.error}
            title={this.props.errorTitle || 'Component Error'}
            onRetry={this.handleRetry}
          />
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component for error boundary
 */
export const withErrorBoundary = (Component, options = {}) => {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary 
        errorTitle={options.errorTitle}
        fallback={options.fallback}
      >
        <Component {...props} />
      </ErrorBoundary>
    );
  };
};

/**
 * Hook for error handling in functional components
 */
export const useErrorHandler = () => {
  const [error, setError] = React.useState(null);

  const handleError = React.useCallback((err, context = {}) => {
    const tracked = ErrorTracker.track(err, context);
    setError(tracked);
    return tracked;
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const handleAsyncError = React.useCallback((asyncFn) => {
    return async (...args) => {
      try {
        return await asyncFn(...args);
      } catch (err) {
        handleError(err, { async: true });
        throw err;
      }
    };
  }, [handleError]);

  return {
    error,
    handleError,
    clearError,
    handleAsyncError,
    hasError: error !== null,
  };
};

/**
 * API Error Handler with retry logic
 */
export const handleApiError = async (apiCall, options = {}) => {
  const {
    maxRetries = 2,
    retryDelay = 1000,
    onError = null,
    fallbackValue = null,
    showToast = true,
  } = options;

  let lastError = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error;
      
      // Don't retry for certain errors
      const status = error?.response?.status;
      if (status === 401 || status === 403 || status === 404) {
        break;
      }

      // Wait before retrying
      if (attempt < maxRetries) {
        await new Promise(r => setTimeout(r, retryDelay * (attempt + 1)));
      }
    }
  }

  // All retries failed
  ErrorTracker.track(lastError, { apiCall: apiCall.name, retries: maxRetries });
  
  if (showToast) {
    const message = lastError?.response?.data?.detail || lastError?.message || 'Request failed';
    toast.error(message);
  }

  if (onError) {
    onError(lastError);
  }

  return fallbackValue;
};

/**
 * Error statistics component for admin dashboard
 */
export const ErrorStats = () => {
  const [stats, setStats] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/errors/stats');
        setStats(response.data);
      } catch (e) {
        console.error('Failed to fetch error stats:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="animate-pulse bg-gray-800 h-24 rounded-lg" />;
  }

  if (!stats) {
    return null;
  }

  const recoveryRate = stats.recovery?.recovery_rate?.toFixed(1) || 0;
  const totalErrors = stats.recovery?.total_errors || 0;
  const errorsLast24h = stats.database?.errors_last_24h || 0;

  return (
    <Card className="bg-slate-900/50 border-slate-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Bug className="w-4 h-4 text-orange-400" />
          Error Stats
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-white">{totalErrors}</div>
            <div className="text-xs text-gray-400">Total Handled</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{recoveryRate}%</div>
            <div className="text-xs text-gray-400">Recovery Rate</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-400">{errorsLast24h}</div>
            <div className="text-xs text-gray-400">Last 24h</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export { ErrorBoundary, ErrorTracker };
export default ErrorBoundary;
