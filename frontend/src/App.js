import React, { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import StrategySelector from "./pages/StrategySelector";
import TradingView from "./pages/TradingView";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import AILearning from "./pages/AILearning";
import Sidebar from "./components/Sidebar";
import { Toaster } from "./components/ui/sonner";
import { motion } from "framer-motion";

function App() {
  const [userId, setUserId] = useState('');

  useEffect(() => {
    // Initialize user session
    let uid = localStorage.getItem('user_id');
    if (!uid) {
      uid = 'demo_user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('user_id', uid);
    }
    setUserId(uid);
  }, []);

  return (
    <div className="App noise-bg">
      <BrowserRouter>
        <div className="flex min-h-screen">
          <Sidebar />
          <motion.main 
            className="flex-1 overflow-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/strategies" element={<StrategySelector />} />
              <Route path="/trading" element={<TradingView />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/learning" element={<AILearning />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.main>
        </div>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;