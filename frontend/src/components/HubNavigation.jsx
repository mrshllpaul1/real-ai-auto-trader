import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * Breadcrumb navigation component for hub pages
 */
export const Breadcrumb = ({ items }) => {
  return (
    <nav className="flex items-center gap-2 text-sm mb-4" aria-label="Breadcrumb">
      <Link 
        to="/" 
        className="text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1"
      >
        <Home className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Home</span>
      </Link>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          {item.href ? (
            <Link 
              to={item.href}
              className="text-slate-500 hover:text-slate-300 transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-slate-300 font-medium">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

/**
 * Hook for keyboard navigation in tabs
 * @param {string[]} tabs - Array of tab values
 * @param {string} activeTab - Current active tab
 * @param {function} setActiveTab - Function to set active tab
 */
export const useTabKeyboardNav = (tabs, activeTab, setActiveTab) => {
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      // Only handle if not in an input field
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      const currentIndex = tabs.indexOf(activeTab);
      
      // Number keys 1-9 for direct tab access
      if (e.key >= '1' && e.key <= '9' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const tabIndex = parseInt(e.key) - 1;
        if (tabIndex < tabs.length) {
          e.preventDefault();
          setActiveTab(tabs[tabIndex]);
        }
      }
      
      // Left/Right arrows for tab navigation (with Alt key)
      if (e.altKey && e.key === 'ArrowLeft') {
        e.preventDefault();
        const newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
        setActiveTab(tabs[newIndex]);
      }
      
      if (e.altKey && e.key === 'ArrowRight') {
        e.preventDefault();
        const newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
        setActiveTab(tabs[newIndex]);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tabs, activeTab, setActiveTab]);
};

/**
 * Keyboard shortcut hint component
 */
export const KeyboardHint = ({ show = true }) => {
  if (!show) return null;
  
  return (
    <div className="hidden md:flex items-center gap-3 text-xs text-slate-500">
      <span className="flex items-center gap-1">
        <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400 font-mono">1-9</kbd>
        <span>tabs</span>
      </span>
      <span className="flex items-center gap-1">
        <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400 font-mono">Alt</kbd>
        <span>+</span>
        <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400 font-mono">←→</kbd>
        <span>navigate</span>
      </span>
    </div>
  );
};

/**
 * Mobile-optimized scrollable tabs wrapper
 */
export const MobileTabsList = ({ children, className = '' }) => {
  return (
    <div className={`overflow-x-auto scrollbar-hide -mx-4 px-4 md:mx-0 md:px-0 ${className}`}>
      <div className="inline-flex min-w-full md:flex md:flex-wrap">
        {children}
      </div>
    </div>
  );
};

export default { Breadcrumb, useTabKeyboardNav, KeyboardHint, MobileTabsList };
