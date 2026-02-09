import React from 'react';
import { AlertTriangle, RefreshCcw, Home, Bug } from 'lucide-react';

/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 * and displays a fallback UI instead of crashing the whole app
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
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
    });

    // Report error to backend monitoring
    this.reportError(error, errorInfo);
  }

  async reportError(error, errorInfo) {
    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 
                         import.meta.env.REACT_APP_BACKEND_URL || 
                         'http://localhost:8001';
      
      await fetch(`${backendUrl}/api/monitoring/errors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error_id: this.state.errorId,
          type: 'frontend_error',
          message: error?.message || 'Unknown error',
          stack: error?.stack || '',
          component_stack: errorInfo?.componentStack || '',
          url: window.location.href,
          user_agent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (e) {
      console.error('Failed to report error:', e);
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          errorInfo: this.state.errorInfo,
          reset: this.handleReset,
        });
      }

      // Default fallback UI
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 shadow-xl border border-gray-700">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-red-500/20 rounded-full">
                <AlertTriangle className="w-12 h-12 text-red-400" />
              </div>
            </div>

            {/* Error Message */}
            <h2 className="text-2xl font-bold text-white text-center mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-400 text-center mb-6">
              {this.props.message || "We encountered an unexpected error. Please try again."}
            </p>

            {/* Error ID */}
            {this.state.errorId && (
              <div className="bg-gray-800/50 rounded-lg p-3 mb-6">
                <p className="text-xs text-gray-500 text-center">
                  Error ID: <code className="text-gray-400">{this.state.errorId}</code>
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <RefreshCcw className="w-4 h-4" />
                Try Again
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                <Home className="w-4 h-4" />
                Go Home
              </button>
            </div>

            {/* Developer Info (only in development) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mt-6 p-4 bg-gray-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Bug className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium text-yellow-500">Debug Info</span>
                </div>
                <p className="text-xs text-red-400 font-mono break-all">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo?.componentStack && (
                  <pre className="mt-2 text-xs text-gray-500 overflow-auto max-h-32">
                    {this.state.errorInfo.componentStack}
                  </pre>
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
