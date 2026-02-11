/**
 * Keyboard Shortcuts Configuration
 * Global keyboard shortcuts for common trading actions
 * 
 * Usage:
 * import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
 * 
 * function MyComponent() {
 *   useKeyboardShortcuts();
 *   return <div>...</div>;
 * }
 */

export const KEYBOARD_SHORTCUTS = {
  // Navigation
  DASHBOARD: { key: 'd', ctrl: true, description: 'Go to Dashboard' },
  STRATEGIES: { key: 's', ctrl: true, description: 'Go to AI Strategies' },
  PORTFOLIO: { key: 'p', ctrl: true, description: 'Go to Portfolio' },
  TRADING: { key: 't', ctrl: true, description: 'Go to Trading' },
  SETTINGS: { key: ',', ctrl: true, description: 'Go to Settings' },
  
  // Actions
  QUICK_BUY: { key: 'b', ctrl: true, shift: true, description: 'Quick Buy' },
  QUICK_SELL: { key: 's', ctrl: true, shift: true, description: 'Quick Sell' },
  REFRESH: { key: 'r', ctrl: true, description: 'Refresh Data' },
  SEARCH: { key: 'k', ctrl: true, description: 'Open Search' },
  COMMAND_PALETTE: { key: 'p', ctrl: true, shift: true, description: 'Command Palette' },
  
  // AI & Training
  START_TETHYS: { key: 'a', ctrl: true, shift: true, description: 'Start/Stop Tethys' },
  TRAIN_MODEL: { key: 't', ctrl: true, shift: true, description: 'Train AI Model' },
  
  // Display
  TOGGLE_THEME: { key: 'd', ctrl: true, shift: true, description: 'Toggle Dark/Light Mode' },
  TOGGLE_SIDEBAR: { key: 'b', ctrl: true, description: 'Toggle Sidebar' },
  FOCUS_MODE: { key: 'f', ctrl: true, description: 'Toggle Focus Mode' },
  
  // Help
  HELP: { key: '?', description: 'Show Keyboard Shortcuts' },
  ESCAPE: { key: 'Escape', description: 'Close Modals/Dialogs' }
};

/**
 * Format shortcut for display
 * @param {Object} shortcut - Shortcut configuration
 * @returns {string} Formatted shortcut string
 */
export function formatShortcut(shortcut) {
  const parts = [];
  
  if (shortcut.ctrl) parts.push('Ctrl');
  if (shortcut.shift) parts.push('Shift');
  if (shortcut.alt) parts.push('Alt');
  if (shortcut.meta) parts.push('⌘');
  
  // Capitalize single keys
  const key = shortcut.key === '?' ? '?' : 
              shortcut.key === 'Escape' ? 'Esc' : 
              shortcut.key.toUpperCase();
  parts.push(key);
  
  return parts.join(' + ');
}

/**
 * Check if event matches shortcut
 * @param {KeyboardEvent} event 
 * @param {Object} shortcut 
 * @returns {boolean}
 */
export function matchesShortcut(event, shortcut) {
  const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
  const ctrlMatch = !shortcut.ctrl || (event.ctrlKey || event.metaKey);
  const shiftMatch = !shortcut.shift || event.shiftKey;
  const altMatch = !shortcut.alt || event.altKey;
  
  return keyMatch && ctrlMatch && shiftMatch && altMatch;
}

/**
 * Get shortcut by action name
 * @param {string} action - Action name (e.g., 'DASHBOARD')
 * @returns {Object|null}
 */
export function getShortcut(action) {
  return KEYBOARD_SHORTCUTS[action] || null;
}

/**
 * Get all shortcuts grouped by category
 * @returns {Object}
 */
export function getShortcutsByCategory() {
  return {
    'Navigation': [
      { action: 'DASHBOARD', ...KEYBOARD_SHORTCUTS.DASHBOARD },
      { action: 'STRATEGIES', ...KEYBOARD_SHORTCUTS.STRATEGIES },
      { action: 'PORTFOLIO', ...KEYBOARD_SHORTCUTS.PORTFOLIO },
      { action: 'TRADING', ...KEYBOARD_SHORTCUTS.TRADING },
      { action: 'SETTINGS', ...KEYBOARD_SHORTCUTS.SETTINGS }
    ],
    'Actions': [
      { action: 'QUICK_BUY', ...KEYBOARD_SHORTCUTS.QUICK_BUY },
      { action: 'QUICK_SELL', ...KEYBOARD_SHORTCUTS.QUICK_SELL },
      { action: 'REFRESH', ...KEYBOARD_SHORTCUTS.REFRESH },
      { action: 'SEARCH', ...KEYBOARD_SHORTCUTS.SEARCH },
      { action: 'COMMAND_PALETTE', ...KEYBOARD_SHORTCUTS.COMMAND_PALETTE }
    ],
    'AI & Training': [
      { action: 'START_TETHYS', ...KEYBOARD_SHORTCUTS.START_TETHYS },
      { action: 'TRAIN_MODEL', ...KEYBOARD_SHORTCUTS.TRAIN_MODEL }
    ],
    'Display': [
      { action: 'TOGGLE_THEME', ...KEYBOARD_SHORTCUTS.TOGGLE_THEME },
      { action: 'TOGGLE_SIDEBAR', ...KEYBOARD_SHORTCUTS.TOGGLE_SIDEBAR },
      { action: 'FOCUS_MODE', ...KEYBOARD_SHORTCUTS.FOCUS_MODE }
    ],
    'Help': [
      { action: 'HELP', ...KEYBOARD_SHORTCUTS.HELP },
      { action: 'ESCAPE', ...KEYBOARD_SHORTCUTS.ESCAPE }
    ]
  };
}

export default KEYBOARD_SHORTCUTS;
