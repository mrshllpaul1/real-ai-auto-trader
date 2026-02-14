import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, LayoutDashboard, Wallet, Brain, BarChart3, Newspaper, Radar,
  Sprout, Settings, Bug, Gauge, TrendingUp, Activity, Zap, Bot, Layers,
  Wand2, GraduationCap, Cpu, Target, Shield, PieChart, Award,
  Users, DollarSign, Globe, ArrowRight, Command, X
} from 'lucide-react';

const PAGES = [
  { name: 'Command Center', path: '/', icon: LayoutDashboard, category: 'Navigation', keywords: 'home dashboard overview portfolio' },
  { name: 'Trading Hub', path: '/trading', icon: Wallet, category: 'Trading', keywords: 'spot buy sell trade order' },
  { name: 'AI & Strategy', path: '/ai', icon: Brain, category: 'AI', keywords: 'ai ml model prediction strategy' },
  { name: 'Backtest Engine', path: '/backtest', icon: BarChart3, category: 'Analysis', keywords: 'backtest simulate history test' },
  { name: 'News & Events', path: '/news', icon: Newspaper, category: 'Market', keywords: 'news events triggers sentiment' },
  { name: 'Scanner & Social', path: '/scanner', icon: Radar, category: 'Discovery', keywords: 'scanner gems social copy trading' },
  { name: 'DeFi Hub', path: '/defi', icon: Sprout, category: 'DeFi', keywords: 'defi wallet yield farming' },
  { name: 'Error Analytics', path: '/error-analytics', icon: Bug, category: 'System', keywords: 'errors bugs analytics monitoring' },
  { name: 'Performance Monitor', path: '/performance-monitor', icon: Gauge, category: 'System', keywords: 'performance metrics speed cache' },
  { name: 'Settings & Config', path: '/settings', icon: Settings, category: 'Settings', keywords: 'settings config api keys telegram' },
  { name: 'Paper Leaderboard', path: '/leaderboard', icon: Award, category: 'Social', keywords: 'leaderboard competition ranking' },
  { name: 'Strategy Marketplace', path: '/marketplace', icon: Layers, category: 'Social', keywords: 'marketplace strategy share subscribe' },
  { name: 'Tax Reporting', path: '/tax', icon: DollarSign, category: 'Analysis', keywords: 'tax report gains losses form' },
  { name: 'Social Feed', path: '/social', icon: Users, category: 'Social', keywords: 'social feed trades share follow' },
  { name: 'Web3 Wallet', path: '/web3-wallet', icon: Globe, category: 'DeFi', keywords: 'web3 wallet metamask nft defi' },
  { name: 'AI Explainability', path: '/ai-explain', icon: Cpu, category: 'AI', keywords: 'explain ai why confidence features' },
];

const QUICK_ACTIONS = [
  { name: 'Buy Bitcoin', action: 'navigate', path: '/trading', icon: TrendingUp, category: 'Quick Action', keywords: 'buy btc bitcoin' },
  { name: 'Check AI Signal', action: 'navigate', path: '/ai', icon: Zap, category: 'Quick Action', keywords: 'ai signal check prediction' },
  { name: 'Run Backtest', action: 'navigate', path: '/backtest', icon: Activity, category: 'Quick Action', keywords: 'run backtest simulate' },
  { name: 'View Portfolio', action: 'navigate', path: '/', icon: PieChart, category: 'Quick Action', keywords: 'portfolio holdings balance' },
  { name: 'API Settings', action: 'navigate', path: '/settings', icon: Settings, category: 'Quick Action', keywords: 'api key kraken setup' },
  { name: 'Auto Trading', action: 'navigate', path: '/ai', icon: Bot, category: 'Quick Action', keywords: 'auto trade bot autopilot' },
];

const ALL_ITEMS = [...QUICK_ACTIONS, ...PAGES];

const CommandPalette = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const navigate = useNavigate();

  const filtered = query.trim()
    ? ALL_ITEMS.filter(item => {
        const q = query.toLowerCase();
        return (
          item.name.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q) ||
          item.keywords.toLowerCase().includes(q)
        );
      })
    : ALL_ITEMS;

  const handleSelect = useCallback((item) => {
    onClose();
    setQuery('');
    setSelectedIndex(0);
    if (item.path) {
      navigate(item.path);
    }
  }, [navigate, onClose]);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selected = listRef.current.querySelector(`[data-index="${selectedIndex}"]`);
      if (selected) {
        selected.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, filtered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        handleSelect(filtered[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  }, [filtered, selectedIndex, handleSelect, onClose]);

  // Group items by category
  const grouped = {};
  filtered.forEach((item, idx) => {
    if (!grouped[item.category]) grouped[item.category] = [];
    grouped[item.category].push({ ...item, _idx: idx });
  });

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999]"
            onClick={onClose}
          />

          {/* Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="fixed top-[15%] left-1/2 -translate-x-1/2 w-full max-w-xl z-[10000]"
          >
            <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden">
              {/* Search Input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-700/50">
                <Search className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Search pages, features, and actions..."
                  className="flex-1 bg-transparent text-white text-sm placeholder-slate-500 outline-none"
                />
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <kbd className="px-1.5 py-0.5 text-[10px] bg-slate-800 text-slate-400 rounded border border-slate-700 font-mono">ESC</kbd>
                  <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-lg transition-colors">
                    <X className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              </div>

              {/* Results */}
              <div ref={listRef} className="max-h-80 overflow-y-auto py-2 scrollbar-thin scrollbar-thumb-slate-700">
                {Object.keys(grouped).length === 0 ? (
                  <div className="px-4 py-8 text-center text-slate-500 text-sm">
                    No results for "{query}"
                  </div>
                ) : (
                  Object.entries(grouped).map(([category, items]) => (
                    <div key={category}>
                      <div className="px-4 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                        {category}
                      </div>
                      {items.map((item) => {
                        const Icon = item.icon;
                        const isSelected = item._idx === selectedIndex;
                        return (
                          <button
                            key={item.name}
                            data-index={item._idx}
                            onClick={() => handleSelect(item)}
                            onMouseEnter={() => setSelectedIndex(item._idx)}
                            className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                              isSelected
                                ? 'bg-cyan-500/15 text-cyan-400'
                                : 'text-slate-300 hover:bg-slate-800/50'
                            }`}
                          >
                            <div className={`p-1.5 rounded-lg ${isSelected ? 'bg-cyan-500/20' : 'bg-slate-800'}`}>
                              <Icon className="w-4 h-4" />
                            </div>
                            <span className="flex-1 text-sm font-medium">{item.name}</span>
                            {isSelected && (
                              <ArrowRight className="w-4 h-4 text-cyan-400" />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  ))
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-2 border-t border-slate-700/50 flex items-center gap-4 text-[10px] text-slate-500">
                <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 font-mono">↑↓</kbd> Navigate</span>
                <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 font-mono">↵</kbd> Open</span>
                <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 font-mono">ESC</kbd> Close</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default CommandPalette;
