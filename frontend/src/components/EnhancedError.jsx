/**
 * Enhanced Error Display Component
 * Shows user-friendly error messages with actionable suggestions
 */

import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { 
  AlertCircle, 
  WifiOff, 
  Key, 
  Database, 
  TrendingDown,
  Info,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

/**
 * Error types with specific handling
 */
const ERROR_TYPES = {
  NETWORK: 'network',
  AUTH: 'auth',
  API_KEY: 'api_key',
  RATE_LIMIT: 'rate_limit',
  DATABASE: 'database',
  VALIDATION: 'validation',
  INSUFFICIENT_FUNDS: 'insufficient_funds',
  MARKET_CLOSED: 'market_closed',
  UNKNOWN: 'unknown'
};

/**
 * Parse error and determine type
 */
const parseError = (error) => {
  const errorMessage = error?.message || error?.detail || error?.toString() || 'Unknown error';
  const statusCode = error?.status || error?.response?.status;

  // Network errors
  if (!navigator.onLine || errorMessage.includes('Network Error') || errorMessage.includes('Failed to fetch')) {
    return { type: ERROR_TYPES.NETWORK, message: 'Network connection lost' };
  }

  // Authentication errors
  if (statusCode === 401 || statusCode === 403) {
    return { type: ERROR_TYPES.AUTH, message: 'Authentication failed' };
  }

  // API Key errors
  if (errorMessage.includes('API key') || errorMessage.includes('Invalid credentials')) {
    return { type: ERROR_TYPES.API_KEY, message: 'Invalid API credentials' };
  }

  // Rate limiting
  if (statusCode === 429 || errorMessage.includes('rate limit')) {
    return { type: ERROR_TYPES.RATE_LIMIT, message: 'Rate limit exceeded' };
  }

  // Database errors
  if (errorMessage.includes('database') || errorMessage.includes('MongoDB')) {
    return { type: ERROR_TYPES.DATABASE, message: 'Database error occurred' };
  }

  // Validation errors
  if (statusCode === 400 || errorMessage.includes('validation')) {
    return { type: ERROR_TYPES.VALIDATION, message: 'Invalid input data' };
  }

  // Insufficient funds
  if (errorMessage.includes('insufficient') || errorMessage.includes('not enough balance')) {
    return { type: ERROR_TYPES.INSUFFICIENT_FUNDS, message: 'Insufficient funds' };
  }

  // Market closed
  if (errorMessage.includes('market closed')) {
    return { type: ERROR_TYPES.MARKET_CLOSED, message: 'Market is currently closed' };
  }

  return { type: ERROR_TYPES.UNKNOWN, message: errorMessage };
};

/**
 * Get error configuration (icon, title, suggestions)
 */
const getErrorConfig = (errorType, errorMessage) => {
  const configs = {
    [ERROR_TYPES.NETWORK]: {
      icon: WifiOff,
      title: 'Connection Lost',
      description: 'Unable to connect to the server',
      suggestions: [
        'Check your internet connection',
        'Try refreshing the page',
        'Check if the server is running'
      ],
      actions: [
        { label: 'Retry', action: 'retry', variant: 'default' }
      ]
    },
    [ERROR_TYPES.AUTH]: {
      icon: Key,
      title: 'Authentication Error',
      description: 'Your session may have expired',
      suggestions: [
        'Try logging in again',
        'Check if your session is still valid',
        'Clear browser cache and cookies'
      ],
      actions: [
        { label: 'Go to Settings', action: 'settings', variant: 'default' }
      ]
    },
    [ERROR_TYPES.API_KEY]: {
      icon: Key,
      title: 'Invalid API Credentials',
      description: 'Your API keys are not configured or invalid',
      suggestions: [
        'Go to Settings → API Credentials',
        'Enter valid Kraken API credentials',
        'Ensure API keys have correct permissions'
      ],
      actions: [
        { label: 'Configure API Keys', action: 'api-settings', variant: 'default' },
        { label: 'Help', action: 'help', variant: 'outline' }
      ]
    },
    [ERROR_TYPES.RATE_LIMIT]: {
      icon: TrendingDown,
      title: 'Rate Limit Exceeded',
      description: 'Too many requests in a short time',
      suggestions: [
        'Wait a few minutes before trying again',
        'Consider upgrading to Pro tier for higher limits',
        'Reduce request frequency'
      ],
      actions: [
        { label: 'View Limits', action: 'rate-limits', variant: 'outline' }
      ]
    },
    [ERROR_TYPES.DATABASE]: {
      icon: Database,
      title: 'Database Error',
      description: 'Unable to access or save data',
      suggestions: [
        'This is likely a temporary issue',
        'Try again in a few moments',
        'Contact support if the problem persists'
      ],
      actions: [
        { label: 'Retry', action: 'retry', variant: 'default' },
        { label: 'Contact Support', action: 'support', variant: 'outline' }
      ]
    },
    [ERROR_TYPES.VALIDATION]: {
      icon: AlertCircle,
      title: 'Invalid Input',
      description: errorMessage || 'Please check your input',
      suggestions: [
        'Review the form fields',
        'Ensure all required fields are filled',
        'Check for any validation errors'
      ],
      actions: []
    },
    [ERROR_TYPES.INSUFFICIENT_FUNDS]: {
      icon: TrendingDown,
      title: 'Insufficient Funds',
      description: 'Not enough balance to execute trade',
      suggestions: [
        'Check your available balance',
        'Reduce trade size',
        'Add more funds to your account'
      ],
      actions: [
        { label: 'View Portfolio', action: 'portfolio', variant: 'default' }
      ]
    },
    [ERROR_TYPES.MARKET_CLOSED]: {
      icon: Info,
      title: 'Market Closed',
      description: 'Trading is not available at this time',
      suggestions: [
        'Wait for market to open',
        'Check market hours',
        'Use paper trading mode to practice'
      ],
      actions: []
    },
    [ERROR_TYPES.UNKNOWN]: {
      icon: AlertCircle,
      title: 'Error Occurred',
      description: errorMessage || 'An unexpected error occurred',
      suggestions: [
        'Try refreshing the page',
        'Check browser console for details',
        'Contact support if the issue persists'
      ],
      actions: [
        { label: 'Retry', action: 'retry', variant: 'default' },
        { label: 'Report Issue', action: 'report', variant: 'outline' }
      ]
    }
  };

  return configs[errorType] || configs[ERROR_TYPES.UNKNOWN];
};

/**
 * Enhanced Error Display Component
 */
export const EnhancedError = ({ 
  error, 
  onRetry, 
  onAction,
  className = '' 
}) => {
  const { type, message } = parseError(error);
  const config = getErrorConfig(type, message);
  const Icon = config.icon;

  const handleAction = (action) => {
    if (action === 'retry' && onRetry) {
      onRetry();
    } else if (action === 'settings') {
      window.location.href = '/settings';
    } else if (action === 'api-settings') {
      window.location.href = '/settings?tab=api';
    } else if (action === 'portfolio') {
      window.location.href = '/portfolio';
    } else if (action === 'help') {
      window.open('https://docs.yourapp.com/api-setup', '_blank');
    } else if (action === 'support') {
      window.open('mailto:support@emergentagent.com', '_blank');
    } else if (onAction) {
      onAction(action);
    }
  };

  return (
    <Alert variant="destructive" className={className}>
      <Icon className="h-4 w-4" />
      <AlertTitle>{config.title}</AlertTitle>
      <AlertDescription>
        <div className="space-y-3 mt-2">
          <p className="text-sm">{config.description}</p>
          
          {config.suggestions.length > 0 && (
            <div className="space-y-1">
              <p className="text-sm font-medium">What you can do:</p>
              <ul className="list-disc list-inside space-y-1 text-sm opacity-90">
                {config.suggestions.map((suggestion, idx) => (
                  <li key={idx}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
          
          {config.actions.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {config.actions.map((action, idx) => (
                <Button
                  key={idx}
                  variant={action.variant}
                  size="sm"
                  onClick={() => handleAction(action.action)}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          )}
          
          {/* Error ID for support (if available) */}
          {error?.error_id && (
            <p className="text-xs opacity-70 mt-2">
              Error ID: {error.error_id}
            </p>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};

/**
 * Simple error display for inline use
 */
export const SimpleError = ({ error, className = '' }) => {
  const { message } = parseError(error);
  
  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
};

/**
 * Hook for error handling with toast notifications
 */
export const useErrorHandler = () => {
  const handleError = (error, options = {}) => {
    const { 
      showToast = true, 
      logToConsole = true,
      onRetry 
    } = options;

    const { type, message } = parseError(error);

    if (logToConsole) {
      console.error('[Error Handler]', { type, message, error });
    }

    if (showToast) {
      // Assuming toast is available globally
      if (typeof window !== 'undefined' && window.toast) {
        window.toast.error(message);
      }
    }

    return { type, message, canRetry: !!onRetry };
  };

  return { handleError };
};

export default EnhancedError;
