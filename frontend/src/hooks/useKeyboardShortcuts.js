/**
 * Keyboard Shortcuts Hook
 * Custom React hook to handle global keyboard shortcuts
 */

import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { KEYBOARD_SHORTCUTS, matchesShortcut } from '../config/keyboardShortcuts';

export function useKeyboardShortcuts(handlers = {}) {
  const navigate = useNavigate();

  // Create shortcut-to-action mapping for better maintainability
  const shortcutActions = {
    // Navigation shortcuts
    DASHBOARD: () => navigate('/'),
    STRATEGIES: () => navigate('/strategies'),
    PORTFOLIO: () => navigate('/portfolio'),
    TRADING: () => navigate('/trading'),
    SETTINGS: () => navigate('/settings'),
    
    // Action shortcuts - use custom handlers
    QUICK_BUY: () => handlers.onQuickBuy?.(),
    QUICK_SELL: () => handlers.onQuickSell?.(),
    REFRESH: () => handlers.onRefresh?.(),
    SEARCH: () => handlers.onSearch?.(),
    COMMAND_PALETTE: () => handlers.onCommandPalette?.(),
    
    // AI shortcuts
    START_TETHYS: () => handlers.onStartTethys?.(),
    TRAIN_MODEL: () => handlers.onTrainModel?.(),
    
    // Display shortcuts
    TOGGLE_THEME: () => handlers.onToggleTheme?.(),
    TOGGLE_SIDEBAR: () => handlers.onToggleSidebar?.(),
    FOCUS_MODE: () => handlers.onFocusMode?.(),
    
    // Help shortcuts
    HELP: () => handlers.onHelp?.(),
    ESCAPE: () => handlers.onEscape?.()
  };

  const handleKeyPress = useCallback(
    (event) => {
      // Ignore shortcuts when typing in inputs, textareas, or contentEditable
      const target = event.target;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow Escape key even in inputs
        if (event.key !== 'Escape') {
          return;
        }
      }

      // Check all shortcuts and execute matching action
      for (const [actionName, shortcut] of Object.entries(KEYBOARD_SHORTCUTS)) {
        if (matchesShortcut(event, shortcut)) {
          event.preventDefault();
          const action = shortcutActions[actionName];
          if (action) {
            action();
          }
          return;
        }
      }
    },
    [navigate, handlers]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  return null;
}

export default useKeyboardShortcuts;
