import { toast as sonnerToast } from 'sonner';

/**
 * Enhanced toast notification system
 * Provides consistent, beautiful notifications throughout the app
 */

export const toast = {
  success: (message, options = {}) => {
    sonnerToast.success(message, {
      duration: 4000,
      ...options,
    });
  },

  error: (message, options = {}) => {
    sonnerToast.error(message, {
      duration: 5000,
      ...options,
    });
  },

  loading: (message, options = {}) => {
    return sonnerToast.loading(message, {
      duration: Infinity,
      ...options,
    });
  },

  info: (message, options = {}) => {
    sonnerToast.info(message, {
      duration: 4000,
      ...options,
    });
  },

  warning: (message, options = {}) => {
    sonnerToast.warning(message, {
      duration: 5000,
      ...options,
    });
  },

  promise: (promise, messages) => {
    return sonnerToast.promise(promise, {
      loading: messages.loading || 'Loading...',
      success: messages.success || 'Success!',
      error: messages.error || 'Something went wrong',
    });
  },

  // Custom toast for trading operations
  trade: {
    executed: (symbol, action, amount) => {
      sonnerToast.success(`Trade executed: ${action} ${amount} ${symbol}`, {
        duration: 5000,
        action: {
          label: 'View',
          onClick: () => window.location.href = '/journal',
        },
      });
    },

    failed: (symbol, action, reason) => {
      sonnerToast.error(`Trade failed: ${action} ${symbol}`, {
        description: reason,
        duration: 6000,
      });
    },

    pending: (symbol, action) => {
      return sonnerToast.loading(`Executing ${action} order for ${symbol}...`);
    },
  },

  // Custom toast for AI operations
  ai: {
    started: (modelName) => {
      sonnerToast.success(`${modelName} started successfully`, {
        description: 'AI engine is now active',
        duration: 4000,
      });
    },

    stopped: (modelName) => {
      sonnerToast.info(`${modelName} stopped`, {
        description: 'AI engine is now inactive',
        duration: 3000,
      });
    },

    training: (modelName) => {
      return sonnerToast.loading(`Training ${modelName}...`, {
        description: 'This may take a few minutes',
      });
    },

    trained: (modelName, accuracy) => {
      sonnerToast.success(`${modelName} training complete!`, {
        description: `Accuracy: ${accuracy}%`,
        duration: 5000,
      });
    },
  },

  // Custom toast for triggers
  trigger: {
    created: (triggerName) => {
      sonnerToast.success('Trigger created', {
        description: triggerName,
        duration: 4000,
      });
    },

    executed: (triggerName, action) => {
      sonnerToast.info(`Trigger fired: ${triggerName}`, {
        description: `Action: ${action}`,
        duration: 5000,
        action: {
          label: 'View Details',
          onClick: () => window.location.href = '/triggers',
        },
      });
    },

    deleted: (triggerName) => {
      sonnerToast.success('Trigger deleted', {
        description: triggerName,
        duration: 3000,
      });
    },
  },

  // Custom toast for portfolio updates
  portfolio: {
    updated: () => {
      sonnerToast.success('Portfolio refreshed', {
        duration: 2000,
      });
    },

    synced: (exchange) => {
      sonnerToast.success(`${exchange} portfolio synced`, {
        duration: 3000,
      });
    },
  },

  // Dismiss specific toast
  dismiss: (toastId) => {
    sonnerToast.dismiss(toastId);
  },

  // Dismiss all toasts
  dismissAll: () => {
    sonnerToast.dismiss();
  },
};

export default toast;
