/**
 * Code-Split App Component with Lazy Loading
 * Optimized version that loads routes on-demand
 */

import React, { useEffect, lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary, { PageErrorBoundary } from "./components/ErrorBoundary";

// Core components - loaded immediately
import Sidebar from "./components/Sidebar";
import FloatingCommandHub from "./components/FloatingCommandHub";
import TrainingProgress from "./components/TrainingProgress";
import { Toaster } from "./components/ui/sonner";
import { motion } from "framer-motion";
import { TradingModeProvider } from "./context/TradingModeContext";

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen bg-[#0A0A0A]">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#00FF94] mx-auto mb-4"></div>
      <p className="text-gray-400">Loading...</p>
    </div>
  </div>
);

// Lazy-load Hub Pages (loaded on-demand)
const CommandCenter = lazy(() => import("./pages/CommandCenter"));
const TradingHub = lazy(() => import("./pages/TradingHub"));
const AIHub = lazy(() => import("./pages/AIHub"));
const BacktestHub = lazy(() => import("./pages/BacktestHub"));
const NewsHub = lazy(() => import("./pages/NewsHub"));
const ScannerHub = lazy(() => import("./pages/ScannerHub"));
const DeFiHub = lazy(() => import("./pages/DeFiHub"));
const SettingsHub = lazy(() => import("./pages/SettingsHub"));

// Lazy-load individual pages (for backwards compatibility)
const SpotTrading = lazy(() => import("./pages/SpotTrading"));
const PositionManagement = lazy(() => import("./pages/PositionManagement"));
const PortfolioDashboard = lazy(() => import("./pages/PortfolioDashboard"));
const YearlyBacktest = lazy(() => import("./pages/YearlyBacktest"));
const Analytics = lazy(() => import("./pages/Analytics"));

function App() {
  useEffect(() => {
    // Initialize user session
    let uid = localStorage.getItem('user_id');
    if (!uid) {
      uid = 'demo_user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('user_id', uid);
    }

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

    // Preload critical routes after initial render
    setTimeout(() => {
      // Preload most commonly used routes
      import("./pages/TradingHub");
      import("./pages/AIHub");
    }, 2000);
  }, []);

  return (
    <TradingModeProvider>
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
                  <Suspense fallback={<PageLoader />}>
                    <Routes>
                      {/* Main Hub Routes - Lazy Loaded */}
                      <Route path="/" element={<PageErrorBoundary><CommandCenter /></PageErrorBoundary>} />
                      <Route path="/trading" element={<PageErrorBoundary><TradingHub /></PageErrorBoundary>} />
                      <Route path="/ai" element={<PageErrorBoundary><AIHub /></PageErrorBoundary>} />
                      <Route path="/backtest" element={<PageErrorBoundary><BacktestHub /></PageErrorBoundary>} />
                      <Route path="/news" element={<PageErrorBoundary><NewsHub /></PageErrorBoundary>} />
                      <Route path="/scanner" element={<PageErrorBoundary><ScannerHub /></PageErrorBoundary>} />
                      <Route path="/defi" element={<PageErrorBoundary><DeFiHub /></PageErrorBoundary>} />
                      <Route path="/settings" element={<PageErrorBoundary><SettingsHub /></PageErrorBoundary>} />
                      
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
                      
                      {/* Individual pages (if needed) */}
                      <Route path="/spot" element={<PageErrorBoundary><SpotTrading /></PageErrorBoundary>} />
                      <Route path="/portfolio" element={<PageErrorBoundary><PortfolioDashboard /></PageErrorBoundary>} />
                      <Route path="/analytics" element={<PageErrorBoundary><Analytics /></PageErrorBoundary>} />
                      
                      {/* Catch-all redirect to home */}
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </Suspense>
                </motion.div>
              </main>
            </div>

            {/* Global components */}
            <FloatingCommandHub />
            <TrainingProgress />
            <Toaster 
              position="top-right" 
              toastOptions={{
                className: 'toast-custom',
                duration: 4000,
              }}
            />
          </div>
        </ErrorBoundary>
      </BrowserRouter>
    </TradingModeProvider>
  );
}

export default App;
