import React, { createContext, useContext, useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';

// Loading Context
const LoadingContext = createContext({
  isLoading: false,
  loadingMessage: '',
  startLoading: () => {},
  stopLoading: () => {},
});

export const useLoading = () => useContext(LoadingContext);

// Loading Provider
export const LoadingProvider = ({ children }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  const startLoading = useCallback((message = 'Loading...') => {
    setLoadingMessage(message);
    setIsLoading(true);
  }, []);

  const stopLoading = useCallback(() => {
    setIsLoading(false);
    setLoadingMessage('');
  }, []);

  return (
    <LoadingContext.Provider value={{ isLoading, loadingMessage, startLoading, stopLoading }}>
      {children}
      {isLoading && <GlobalLoadingIndicator message={loadingMessage} />}
    </LoadingContext.Provider>
  );
};

// Global Loading Indicator (Top bar style)
const GlobalLoadingIndicator = ({ message }) => {
  return (
    <>
      {/* Top loading bar */}
      <div className="fixed top-0 left-0 right-0 z-[99999] h-1 bg-gray-900">
        <div 
          className="h-full bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 animate-pulse"
          style={{
            animation: 'loadingBar 1.5s ease-in-out infinite',
          }}
        />
      </div>
      
      {/* Loading message pill */}
      {message && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-[99999]">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gray-900/90 backdrop-blur-sm border border-gray-700 shadow-xl">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
            <span className="text-sm text-gray-300">{message}</span>
          </div>
        </div>
      )}
      
      {/* Inline styles for animation */}
      <style>{`
        @keyframes loadingBar {
          0% { width: 0%; margin-left: 0; }
          50% { width: 70%; margin-left: 15%; }
          100% { width: 0%; margin-left: 100%; }
        }
      `}</style>
    </>
  );
};

// Hook for component-level loading with automatic state management
export const useAsyncLoading = () => {
  const { startLoading, stopLoading } = useLoading();
  
  const withLoading = useCallback(async (asyncFn, message = 'Loading...') => {
    try {
      startLoading(message);
      const result = await asyncFn();
      return result;
    } finally {
      stopLoading();
    }
  }, [startLoading, stopLoading]);
  
  return { withLoading };
};

export default LoadingProvider;
