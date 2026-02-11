import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary, { PageErrorBoundary } from "./components/ErrorBoundary";

// Hub Pages (consolidated)
import CommandCenter from "./pages/CommandCenter";
import TradingHub from "./pages/TradingHub";
import AIHub from "./pages/AIHub";
import BacktestHub from "./pages/BacktestHub";
import NewsHub from "./pages/NewsHub";
import ScannerHub from "./pages/ScannerHub";
import DeFiHub from "./pages/DeFiHub";
import SettingsHub from "./pages/SettingsHub";

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
                  <Routes>
                    {/* Main Hub Routes */}
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
            <Toaster position="top-right" richColors closeButton />
          </div>
        </ErrorBoundary>
      </BrowserRouter>
    </TradingModeProvider>
  );
}

export default App;
