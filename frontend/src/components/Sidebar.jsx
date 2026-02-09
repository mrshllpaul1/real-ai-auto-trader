import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, TrendingUp, BarChart3, Settings, Sparkles,
  Brain, Newspaper, Zap, Radar, Bot, FlaskConical, BookOpen,
  Menu, X, ChevronLeft, Key, Wallet, TestTube, Cpu, MessageCircle, Layers,
  Target, Gem, Calendar, Shield, Award, Gauge, Briefcase, PieChart, Wand2, GraduationCap, Waves,
  Users, Activity, Layout, Sprout, LineChart, DollarSign
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import NotificationCenter from './NotificationCenter';
import { useTradingMode } from '../context/TradingModeContext';

// Trading Mode Indicator component
const TradingModeIndicator = ({ isCollapsed, mobile }) => {
  const { mode, isRealMode, toggleMode } = useTradingMode();
  
  if (isCollapsed && !mobile) {
    // Compact indicator for collapsed sidebar
    return (
      <button
        onClick={toggleMode}
        className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
          isRealMode 
            ? 'bg-[#00FF94]/20 border border-[#00FF94]/50' 
            : 'bg-[#FF9500]/20 border border-[#FF9500]/50'
        }`}
        title={`Click to switch to ${isRealMode ? 'Paper' : 'Real'} Trading`}
        data-testid="trading-mode-indicator-compact"
      >
        {isRealMode ? (
          <Wallet size={18} className="text-[#00FF94]" />
        ) : (
          <TestTube size={18} className="text-[#FF9500]" />
        )}
      </button>
    );
  }
  
  // Full indicator with label
  return (
    <button
      onClick={toggleMode}
      className={`w-full mt-2 p-2 rounded-lg flex items-center gap-2 transition-all active:scale-[0.98] ${
        isRealMode 
          ? 'bg-[#00FF94]/10 border border-[#00FF94]/30 hover:bg-[#00FF94]/20' 
          : 'bg-[#FF9500]/10 border border-[#FF9500]/30 hover:bg-[#FF9500]/20'
      }`}
      title={`Click to switch to ${isRealMode ? 'Paper' : 'Real'} Trading`}
      data-testid="trading-mode-indicator"
    >
      {isRealMode ? (
        <>
          <div className="w-2 h-2 rounded-full bg-[#00FF94] animate-pulse" />
          <Wallet size={16} className="text-[#00FF94]" />
          <span className="text-sm font-bold text-[#00FF94]">REAL</span>
          <span className="text-xs text-[#A1A1AA] ml-auto">Live Money</span>
        </>
      ) : (
        <>
          <div className="w-2 h-2 rounded-full bg-[#FF9500]" />
          <TestTube size={16} className="text-[#FF9500]" />
          <span className="text-sm font-bold text-[#FF9500]">PAPER</span>
          <span className="text-xs text-[#A1A1AA] ml-auto">Practice</span>
        </>
      )}
    </button>
  );
};

// Mobile menu button component
const MobileMenuButton = ({ isOpen, onClick }) => (
  <button
    onClick={onClick}
    className="md:hidden fixed top-4 left-4 z-50 p-3 bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl shadow-lg active:scale-95 transition-transform"
    data-testid="mobile-menu-btn"
  >
    {isOpen ? <X size={24} className="text-[#00FF94]" /> : <Menu size={24} className="text-white" />}
  </button>
);

// Collapse button component
const CollapseButton = ({ isCollapsed, onClick }) => (
  <button
    onClick={onClick}
    className="hidden md:flex absolute -right-3 top-20 z-10 p-1.5 bg-[#1F1F1F] border border-[#333] rounded-full hover:bg-[#333] transition-colors"
    data-testid="collapse-btn"
  >
    <ChevronLeft size={16} className={`text-[#A1A1AA] transition-transform ${isCollapsed ? 'rotate-180' : ''}`} />
  </button>
);

// Sidebar content component
const SidebarContent = ({ isCollapsed, mobile, navItems, tradingMode }) => (
  <div className={`flex flex-col h-full ${mobile ? 'pt-16' : ''}`}>
    <div className={`p-4 ${isCollapsed && !mobile ? 'px-2' : 'p-6'} border-b border-[#1F1F1F]`}>
      <div className="flex items-center justify-between">
        {(!isCollapsed || mobile) ? (
          <h1 className="text-xl md:text-2xl font-heading font-black tracking-tight" data-testid="app-logo">
            <span className="text-[#00FF94]">AI</span>
            <span className="text-white">Crypto</span>
            <span className="text-[#9D00FF]">Trade</span>
          </h1>
        ) : (
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00FF94] to-[#9D00FF] flex items-center justify-center">
            <span className="text-black font-bold text-sm">AI</span>
          </div>
        )}
        {(!isCollapsed || mobile) && <NotificationCenter />}
      </div>
      {(!isCollapsed || mobile) && <p className="text-xs text-[#A1A1AA] mt-1">Real Money Auto Trading</p>}
      {/* Trading Mode Indicator - passed as prop */}
      {tradingMode}
    </div>
    <nav className="flex-1 p-2 md:p-4 overflow-y-auto" data-testid="sidebar-nav">
      <ul className="space-y-1">
        {navItems.map((item) => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 active:scale-95 ${
                  isCollapsed && !mobile ? 'justify-center' : ''
                } ${
                  isActive
                    ? 'bg-[#00FF94]/10 text-[#00FF94] border border-[#00FF94]/30'
                    : item.highlight 
                      ? 'text-[#FF0055] hover:text-[#FF0055] hover:bg-[#FF0055]/10 border border-transparent hover:border-[#FF0055]/30'
                      : 'text-[#A1A1AA] hover:text-white hover:bg-white/5 border border-transparent'
                }`
              }
            >
              <item.icon size={20} className="flex-shrink-0" />
              {(!isCollapsed || mobile) && <span className="font-medium text-sm">{item.label}</span>}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
    {(!isCollapsed || mobile) && (
      <div className="p-4 border-t border-[#1F1F1F]">
        <div className="bg-gradient-to-r from-[#9D00FF]/20 to-[#00FF94]/20 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={14} className="text-[#9D00FF]" />
            <span className="text-xs font-bold text-white">AI-Powered</span>
          </div>
          <p className="text-xs text-[#A1A1AA]">Strategies updated weekly</p>
        </div>
      </div>
    )}
  </div>
);

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  
  // Use trading mode context
  const { mode, isRealMode, toggleMode } = useTradingMode();

  // Close mobile menu on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Check screen size and set initial state
  useEffect(() => {
    const checkMobile = () => {
      if (window.innerWidth < 768) {
        setIsCollapsed(true);
      }
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Command Center', highlight: true },
    { path: '/ai-center', icon: Brain, label: 'AI Center', highlight: true },
    { path: '/budget', icon: Shield, label: 'AI Budget', highlight: true },
    { path: '/spot-trading', icon: Wallet, label: 'Spot Trading', highlight: true },
    { path: '/positions', icon: Briefcase, label: 'Positions', highlight: true },
    { path: '/portfolio-dashboard', icon: PieChart, label: 'Portfolio', highlight: true },
    { path: '/copy-trading', icon: Users, label: 'Copy Trading', highlight: true },
    { path: '/market-maker', icon: Activity, label: 'Market Maker', highlight: true },
    { path: '/options-trading', icon: Target, label: 'Options', highlight: true },
    { path: '/backtest-engine', icon: BarChart3, label: 'Backtest Engine', highlight: true },
    { path: '/advanced-orders', icon: Layers, label: 'Advanced Orders', highlight: true },
    { path: '/defi-wallet', icon: Wallet, label: 'DeFi Wallet', highlight: true },
    { path: '/yield-farming', icon: Sprout, label: 'Yield Farming', highlight: true },
    { path: '/perpetuals', icon: LineChart, label: 'Perpetuals', highlight: true },
    { path: '/news-sentiment', icon: Newspaper, label: 'News Sentiment', highlight: true },
    { path: '/risk-analyzer', icon: Shield, label: 'Risk Analyzer', highlight: true },
    { path: '/triggers', icon: Target, label: 'Event Triggers', highlight: true },
    { path: '/trigger-performance', icon: Award, label: 'Trigger Stats', highlight: true },
    { path: '/adaptive', icon: Gauge, label: 'Adaptive AI', highlight: true },
    { path: '/training', icon: GraduationCap, label: 'AI Training', highlight: true },
    { path: '/model-performance', icon: Cpu, label: 'Model Performance', highlight: true },
    { path: '/event-timeline', icon: Calendar, label: 'Event Timeline', highlight: true },
    { path: '/journal', icon: BookOpen, label: 'Journal' },
    { path: '/scanner', icon: Radar, label: 'Gem Scanner', highlight: true },
    { path: '/gem-backtest', icon: Gem, label: 'Gem Backtester', highlight: true },
    { path: '/gem-ml-dl', icon: Cpu, label: 'ML vs DL Gems', highlight: true },
    { path: '/auto-exec', icon: Bot, label: 'Auto Execute', highlight: true },
    { path: '/advanced', icon: FlaskConical, label: 'Advanced' },
    { path: '/strategies', icon: Sparkles, label: 'AI Strategies' },
    { path: '/auto-trading', icon: Zap, label: 'Auto Trading' },
    { path: '/trading', icon: TrendingUp, label: 'Trading' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/learning', icon: Brain, label: 'AI Learning' },
    { path: '/learning-loop', icon: Brain, label: 'Learning Loop', highlight: true },
    { path: '/ensemble', icon: Layers, label: 'Ensemble AI', highlight: true },
    { path: '/news', icon: Newspaper, label: 'News & Intel' },
    { path: '/dashboard-settings', icon: Layout, label: 'Customize', highlight: true },
    { path: '/guide', icon: BookOpen, label: 'Guide' },
    { path: '/setup', icon: Key, label: 'Setup', highlight: true },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <>
      <MobileMenuButton isOpen={isOpen} onClick={() => setIsOpen(!isOpen)} />
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="md:hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="md:hidden fixed left-0 top-0 bottom-0 w-72 bg-[#0A0A0A] border-r border-[#1F1F1F] z-40 overflow-hidden"
            data-testid="mobile-sidebar"
          >
            <SidebarContent 
              isCollapsed={false} 
              mobile={true} 
              navItems={navItems} 
              tradingMode={<TradingModeIndicator isCollapsed={false} mobile={true} />}
            />
          </motion.div>
        )}
      </AnimatePresence>
      <motion.div 
        className={`hidden md:flex flex-col glass-card border-r border-[#1F1F1F] relative transition-all duration-300 ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        data-testid="desktop-sidebar"
      >
        <CollapseButton isCollapsed={isCollapsed} onClick={() => setIsCollapsed(!isCollapsed)} />
        <SidebarContent 
          isCollapsed={isCollapsed} 
          mobile={false} 
          navItems={navItems}
          tradingMode={<TradingModeIndicator isCollapsed={isCollapsed} mobile={false} />}
        />
      </motion.div>
    </>
  );
};

export default Sidebar;
