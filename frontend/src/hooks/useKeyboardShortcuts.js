/**
 * Keyboard Shortcuts Hook
 * Custom React hook to handle global keyboard shortcuts
 */

import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { KEYBOARD_SHORTCUTS, matchesShortcut } from '../config/keyboardShortcuts';

export function useKeyboardShortcuts(handlers = {}) {
  const navigate = useNavigate();

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

      // Navigation shortcuts
      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.DASHBOARD)) {
        event.preventDefault();
        navigate('/');
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.STRATEGIES)) {
        event.preventDefault();
        navigate('/strategies');
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.PORTFOLIO)) {
        event.preventDefault();
        navigate('/portfolio');
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.TRADING)) {
        event.preventDefault();
        navigate('/trading');
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.SETTINGS)) {
        event.preventDefault();
        navigate('/settings');
        return;
      }

      // Action shortcuts - check custom handlers
      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.QUICK_BUY)) {
        event.preventDefault();
        handlers.onQuickBuy?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.QUICK_SELL)) {
        event.preventDefault();
        handlers.onQuickSell?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.REFRESH)) {
        event.preventDefault();
        handlers.onRefresh?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.SEARCH)) {
        event.preventDefault();
        handlers.onSearch?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.COMMAND_PALETTE)) {
        event.preventDefault();
        handlers.onCommandPalette?.();
        return;
      }

      // AI shortcuts
      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.START_TETHYS)) {
        event.preventDefault();
        handlers.onStartTethys?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.TRAIN_MODEL)) {
        event.preventDefault();
        handlers.onTrainModel?.();
        return;
      }

      // Display shortcuts
      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.TOGGLE_THEME)) {
        event.preventDefault();
        handlers.onToggleTheme?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.TOGGLE_SIDEBAR)) {
        event.preventDefault();
        handlers.onToggleSidebar?.();
        return;
      }

      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.FOCUS_MODE)) {
        event.preventDefault();
        handlers.onFocusMode?.();
        return;
      }

      // Help
      if (matchesShortcut(event, KEYBOARD_SHORTCUTS.HELP)) {
        event.preventDefault();
        handlers.onHelp?.();
        return;
      }

      // Escape - close modals/dialogs
      if (event.key === 'Escape') {
        handlers.onEscape?.();
        return;
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
