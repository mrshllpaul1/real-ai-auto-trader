import React, { useEffect, lazy, Suspense, useState, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary, { PageErrorBoundary } from "./components/ErrorBoundary";
import { PageLoadingSkeleton } from "./components/LoadingSkeleton";
import KeyboardShortcutsModal from "./components/KeyboardShortcutsModal";

// Hub Pages (lazy loaded with prefetch hints)
const CommandCenter = lazy(() => import(/* webpackPrefetch: true */ "./pages/CommandCenter"));
const TradingHub = lazy(() => import(/* webpackPrefetch: true */ "./pages/TradingHub"));
const AIHub = lazy(() => import(/* webpackPrefetch: true */ "./pages/AIHub"));
const BacktestHub = lazy(() => import("./pages/BacktestHub"));
const NewsHub = lazy(() => import("./pages/NewsHub"));
const ScannerHub = lazy(() => import("./pages/ScannerHub"));
const DeFiHub = lazy(() => import("./pages/DeFiHub"));
const SettingsHub = lazy(() => import("./pages/SettingsHub"));

// New Enhancement Pages (P0, P1, Quick Wins)
const PaperLeaderboard = lazy(() => import("./pages/PaperLeaderboard"));
const StrategyMarketplace = lazy(() => import("./pages/StrategyMarketplace"));
const TaxReporting = lazy(() => import("./pages/TaxReporting"));
const SocialFeed = lazy(() => import("./pages/SocialFeed"));
const Web3Wallet = lazy(() => import("./pages/Web3Wallet"));
const AIExplainability = lazy(() => import("./pages/AIExplainability"));
const ErrorAnalyticsDashboard = lazy(() => import("./pages/ErrorAnalyticsDashboard"));
const PerformanceMonitorDashboard = lazy(() => import("./pages/PerformanceDashboard"));

// Keep individual pages for direct access (backwards compatibility)
import SpotTrading from "./pages/SpotTrading";
import PositionManagement from "./pages/PositionManagement";
import PortfolioDashboard from "./pages/PortfolioDashboard";
import YearlyBacktest from "./pages/YearlyBacktest";
import Analytics from "./pages/Analytics";

import Sidebar from "./components/Sidebar";
import FloatingCommandHub from "./components/FloatingCommandHub";
import TrainingProgress from "./components/TrainingProgress";
import { Toaster } from "./components/ui/sonner";
import { motion } from "framer-motion";
import { TradingModeProvider } from "./context/TradingModeContext";
import { LoadingProvider } from "./context/LoadingContext";

// Prefetch commonly used routes on idle
const prefetchRoutes = () => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      // Prefetch most common pages during idle time
      import("./pages/TradingHub");
      import("./pages/AIHub");
      import("./pages/SettingsHub");
    }, { timeout: 2000 });
  }
};

// Suspense wrapper with optimized loading skeleton
const SuspenseWrapper = ({ children }) => (
  <Suspense fallback={<PageLoadingSkeleton />}>
    {children}
  </Suspense>
);

