import React from 'react';
import { X, Keyboard } from 'lucide-react';
import { SHORTCUTS } from '../hooks/useKeyboardShortcuts';

const KeyboardShortcutsModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <Keyboard className="w-5 h-5 text-blue-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {/* Navigation */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
              Navigation
            </h3>
            <div className="grid gap-2">
              {SHORTCUTS.navigation.map((shortcut, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-2 rounded-lg bg-gray-800/50"
                >
                  <span className="text-gray-300">{shortcut.description}</span>
                  <kbd className="px-2 py-1 text-xs font-mono bg-gray-700 text-gray-300 rounded border border-gray-600">
                    {shortcut.keys}
                  </kbd>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
              Actions
            </h3>
            <div className="grid gap-2">
              {SHORTCUTS.actions.map((shortcut, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-2 rounded-lg bg-gray-800/50"
                >
                  <span className="text-gray-300">{shortcut.description}</span>
                  <kbd className="px-2 py-1 text-xs font-mono bg-gray-700 text-gray-300 rounded border border-gray-600">
                    {shortcut.keys}
                  </kbd>
                </div>
              ))}
            </div>
          </div>

          {/* Tip */}
          <div className="mt-6 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <p className="text-sm text-blue-300">
              <span className="font-medium">Pro tip:</span> Press{' '}
              <kbd className="px-1.5 py-0.5 text-xs font-mono bg-blue-500/20 rounded">?</kbd>
              {' '}anytime to show this menu.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcutsModal;
