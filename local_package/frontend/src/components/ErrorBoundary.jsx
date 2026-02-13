import React from 'react';
import { AlertTriangle, RefreshCcw, Home, Bug, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { reportUICrash, ErrorSeverity, ErrorCategory } from '../services/errorReporting';

/**
 * Enhanced Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 * and displays a fallback UI instead of crashing the whole app
 * Now with automatic error reporting and improved UX
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      copied: false,
      showDetails: false,
      retryCount: 0,
      isReporting: false,
      reportSuccess: false,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      errorId: `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console and optionally to error reporting service
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo,
      isReporting: true,
    });

    // Report error using the centralized error reporting service
    this.reportError(error, errorInfo);
  }

  async reportError(error, errorInfo) {
    try {
      // Use the centralized error reporting service
      const errorId = reportUICrash(
        error,
        errorInfo,
        this.props.componentName || 'Unknown'
      );
      
      // Also send to backend for persistence
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                         import.meta.env.REACT_APP_BACKEND_URL || 
                         window.location.origin;
      
      await fetch(`${backendUrl}/api/monitoring/errors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error_id: this.state.errorId,
          type: 'ui_crash',
          severity: ErrorSeverity.HIGH,
          category: ErrorCategory.UI_CRASH,
          message: error?.message || 'Unknown error',
          stack: error?.stack || '',
          component_stack: errorInfo?.componentStack || '',
          component_name: this.props.componentName || 'Unknown',
          url: window.location.href,
          pathname: window.location.pathname,
          user_agent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          session_id: sessionStorage.getItem('sessionId'),
          user_id: localStorage.getItem('user_id') || 'anonymous',
        }),
      });
      
      this.setState({ isReporting: false, reportSuccess: true });
    } catch (e) {
      console.error('Failed to report error:', e);
      this.setState({ isReporting: false, reportSuccess: false });
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    const newRetryCount = this.state.retryCount + 1;
    
    // If too many retries, suggest refreshing
    if (newRetryCount >= 3) {
      this.setState({
        hasError: true,
        error: new Error('Component failed after multiple retries'),
        retryCount: newRetryCount,
      });
      return;
    }
    
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      copied: false,
      showDetails: false,
      retryCount: newRetryCount,
      reportSuccess: false,
    });
  };

  handleCopyError = async () => {
    const errorDetails = {
      id: this.state.errorId,
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      componentStack: this.state.errorInfo?.componentStack,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };
    
    try {
      await navigator.clipboard.writeText(JSON.stringify(errorDetails, null, 2));
      this.setState({ copied: true });
      setTimeout(() => this.setState({ copied: false }), 2000);
    } catch (e) {
      console.error('Failed to copy error:', e);
    }
  };

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          errorInfo: this.state.errorInfo,
          reset: this.handleReset,
          errorId: this.state.errorId,
        });
      }

      const tooManyRetries = this.state.retryCount >= 3;

      // Default fallback UI with enhanced features
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 shadow-xl border border-gray-700">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-red-500/20 rounded-full animate-pulse">
                <AlertTriangle className="w-12 h-12 text-red-400" />
              </div>
            </div>

            {/* Error Message */}
            <h2 className="text-2xl font-bold text-white text-center mb-2">
              {tooManyRetries ? 'Persistent Error' : 'Something went wrong'}
            </h2>
            <p className="text-gray-400 text-center mb-4">
              {tooManyRetries 
                ? "This component keeps failing. Please refresh the page or contact support."
                : (this.props.message || "We encountered an unexpected error. Please try again.")}
            </p>

            {/* Reporting Status */}
            {this.state.isReporting && (
              <div className="flex items-center justify-center gap-2 mb-4 text-sm text-blue-400">
                <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                <span>Reporting error...</span>
              </div>
            )}
            {this.state.reportSuccess && (
              <div className="flex items-center justify-center gap-2 mb-4 text-sm text-green-400">
                <Check className="w-4 h-4" />
                <span>Error reported automatically</span>
              </div>
            )}

            {/* Error ID with Copy Button */}
            {this.state.errorId && (
              <div className="bg-gray-800/50 rounded-lg p-3 mb-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-500">
                    Error ID: <code className="text-gray-400">{this.state.errorId}</code>
                  </p>
                  <button
                    onClick={this.handleCopyError}
                    className="p-1 hover:bg-gray-700 rounded transition-colors"
                    title="Copy error details"
                  >
                    {this.state.copied ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Retry Count */}
            {this.state.retryCount > 0 && (
              <p className="text-xs text-yellow-500 text-center mb-4">
                Retry attempts: {this.state.retryCount}/3
              </p>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 mb-4">
              {!tooManyRetries ? (
                <button
                  onClick={this.handleReset}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <RefreshCcw className="w-4 h-4" />
                  Try Again
                </button>
              ) : (
                <button
                  onClick={this.handleReload}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <RefreshCcw className="w-4 h-4" />
                  Refresh Page
                </button>
              )}
              <button
                onClick={this.handleGoHome}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                <Home className="w-4 h-4" />
                Go Home
              </button>
            </div>

            {/* Expandable Details */}
            <button
              onClick={this.toggleDetails}
              className="w-full flex items-center justify-center gap-2 py-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
            >
              <Bug className="w-4 h-4" />
              <span>Technical Details</span>
              {this.state.showDetails ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {this.state.showDetails && this.state.error && (
              <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <p className="text-xs text-red-400 font-mono break-all mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo?.componentStack && (
                  <details className="mt-2">
                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                      Component Stack
                    </summary>
                    <pre className="mt-2 text-xs text-gray-600 overflow-auto max-h-32 p-2 bg-gray-900 rounded">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Page-level Error Boundary
 * Use this for wrapping entire pages
 */
export const PageErrorBoundary = ({ children }) => (
  <ErrorBoundary message="This page encountered an error. Please try refreshing.">
    {children}
  </ErrorBoundary>
);

/**
 * Component-level Error Boundary
 * Use this for wrapping individual components that might fail
 */
export const ComponentErrorBoundary = ({ children, fallback }) => (
  <ErrorBoundary
    fallback={fallback || (({ reset }) => (
      <div className="p-4 bg-gray-800/50 rounded-lg border border-red-500/20">
        <div className="flex items-center gap-2 text-red-400">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm">Component failed to load</span>
        </div>
        <button
          onClick={reset}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300"
        >
          Try again
        </button>
      </div>
    ))}
  >
    {children}
  </ErrorBoundary>
);

/**
 * Chart Error Boundary
 * Specialized for chart components
 */
export const ChartErrorBoundary = ({ children }) => (
  <ErrorBoundary
    fallback={({ reset }) => (
      <div className="h-full min-h-[200px] flex items-center justify-center bg-gray-800/30 rounded-lg border border-gray-700">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
          <p className="text-sm text-gray-400 mb-2">Chart failed to render</p>
          <button
            onClick={reset}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            Retry
          </button>
        </div>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);

/**
 * Form Error Boundary
 * Specialized for form components
 */
export const FormErrorBoundary = ({ children }) => (
  <ErrorBoundary
    fallback={({ reset }) => (
      <div className="p-6 bg-gray-800/50 rounded-lg border border-red-500/20">
        <div className="flex items-center gap-2 text-red-400 mb-4">
          <AlertTriangle className="w-5 h-5" />
          <span className="font-medium">Form Error</span>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          The form encountered an error. Your data may not have been saved.
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg"
        >
          Reset Form
        </button>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);

export default ErrorBoundary;
