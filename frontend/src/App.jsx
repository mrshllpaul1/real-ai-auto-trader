import React, { useEffect, Suspense, lazy } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import FloatingCommandHub from "./components/FloatingCommandHub";
import { Toaster } from "./components/ui/sonner";
import { motion } from "framer-motion";
import { TradingModeProvider } from "./context/TradingModeContext";

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen bg-background">
    <div className="text-center">
      <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      <p className="mt-4 text-muted-foreground">Loading...</p>
    </div>
  </div>
);

// Lazy load pages for code splitting
const UnifiedCommandCenter = lazy(() => import("./pages/UnifiedCommandCenter"));
const TradingView = lazy(() => import("./pages/TradingView"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Settings = lazy(() => import("./pages/Settings"));
const AITraining = lazy(() => import("./pages/AITraining"));
const NewsAndIntelligence = lazy(() => import("./pages/NewsAndIntelligence"));
const NewsFilters = lazy(() => import("./pages/NewsFilters"));
const CopyTrading = lazy(() => import('./pages/CopyTrading'));
const MarketMaker = lazy(() => import('./pages/MarketMaker'));
const DashboardCustomization = lazy(() => import('./pages/DashboardCustomization'));
const OptionsTrading = lazy(() => import('./pages/OptionsTrading'));
const BacktestEngine = lazy(() => import('./pages/BacktestEngine'));
const AutoTrading = lazy(() => import("./pages/AutoTrading"));
const GemScanner = lazy(() => import("./pages/GemScanner"));
const AutoExecution = lazy(() => import("./pages/AutoExecution"));
const AdvancedAI = lazy(() => import("./pages/AdvancedAI"));
const Guide = lazy(() => import("./pages/Guide"));
const Setup = lazy(() => import("./pages/Setup"));
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
const StrategyBuilder = lazy(() => import("./pages/StrategyBuilder"));
const SpotTrading = lazy(() => import("./pages/SpotTrading"));
const ModelPerformanceDashboard = lazy(() => import("./pages/ModelPerformanceDashboard"));


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
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<UnifiedCommandCenter />} />
                  <Route path="/command" element={<UnifiedCommandCenter />} />
                  <Route path="/ai-center" element={<UnifiedCommandCenter />} />
                  <Route path="/growth" element={<UnifiedCommandCenter />} />
                  <Route path="/master" element={<UnifiedCommandCenter />} />
                  <Route path="/upgrades" element={<UnifiedCommandCenter />} />
                  <Route path="/enhanced-ai" element={<UnifiedCommandCenter />} />
                  <Route path="/tethys" element={<UnifiedCommandCenter />} />
                  <Route path="/journal" element={<TradingJournal />} />
                  <Route path="/strategy-builder" element={<StrategyBuilder />} />
                  <Route path="/strategies" element={<StrategyBuilder />} />
                  <Route path="/trading" element={<TradingView />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/learning" element={<AITraining />} />
                  <Route path="/learning-loop" element={<AITraining />} />
                  <Route path="/training" element={<AITraining />} />
                  <Route path="/ensemble" element={<EnsembleAI />} />
                  <Route path="/triggers" element={<EventTriggers />} />
                <Route path="/gem-backtest" element={<GemBacktester />} />
                <Route path="/event-timeline" element={<EventTimeline />} />
                <Route path="/ai-chat" element={<AIChat />} />
                <Route path="/news" element={<NewsAndIntelligence />} />
                <Route path="/news-filters" element={<NewsFilters />} />
                <Route path="/copy-trading" element={<CopyTrading />} />
                <Route path="/market-maker" element={<MarketMaker />} />
                <Route path="/dashboard-settings" element={<DashboardCustomization />} />
                <Route path="/options-trading" element={<OptionsTrading />} />
                <Route path="/backtest-engine" element={<BacktestEngine />} />
                <Route path="/auto-trading" element={<AutoTrading />} />
                <Route path="/scanner" element={<GemScanner />} />
                <Route path="/auto-exec" element={<AutoExecution />} />
                <Route path="/advanced" element={<AdvancedAI />} />
                <Route path="/advanced-ai" element={<AdvancedAI />} />
                <Route path="/budget" element={<TradingBudget />} />
                <Route path="/trigger-performance" element={<TriggerPerformance />} />
                <Route path="/adaptive" element={<AdaptiveStrategy />} />
                <Route path="/positions" element={<PositionManagement />} />
                <Route path="/gem-ml-dl" element={<GemMLDLComparison />} />
                <Route path="/portfolio-dashboard" element={<PortfolioDashboard />} />
                <Route path="/strategy-builder" element={<StrategyBuilder />} />

                <Route path="/spot-trading" element={<SpotTrading />} />
                <Route path="/spot" element={<SpotTrading />} />
                <Route path="/models" element={<ModelPerformanceDashboard />} />
                <Route path="/model-performance" element={<ModelPerformanceDashboard />} />
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
