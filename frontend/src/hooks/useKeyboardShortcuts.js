import { useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * Keyboard shortcuts for power users
 * 
 * Navigation:
 * - g + h: Go to Home/Command Center
 * - g + t: Go to Trading Hub
 * - g + a: Go to AI Hub
 * - g + b: Go to Backtest Hub
 * - g + s: Go to Settings
 * - g + p: Go to Portfolio
 * 
 * Actions:
 * - Ctrl/Cmd + K: Open search/command palette
 * - Ctrl/Cmd + /: Show keyboard shortcuts
 * - Escape: Close modals/sidebars
 * - r: Refresh current page data
 */

export const SHORTCUTS = {
  navigation: [
    { keys: 'g h', description: 'Go to Command Center', path: '/' },
    { keys: 'g t', description: 'Go to Trading Hub', path: '/trading' },
    { keys: 'g a', description: 'Go to AI Hub', path: '/ai' },
    { keys: 'g b', description: 'Go to Backtest Hub', path: '/backtest' },
    { keys: 'g s', description: 'Go to Settings', path: '/settings' },
    { keys: 'g p', description: 'Go to Portfolio', path: '/portfolio' },
    { keys: 'g m', description: 'Go to Marketplace', path: '/marketplace' },
    { keys: 'g l', description: 'Go to Leaderboard', path: '/leaderboard' },
  ],
  actions: [
    { keys: 'Ctrl+K', description: 'Open Command Palette', action: 'command_palette' },
    { keys: 'Ctrl+/', description: 'Show Shortcuts', action: 'show_shortcuts' },
    { keys: 'Escape', description: 'Close Modal', action: 'close_modal' },
    { keys: 'r', description: 'Refresh Data', action: 'refresh' },
    { keys: 'n', description: 'New Trade', action: 'new_trade' },
  ]
};

export function useKeyboardShortcuts({ onAction, enabled = true }) {
  const navigate = useNavigate();
  const location = useLocation();

  // Track key sequence for multi-key shortcuts
  let keySequence = '';
  let sequenceTimeout = null;

  const handleKeyDown = useCallback((event) => {
    if (!enabled) return;

    // Don't trigger shortcuts when typing in inputs
    const target = event.target;
    const isInput = target.tagName === 'INPUT' || 
                   target.tagName === 'TEXTAREA' || 
                   target.isContentEditable;
    
    if (isInput && event.key !== 'Escape') return;

    const key = event.key.toLowerCase();
    const isCtrlOrCmd = event.ctrlKey || event.metaKey;

    // Handle Ctrl/Cmd shortcuts
    if (isCtrlOrCmd) {
      if (key === 'k') {
        event.preventDefault();
        onAction?.('command_palette');
        return;
      }
      if (key === '/') {
        event.preventDefault();
        onAction?.('show_shortcuts');
        return;
      }
    }

    // Handle Escape
    if (key === 'escape') {
      onAction?.('close_modal');
      return;
    }

    // Handle single-key shortcuts
    if (!isCtrlOrCmd && !event.altKey && !event.shiftKey) {
      // Build key sequence
      keySequence += key;
      
      // Clear sequence after delay
      if (sequenceTimeout) clearTimeout(sequenceTimeout);
      sequenceTimeout = setTimeout(() => {
        keySequence = '';
      }, 500);

      // Check navigation shortcuts (g + letter)
      if (keySequence.startsWith('g')) {
        const shortcut = SHORTCUTS.navigation.find(s => 
          s.keys.replace(' ', '') === keySequence
        );
        if (shortcut) {
          event.preventDefault();
          navigate(shortcut.path);
          keySequence = '';
          return;
        }
      }

      // Single key actions (only if not in sequence)
      if (keySequence.length === 1) {
        if (key === 'r' && !isInput) {
          event.preventDefault();
          onAction?.('refresh');
          return;
        }
        if (key === 'n' && !isInput) {
          event.preventDefault();
          onAction?.('new_trade');
          return;
        }
        if (key === '?' && !isInput) {
          event.preventDefault();
          onAction?.('show_shortcuts');
          return;
        }
      }
    }
  }, [enabled, navigate, onAction]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (sequenceTimeout) clearTimeout(sequenceTimeout);
    };
  }, [handleKeyDown]);

  return { shortcuts: SHORTCUTS };
}

export default useKeyboardShortcuts;
