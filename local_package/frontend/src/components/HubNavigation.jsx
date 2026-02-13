import React, { useEffect, useCallback, useMemo } from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';

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
 * Hook for tab state with URL persistence
 * @param {string[]} tabs - Array of tab values
 * @param {string} defaultTab - Default tab if none in URL
 * @returns {[string, function]} - [activeTab, setActiveTab]
 */
export const useTabState = (tabs, defaultTab) => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Get tab from URL or use default
  const activeTab = useMemo(() => {
    const urlTab = searchParams.get('tab');
    return tabs.includes(urlTab) ? urlTab : defaultTab;
  }, [searchParams, tabs, defaultTab]);
  
  // Update URL when tab changes
  const setActiveTab = useCallback((newTab) => {
    if (newTab === defaultTab) {
      // Remove tab param if it's the default
      searchParams.delete('tab');
    } else {
      searchParams.set('tab', newTab);
    }
    setSearchParams(searchParams, { replace: true });
  }, [searchParams, setSearchParams, defaultTab]);
  
  return [activeTab, setActiveTab];
};

/**
 * Hook for keyboard navigation in tabs
 * @param {string[]} tabs - Array of tab values
 * @param {string} activeTab - Current active tab
 * @param {function} setActiveTab - Function to set active tab
 */
export const useTabKeyboardNav = (tabs, activeTab, setActiveTab) => {
  useEffect(() => {
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
export const KeyboardHint = React.memo(({ show = true }) => {
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
});

KeyboardHint.displayName = 'KeyboardHint';

/**
 * Mobile-optimized scrollable tabs wrapper
 */
export const MobileTabsList = React.memo(({ children, className = '' }) => {
  return (
    <div className={`overflow-x-auto scrollbar-hide -mx-4 px-4 md:mx-0 md:px-0 ${className}`}>
      <div className="inline-flex min-w-full md:flex md:flex-wrap">
        {children}
      </div>
    </div>
  );
});

MobileTabsList.displayName = 'MobileTabsList';

/**
 * Loading skeleton for lazy-loaded tab content
 */
export const TabLoadingSkeleton = React.memo(() => (
  <div className="animate-pulse space-y-4">
    <div className="h-8 bg-slate-800 rounded w-1/3"></div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="h-32 bg-slate-800 rounded"></div>
      <div className="h-32 bg-slate-800 rounded"></div>
      <div className="h-32 bg-slate-800 rounded"></div>
    </div>
    <div className="h-64 bg-slate-800 rounded"></div>
  </div>
));

TabLoadingSkeleton.displayName = 'TabLoadingSkeleton';

/**
 * Wrapper for lazy-loaded tab content with loading state
 */
export const LazyTabContent = ({ children, isActive }) => {
  // Only render content when tab is active (for performance)
  if (!isActive) return null;
  
  return (
    <React.Suspense fallback={<TabLoadingSkeleton />}>
      {children}
    </React.Suspense>
  );
};

export default { 
  Breadcrumb, 
  useTabState, 
  useTabKeyboardNav, 
  KeyboardHint, 
  MobileTabsList,
  TabLoadingSkeleton,
  LazyTabContent
};
