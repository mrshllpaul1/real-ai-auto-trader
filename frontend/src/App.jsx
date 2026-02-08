import React, { useEffect, lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import FloatingCommandHub from "./components/FloatingCommandHub";
import { Toaster } from "./components/ui/sonner";
import { motion } from "framer-motion";
import { TradingModeProvider } from "./context/TradingModeContext";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const StrategySelector = lazy(() => import("./pages/StrategySelector"));
const TradingView = lazy(() => import("./pages/TradingView"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Settings = lazy(() => import("./pages/Settings"));
const AILearning = lazy(() => import("./pages/AILearning"));
const AILearningLoop = lazy(() => import("./pages/AILearningLoop"));
const NewsAndIntelligence = lazy(() => import("./pages/NewsAndIntelligence"));
const NewsFilters = lazy(() => import("./pages/NewsFilters"));
const AutoTrading = lazy(() => import("./pages/AutoTrading"));
const GemScanner = lazy(() => import("./pages/GemScanner"));
const AutoExecution = lazy(() => import("./pages/AutoExecution"));
const AdvancedFeatures = lazy(() => import("./pages/AdvancedFeatures"));
const Guide = lazy(() => import("./pages/Guide"));
const Setup = lazy(() => import("./pages/Setup"));
const GrowthDashboard = lazy(() => import("./pages/GrowthDashboard"));
const TradingJournal = lazy(() => import("./pages/TradingJournal"));
const AIChat = lazy(() => import("./pages/AIChat"));
const EnsembleAI = lazy(() => import("./pages/EnsembleAI"));
const EventTriggers = lazy(() => import("./pages/EventTriggers"));
const GemBacktester = lazy(() => import("./pages/GemBacktester"));
const EventTimeline = lazy(() => import("./pages/EventTimeline"));
const TradingBudget = lazy(() => import("./pages/TradingBudget"));
const TriggerPerformance = lazy(() => import("./pages/TriggerPerformance"));
const AdaptiveStrategy = lazy(() => import("./pages/AdaptiveStrategy"));
const PositionManagement = lazy(() => import("./pages/PositionManagement"));
const GemMLDLComparison = lazy(() => import("./pages/GemMLDLComparison"));
const PortfolioDashboard = lazy(() => import("./pages/PortfolioDashboard"));
const EnhancedAIDashboard = lazy(() => import("./pages/EnhancedAIDashboard"));
const StrategyBuilder = lazy(() => import("./pages/StrategyBuilder"));
const TrainingDashboard = lazy(() => import("./pages/TrainingDashboard"));
const SpotTrading = lazy(() => import("./pages/SpotTrading"));
const ModelPerformanceDashboard = lazy(() => import("./pages/ModelPerformanceDashboard"));
const TethysDashboard = lazy(() => import("./pages/TethysDashboard"));

const IDLE_CALLBACK_TIMEOUT = 2000;
const SERVICE_WORKER_FALLBACK_DELAY = 1000;

const addLinkIfMissing = (rel, href, crossOrigin = false) => {
  const existing = Array.from(document.head.querySelectorAll('link')).some(
    (link) => link.rel === rel && link.href === href
  );
  if (existing) {
    return;
  }
  const link = document.createElement('link');
  link.rel = rel;
  link.href = href;
  if (crossOrigin) {
    link.crossOrigin = '';
  }
  document.head.appendChild(link);
};

const registerServiceWorker = () => {
  navigator.serviceWorker.register('/service-worker.js')
    .then(() => console.log('Service Worker registered'))
    .catch((err) => console.error('Service Worker registration failed:', err));
};

function App() {
  useEffect(() => {
    // Initialize user session
    let uid = localStorage.getItem('user_id');
    if (!uid) {
      uid = 'demo_user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('user_id', uid);
    }

    const backendUrl = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
    if (backendUrl) {
      try {
        const backendOrigin = new URL(backendUrl).origin;
        addLinkIfMissing('preconnect', backendOrigin, true);
        addLinkIfMissing('dns-prefetch', backendOrigin);
      } catch (error) {
        console.warn('Failed to parse backend URL:', error);
      }
    }

    // Register service worker for background execution
    if ('serviceWorker' in navigator) {
      if ('requestIdleCallback' in window) {
        window.requestIdleCallback(registerServiceWorker, { timeout: IDLE_CALLBACK_TIMEOUT });
      } else {
        setTimeout(registerServiceWorker, SERVICE_WORKER_FALLBACK_DELAY);
      }
    }

    // Set viewport meta for mobile
    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      viewport.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover');
    }
  }, []);

  return (
    <TradingModeProvider>
      <div className="App noise-bg">
        <BrowserRouter>
          <div className="flex min-h-screen min-h-[100dvh]">
            <Sidebar />
            <motion.main 
              className="flex-1 overflow-auto w-full"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="md:hidden h-16" />
              <Suspense
                fallback={
                  <div className="flex items-center justify-center py-24">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-[#00FF94]" />
                  </div>
                }
              >
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/growth" element={<GrowthDashboard />} />
                  <Route path="/journal" element={<TradingJournal />} />
                  <Route path="/strategies" element={<StrategySelector />} />
                  <Route path="/trading" element={<TradingView />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/learning" element={<AILearning />} />
                  <Route path="/learning-loop" element={<AILearningLoop />} />
                  <Route path="/ensemble" element={<EnsembleAI />} />
                  <Route path="/triggers" element={<EventTriggers />} />
                  <Route path="/gem-backtest" element={<GemBacktester />} />
                  <Route path="/event-timeline" element={<EventTimeline />} />
                  <Route path="/ai-chat" element={<AIChat />} />
                  <Route path="/news" element={<NewsAndIntelligence />} />
                  <Route path="/news-filters" element={<NewsFilters />} />
                  <Route path="/auto-trading" element={<AutoTrading />} />
                  <Route path="/scanner" element={<GemScanner />} />
                  <Route path="/auto-exec" element={<AutoExecution />} />
                  <Route path="/advanced" element={<AdvancedFeatures />} />
                  <Route path="/budget" element={<TradingBudget />} />
                  <Route path="/trigger-performance" element={<TriggerPerformance />} />
                  <Route path="/adaptive" element={<AdaptiveStrategy />} />
                  <Route path="/positions" element={<PositionManagement />} />
                  <Route path="/gem-ml-dl" element={<GemMLDLComparison />} />
                  <Route path="/portfolio-dashboard" element={<PortfolioDashboard />} />
                  <Route path="/enhanced-ai" element={<EnhancedAIDashboard />} />
                  <Route path="/strategy-builder" element={<StrategyBuilder />} />
                  <Route path="/training" element={<TrainingDashboard />} />
                  <Route path="/spot" element={<SpotTrading />} />
                  <Route path="/models" element={<ModelPerformanceDashboard />} />
                  <Route path="/tethys" element={<TethysDashboard />} />
                  <Route path="/guide" element={<Guide />} />
                  <Route path="/setup" element={<Setup />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
              {/* Floating Command Hub - hidden on AI Chat page */}
              <Routes>
                <Route path="/ai-chat" element={null} />
                <Route path="*" element={<FloatingCommandHub />} />
              </Routes>
            </motion.main>
          </div>
        </BrowserRouter>
        <Toaster position="top-center" richColors />
      </div>
    </TradingModeProvider>
  );
}

export default App;
