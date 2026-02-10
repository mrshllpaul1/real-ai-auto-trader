/**
 * Keyboard Shortcuts Component
 * Displays available keyboard shortcuts in a modal
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Keyboard, Command } from 'lucide-react';

const KeyboardShortcuts = ({ open, onOpenChange }) => {
  const shortcuts = [
    {
      category: 'Navigation',
      items: [
        { keys: ['Alt', 'D'], description: 'Go to Dashboard' },
        { keys: ['Alt', 'T'], description: 'Go to Trading' },
        { keys: ['Alt', 'P'], description: 'Go to Portfolio' },
        { keys: ['Alt', 'A'], description: 'Go to Analytics' },
        { keys: ['Alt', 'S'], description: 'Go to Settings' },
        { keys: ['Alt', 'H'], description: 'Go to AI Command Center' },
      ]
    },
    {
      category: 'Trading Actions',
      items: [
        { keys: ['Ctrl', 'B'], description: 'Quick Buy' },
        { keys: ['Ctrl', 'S'], description: 'Quick Sell' },
        { keys: ['Ctrl', 'Enter'], description: 'Execute Trade' },
        { keys: ['Esc'], description: 'Cancel/Close Dialog' },
      ]
    },
    {
      category: 'Search & Filters',
      items: [
        { keys: ['Ctrl', 'K'], description: 'Search/Command Palette' },
        { keys: ['Ctrl', 'F'], description: 'Filter Data' },
        { keys: ['/'], description: 'Focus Search' },
      ]
    },
    {
      category: 'View Controls',
      items: [
        { keys: ['Ctrl', 'R'], description: 'Refresh Data' },
        { keys: ['Ctrl', 'E'], description: 'Export Data' },
        { keys: ['Ctrl', 'P'], description: 'Print/Save PDF' },
        { keys: ['?'], description: 'Show This Help' },
      ]
    },
    {
      category: 'AI Features',
      items: [
        { keys: ['Alt', 'G'], description: 'Generate AI Strategy' },
        { keys: ['Alt', 'M'], description: 'Toggle Tethys AI' },
        { keys: ['Alt', 'L'], description: 'View AI Recommendations' },
      ]
    }
  ];

  const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  const formatKey = (key) => {
    if (isMac) {
      const macKeys = {
        'Ctrl': '⌘',
        'Alt': '⌥',
        'Shift': '⇧',
        'Enter': '↵',
        'Esc': '⎋'
      };
      return macKeys[key] || key;
    }
    return key;
  };

  return (
    <div className="space-y-6">
      {shortcuts.map((section, idx) => (
        <div key={idx} className="space-y-3">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            {section.category}
          </h3>
          <div className="space-y-2">
            {section.items.map((shortcut, itemIdx) => (
              <div
                key={itemIdx}
                className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-accent/50 transition-colors"
              >
                <span className="text-sm text-foreground">
                  {shortcut.description}
                </span>
                <div className="flex items-center gap-1">
                  {shortcut.keys.map((key, keyIdx) => (
                    <React.Fragment key={keyIdx}>
                      <kbd className="px-2 py-1 text-xs font-semibold text-foreground bg-muted border border-border rounded shadow-sm">
                        {formatKey(key)}
                      </kbd>
                      {keyIdx < shortcut.keys.length - 1 && (
                        <span className="text-xs text-muted-foreground">+</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Keyboard Shortcuts Dialog Component
 */
export const KeyboardShortcutsDialog = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Keyboard className="h-5 w-5 text-primary" />
            <DialogTitle>Keyboard Shortcuts</DialogTitle>
          </div>
          <DialogDescription>
            Speed up your workflow with these keyboard shortcuts
          </DialogDescription>
        </DialogHeader>
        <KeyboardShortcuts />
      </DialogContent>
    </Dialog>
  );
};

/**
 * Keyboard Shortcuts Button Component
 */
export const KeyboardShortcutsButton = ({ className = '' }) => {
  const [open, setOpen] = useState(false);

  // Listen for '?' key to open shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === '?' && !e.ctrlKey && !e.altKey && !e.metaKey) {
        // Only trigger if not in an input field
        const target = e.target;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA' && !target.isContentEditable) {
          e.preventDefault();
          setOpen(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
        className={className}
        title="Keyboard Shortcuts (Press ?)"
      >
        <Keyboard className="h-4 w-4" />
      </Button>
      <KeyboardShortcutsDialog open={open} onOpenChange={setOpen} />
    </>
  );
};

/**
 * Hook for registering keyboard shortcuts
 */
export const useKeyboardShortcut = (keys, callback, options = {}) => {
  const { enabled = true, preventDefault = true } = options;

  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (e) => {
      const keysPressed = {
        ctrl: e.ctrlKey || e.metaKey,
        alt: e.altKey,
        shift: e.shiftKey,
        key: e.key.toLowerCase()
      };

      const shortcutMatch = keys.every(key => {
        const lowerKey = key.toLowerCase();
        if (lowerKey === 'ctrl') return keysPressed.ctrl;
        if (lowerKey === 'alt') return keysPressed.alt;
        if (lowerKey === 'shift') return keysPressed.shift;
        return keysPressed.key === lowerKey;
      });

      if (shortcutMatch) {
        // Don't trigger shortcuts when typing in input fields
        const target = e.target;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
          return;
        }

        if (preventDefault) {
          e.preventDefault();
        }
        callback(e);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [keys, callback, enabled, preventDefault]);
};

export default KeyboardShortcuts;
