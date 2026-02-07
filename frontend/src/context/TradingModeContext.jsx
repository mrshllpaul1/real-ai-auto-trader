import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

// Create context for global trading mode
const TradingModeContext = createContext();

// Storage key constant
const STORAGE_KEY = 'growth_trading_mode';

// Helper to safely read from localStorage
const readFromStorage = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    console.log('[TradingMode] Read from localStorage:', saved);
    return saved;
  } catch (e) {
    console.error('[TradingMode] Error reading localStorage:', e);
    return null;
  }
};

// Helper to safely write to localStorage
const writeToStorage = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value);
    console.log('[TradingMode] Saved to localStorage:', value);
    return true;
  } catch (e) {
    console.error('[TradingMode] Error writing localStorage:', e);
    return false;
  }
};

// Provider component
export const TradingModeProvider = ({ children }) => {
  // Initialize synchronously from localStorage
  const [mode, setModeState] = useState(() => {
    const saved = readFromStorage();
    const initialMode = saved === 'real' ? 'real' : 'paper';
    console.log('[TradingMode] Initial mode:', initialMode);
    return initialMode;
  });

  // Custom setMode that ALWAYS saves to localStorage
  const setMode = useCallback((newMode) => {
    const finalMode = typeof newMode === 'function' ? newMode(mode) : newMode;
    console.log('[TradingMode] Setting mode to:', finalMode);
    writeToStorage(finalMode);
    setModeState(finalMode);
  }, [mode]);

  // Update localStorage whenever mode changes (backup save)
  useEffect(() => {
    writeToStorage(mode);
  }, [mode]);

  // Listen for changes from other tabs/windows AND verify on focus
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        console.log('[TradingMode] Storage event, new value:', e.newValue);
        setModeState(e.newValue === 'real' ? 'real' : 'paper');
      }
    };
    
    // Also sync on window focus (handles mobile app resume)
    const handleFocus = () => {
      const saved = readFromStorage();
      if (saved && saved !== mode) {
        console.log('[TradingMode] Focus sync, updating to:', saved);
        setModeState(saved === 'real' ? 'real' : 'paper');
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('focus', handleFocus);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [mode]);

  const value = {
    mode,
    setMode,
    isRealMode: mode === 'real',
    isPaperMode: mode === 'paper',
    toggleMode: () => setMode(prev => prev === 'real' ? 'paper' : 'real'),
    setRealMode: () => setMode('real'),
    setPaperMode: () => setMode('paper'),
  };

  return (
    <TradingModeContext.Provider value={value}>
      {children}
    </TradingModeContext.Provider>
  );
};

// Custom hook to use trading mode
export const useTradingMode = () => {
  const context = useContext(TradingModeContext);
  if (!context) {
    throw new Error('useTradingMode must be used within a TradingModeProvider');
  }
  return context;
};

export default TradingModeContext;
