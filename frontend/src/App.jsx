import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ErrorBoundary, { PageErrorBoundary } from "./components/ErrorBoundary";
import StrategySelector from "./pages/StrategySelector";
import TradingView from "./pages/TradingView";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import AILearning from "./pages/AILearning";
import AILearningLoop from "./pages/AILearningLoop";
import NewsAndIntelligence from "./pages/NewsAndIntelligence";
import NewsFilters from "./pages/NewsFilters";
import CopyTrading from './pages/CopyTrading';
import MarketMaker from './pages/MarketMaker';
import DashboardCustomization from './pages/DashboardCustomization';
import OptionsTrading from './pages/OptionsTrading';
import BacktestEngine from './pages/BacktestEngine';
import AdvancedOrders from './pages/AdvancedOrders';
import DeFiWallet from './pages/DeFiWallet';
import YieldFarming from './pages/YieldFarming';
import PerpetualFutures from './pages/PerpetualFutures';
import NewsSentiment from './pages/NewsSentiment';
import RiskAnalyzer from './pages/RiskAnalyzer';
import TelegramNotifications from './pages/TelegramNotifications';
import PortfolioRebalance from './pages/PortfolioRebalance';
import AutoTrading from "./pages/AutoTrading";
import GemScanner from "./pages/GemScanner";
import AutoExecution from "./pages/AutoExecution";
import AdvancedFeatures from "./pages/AdvancedFeatures";
import AdvancedAI from "./pages/AdvancedAI";
import Guide from "./pages/Guide";
import Setup from "./pages/Setup";
import TradingJournal from "./pages/TradingJournal";
import AIChat from "./pages/AIChat";
import AITeacher from "./pages/AITeacher";
import EnsembleAI from "./pages/EnsembleAI";
import EventTriggers from "./pages/EventTriggers";
import GemBacktester from "./pages/GemBacktester";
import EventTimeline from "./pages/EventTimeline";
import TradingBudget from "./pages/TradingBudget";
import TriggerPerformance from "./pages/TriggerPerformance";
import AdaptiveStrategy from "./pages/AdaptiveStrategy";
import PositionManagement from "./pages/PositionManagement";
import GemMLDLComparison from "./pages/GemMLDLComparison";
import PortfolioDashboard from "./pages/PortfolioDashboard";
import StrategyBuilder from "./pages/StrategyBuilder";
import SpotTrading from "./pages/SpotTrading";
import ModelPerformanceDashboard from "./pages/ModelPerformanceDashboard";
import TethysDashboard from "./pages/TethysDashboard";
import CommandCenter from "./pages/CommandCenter";
import AICommandCenter from "./pages/AICommandCenter";
import EnhancedMTFPredictions from "./pages/EnhancedMTFPredictions";
import Sidebar from "./components/Sidebar";
import FloatingCommandHub from "./components/FloatingCommandHub";
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
  }, []);

  return (
    <ErrorBoundary>
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
                <PageErrorBoundary>
                  <Routes>
                    <Route path="/" element={<CommandCenter />} />
                    <Route path="/command" element={<CommandCenter />} />
                    <Route path="/ai-center" element={<AICommandCenter />} />
                    <Route path="/growth" element={<CommandCenter />} />
                    <Route path="/master" element={<CommandCenter />} />
                    <Route path="/upgrades" element={<CommandCenter />} />
                    <Route path="/enhanced-ai" element={<AICommandCenter />} />
                    <Route path="/tethys" element={<AICommandCenter />} />
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
                    <Route path="/ai-teacher" element={<AITeacher />} />
                    <Route path="/news" element={<NewsAndIntelligence />} />
                    <Route path="/news-filters" element={<NewsFilters />} />
                    <Route path="/copy-trading" element={<CopyTrading />} />
                    <Route path="/market-maker" element={<MarketMaker />} />
                    <Route path="/dashboard-settings" element={<DashboardCustomization />} />
                    <Route path="/options-trading" element={<OptionsTrading />} />
                    <Route path="/backtest-engine" element={<BacktestEngine />} />
                    <Route path="/advanced-orders" element={<AdvancedOrders />} />
                    <Route path="/defi-wallet" element={<DeFiWallet />} />
                    <Route path="/yield-farming" element={<YieldFarming />} />
                    <Route path="/perpetuals" element={<PerpetualFutures />} />
                    <Route path="/news-sentiment" element={<NewsSentiment />} />
                    <Route path="/risk-analyzer" element={<RiskAnalyzer />} />
                    <Route path="/telegram" element={<TelegramNotifications />} />
                    <Route path="/rebalance" element={<PortfolioRebalance />} />
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
                    <Route path="/strategy-builder" element={<StrategyBuilder />} />
                    <Route path="/training" element={<TethysDashboard />} />
                    <Route path="/spot-trading" element={<SpotTrading />} />
                    <Route path="/spot" element={<SpotTrading />} />
                    <Route path="/models" element={<ModelPerformanceDashboard />} />
                    <Route path="/model-performance" element={<ModelPerformanceDashboard />} />
                    <Route path="/mtf-predictions" element={<EnhancedMTFPredictions />} />
                    <Route path="/advanced-ai" element={<AdvancedAI />} />
                    <Route path="/guide" element={<Guide />} />
                    <Route path="/setup" element={<Setup />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </PageErrorBoundary>
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
    </ErrorBoundary>
  );
}

export default App;
