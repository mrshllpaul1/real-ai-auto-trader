import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import StrategySelector from "./pages/StrategySelector";
import TradingView from "./pages/TradingView";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import AILearning from "./pages/AILearning";
import NewsAndIntelligence from "./pages/NewsAndIntelligence";
import NewsFilters from "./pages/NewsFilters";
import AutoTrading from "./pages/AutoTrading";
import GemScanner from "./pages/GemScanner";
import AutoExecution from "./pages/AutoExecution";
import AdvancedFeatures from "./pages/AdvancedFeatures";
import Guide from "./pages/Guide";
import Setup from "./pages/Setup";
import GrowthDashboard from "./pages/GrowthDashboard";
import TradingJournal from "./pages/TradingJournal";
import DeepLearningAI from "./pages/DeepLearningAI";
import AIChat from "./pages/AIChat";
import EnsembleAI from "./pages/EnsembleAI";
import Sidebar from "./components/Sidebar";
import FloatingAIChat from "./components/FloatingAIChat";
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
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/growth" element={<GrowthDashboard />} />
                <Route path="/journal" element={<TradingJournal />} />
                <Route path="/strategies" element={<StrategySelector />} />
                <Route path="/trading" element={<TradingView />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/learning" element={<AILearning />} />
                <Route path="/deep-learning" element={<DeepLearningAI />} />
                <Route path="/ensemble" element={<EnsembleAI />} />
                <Route path="/ai-chat" element={<AIChat />} />
                <Route path="/news" element={<NewsAndIntelligence />} />
                <Route path="/news-filters" element={<NewsFilters />} />
                <Route path="/auto-trading" element={<AutoTrading />} />
                <Route path="/scanner" element={<GemScanner />} />
                <Route path="/auto-exec" element={<AutoExecution />} />
                <Route path="/advanced" element={<AdvancedFeatures />} />
                <Route path="/guide" element={<Guide />} />
                <Route path="/setup" element={<Setup />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
              {/* Floating AI Chat - hidden on AI Chat page */}
              <Routes>
                <Route path="/ai-chat" element={null} />
                <Route path="*" element={<FloatingAIChat />} />
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