function App() {
  const [showShortcuts, setShowShortcuts] = useState(false);
  
  useEffect(() => {
    // Initialize auto-debugger
    import('./services/autoDebugger').then(module => {
      module.default.init();
      console.log('[App] AutoDebugger initialized');
    }).catch(err => {
      console.warn('AutoDebugger failed to load:', err);
    });
    
    // Initialize user session
    let uid = localStorage.getItem('user_id');
    if (!uid) {
      uid = 'demo_user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('user_id', uid);
    }

    // Prefetch common routes during idle time
    prefetchRoutes();

    // Register service worker for background execution
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js')
        .then(() => console.log('Service Worker registered'))
        .catch((err) => console.error('Service Worker registration failed:', err));
    }

    // Set viewport meta for mobile
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      viewport.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover');
    }

    // Unlock audio context on first user interaction
    const unlockAudio = () => {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContext.resume();
      document.removeEventListener('click', unlockAudio);
    };
    document.addEventListener('click', unlockAudio);
  }, []);
  
  // Handle keyboard shortcut actions
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setShowShortcuts(true);
      }
      if (e.key === '?' && !e.target.closest('input, textarea')) {
        e.preventDefault();
        setShowShortcuts(true);
      }
      if (e.key === 'Escape') {
        setShowShortcuts(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <TradingModeProvider>
      <LoadingProvider>
        <BrowserRouter>
          <ErrorBoundary>
          <div className="app-root relative">
            {/* Main layout */}
            <div className="flex min-h-screen bg-[#0A0A0A]">
              <Sidebar />
              <main className="flex-1 overflow-auto">
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  className="min-h-screen"
                >
                  <Routes>
                    {/* Main Hub Routes */}
                    <Route path="/" element={<PageErrorBoundary><SuspenseWrapper><CommandCenter /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/trading" element={<PageErrorBoundary><SuspenseWrapper><TradingHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/ai" element={<PageErrorBoundary><SuspenseWrapper><AIHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/backtest" element={<PageErrorBoundary><SuspenseWrapper><BacktestHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/news" element={<PageErrorBoundary><SuspenseWrapper><NewsHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/scanner" element={<PageErrorBoundary><SuspenseWrapper><ScannerHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/defi" element={<PageErrorBoundary><SuspenseWrapper><DeFiHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/settings" element={<PageErrorBoundary><SuspenseWrapper><SettingsHub /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/error-analytics" element={<PageErrorBoundary><SuspenseWrapper><ErrorAnalyticsDashboard /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/performance-monitor" element={<PageErrorBoundary><SuspenseWrapper><PerformanceMonitorDashboard /></SuspenseWrapper></PageErrorBoundary>} />
                    
                    {/* Legacy routes - redirect to hubs */}
                    <Route path="/spot-trading" element={<Navigate to="/trading" replace />} />
                    <Route path="/positions" element={<Navigate to="/trading" replace />} />
                    <Route path="/portfolio-dashboard" element={<Navigate to="/trading" replace />} />
                    <Route path="/advanced-orders" element={<Navigate to="/trading" replace />} />
                    <Route path="/options-trading" element={<Navigate to="/trading" replace />} />
                    <Route path="/perpetuals" element={<Navigate to="/trading" replace />} />
                    <Route path="/market-maker" element={<Navigate to="/trading" replace />} />
                    
                    <Route path="/ai-center" element={<Navigate to="/ai" replace />} />
                    <Route path="/adaptive" element={<Navigate to="/ai" replace />} />
                    <Route path="/auto-trading" element={<Navigate to="/ai" replace />} />
                    <Route path="/auto-exec" element={<Navigate to="/ai" replace />} />
                    <Route path="/ensemble" element={<Navigate to="/ai" replace />} />
                    <Route path="/strategies" element={<Navigate to="/ai" replace />} />
                    <Route path="/learning" element={<Navigate to="/ai" replace />} />
                    <Route path="/learning-loop" element={<Navigate to="/ai" replace />} />
                    <Route path="/ai-teacher" element={<Navigate to="/ai" replace />} />
                    <Route path="/training" element={<Navigate to="/ai" replace />} />
                    <Route path="/model-performance" element={<Navigate to="/ai" replace />} />
                    <Route path="/mtf-predictions" element={<Navigate to="/ai" replace />} />
                    
                    <Route path="/backtest-engine" element={<Navigate to="/backtest" replace />} />
                    <Route path="/yearly-backtest" element={<Navigate to="/backtest" replace />} />
                    <Route path="/gem-backtest" element={<Navigate to="/backtest" replace />} />
                    <Route path="/analytics" element={<Navigate to="/backtest" replace />} />
                    <Route path="/risk-analyzer" element={<Navigate to="/backtest" replace />} />
                    
                    <Route path="/news-sentiment" element={<Navigate to="/news" replace />} />
                    <Route path="/news-intel" element={<Navigate to="/news" replace />} />
                    <Route path="/triggers" element={<Navigate to="/news" replace />} />
                    <Route path="/event-timeline" element={<Navigate to="/news" replace />} />
                    <Route path="/trigger-performance" element={<Navigate to="/news" replace />} />
                    
                    <Route path="/gem-scanner" element={<Navigate to="/scanner" replace />} />
                    <Route path="/gem-ml-dl" element={<Navigate to="/scanner" replace />} />
                    <Route path="/copy-trading" element={<Navigate to="/scanner" replace />} />
                    
                    <Route path="/defi-wallet" element={<Navigate to="/defi" replace />} />
                    <Route path="/yield-farming" element={<Navigate to="/defi" replace />} />
                    <Route path="/rebalance" element={<Navigate to="/defi" replace />} />
                    
                    {/* New Enhancement Routes (P0, P1, Quick Wins) */}
                    <Route path="/leaderboard" element={<PageErrorBoundary><SuspenseWrapper><PaperLeaderboard /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/marketplace" element={<PageErrorBoundary><SuspenseWrapper><StrategyMarketplace /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/tax" element={<PageErrorBoundary><SuspenseWrapper><TaxReporting /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/social" element={<PageErrorBoundary><SuspenseWrapper><SocialFeed /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/web3-wallet" element={<PageErrorBoundary><SuspenseWrapper><Web3Wallet /></SuspenseWrapper></PageErrorBoundary>} />
                    <Route path="/ai-explain" element={<PageErrorBoundary><SuspenseWrapper><AIExplainability /></SuspenseWrapper></PageErrorBoundary>} />
                    
                    <Route path="/setup" element={<Navigate to="/settings" replace />} />
                    <Route path="/budget" element={<Navigate to="/settings" replace />} />
                    <Route path="/telegram" element={<Navigate to="/settings" replace />} />
                    <Route path="/journal" element={<Navigate to="/settings" replace />} />
                    <Route path="/guide" element={<Navigate to="/settings" replace />} />
                    <Route path="/dashboard-settings" element={<Navigate to="/settings" replace />} />
                    
                    {/* Catch-all redirect */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </motion.div>
              </main>
            </div>
            
            {/* Floating components */}
            <FloatingCommandHub />
            <TrainingProgress />
            
            {/* Keyboard Shortcuts Modal */}
            <KeyboardShortcutsModal 
              isOpen={showShortcuts} 
              onClose={() => setShowShortcuts(false)} 
            />
            
            {/* Toast notifications - fixed position with highest z-index */}
            <div className="fixed top-0 right-0 z-[99999] pointer-events-none" style={{ zIndex: 99999 }}>
              <div className="pointer-events-auto">
                <Toaster 
                  position="top-right" 
                  richColors 
                  closeButton 
                  offset="16px"
                  visibleToasts={5}
                  toastOptions={{
                    style: {
                      zIndex: 99999,
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </ErrorBoundary>
        </BrowserRouter>
      </LoadingProvider>
    </TradingModeProvider>
  );
}

export default App;
