import React, { createContext, useContext, useState, useEffect } from 'react';

// Create context for global trading mode
const TradingModeContext = createContext();

// Storage key constant
const STORAGE_KEY = 'growth_trading_mode';

// Provider component
export const TradingModeProvider = ({ children }) => {
  // Initialize synchronously from localStorage
  const [mode, setMode] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved === 'real' ? 'real' : 'paper';
    } catch {
      return 'paper';
    }
  });

  // Update localStorage whenever mode changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch (e) {
      console.error('Failed to save trading mode:', e);
    }
  }, [mode]);

  // Listen for changes from other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        setMode(e.newValue === 'real' ? 'real' : 'paper');
      }
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

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
