import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, TrendingUp, BarChart3, Settings, Sparkles,
  Brain, Newspaper, Zap, Radar, Bot, FlaskConical, BookOpen, GraduationCap,
  Menu, X, ChevronLeft, Key, Wallet, TestTube, Cpu, MessageCircle, Layers,
  Target, Gem, Calendar, Shield, Award, Gauge, Briefcase, PieChart, Wand2, Waves,
  Users, Activity, Layout, Sprout, LineChart, DollarSign, ChevronRight, Bug
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import NotificationCenter from './NotificationCenter';
import { useTradingMode } from '../context/TradingModeContext';

// Enhanced Trading Mode Indicator with modern design
const TradingModeIndicator = ({ isCollapsed, mobile }) => {
  const { mode, isRealMode, toggleMode } = useTradingMode();
  
  if (isCollapsed && !mobile) {
    return (
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={toggleMode}
        className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
          isRealMode 
            ? 'bg-gradient-to-br from-emerald-500/20 to-green-500/10 border border-emerald-500/40 shadow-lg shadow-emerald-500/20' 
            : 'bg-gradient-to-br from-amber-500/20 to-orange-500/10 border border-amber-500/40 shadow-lg shadow-amber-500/20'
        }`}
        title={`Click to switch to ${isRealMode ? 'Paper' : 'Real'} Trading`}
      >
        {isRealMode ? (
          <Wallet size={18} className="text-emerald-400" />
        ) : (
          <TestTube size={18} className="text-amber-400" />
        )}
      </motion.button>
    );
  }
  
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={toggleMode}
      className={`w-full mt-3 p-3 rounded-xl flex items-center gap-3 transition-all duration-300 ${
        isRealMode 
          ? 'bg-gradient-to-r from-emerald-500/15 to-green-500/5 border border-emerald-500/30 hover:border-emerald-400/50 shadow-lg shadow-emerald-500/10' 
          : 'bg-gradient-to-r from-amber-500/15 to-orange-500/5 border border-amber-500/30 hover:border-amber-400/50 shadow-lg shadow-amber-500/10'
      }`}
      title={`Click to switch to ${isRealMode ? 'Paper' : 'Real'} Trading`}
    >
      {isRealMode ? (
        <>
          <div className="relative">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping opacity-50" />
          </div>
          <Wallet size={18} className="text-emerald-400" />
          <span className="text-sm font-bold text-emerald-400 tracking-wide">REAL</span>
          <span className="text-xs text-slate-400 ml-auto bg-emerald-500/10 px-2 py-0.5 rounded-full">Live Money</span>
        </>
      ) : (
        <>
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <TestTube size={18} className="text-amber-400" />
          <span className="text-sm font-bold text-amber-400 tracking-wide">PAPER</span>
          <span className="text-xs text-slate-400 ml-auto bg-amber-500/10 px-2 py-0.5 rounded-full">Practice</span>
        </>
      )}
    </motion.button>
  );
};

// Mobile menu button with modern design
const MobileMenuButton = ({ isOpen, onClick }) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.9 }}
    onClick={onClick}
    className="md:hidden fixed top-4 left-4 z-50 p-3 bg-slate-900/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/50"
  >
    <motion.div
      initial={false}
      animate={{ rotate: isOpen ? 90 : 0 }}
      transition={{ duration: 0.2 }}
    >
      {isOpen ? <X size={24} className="text-emerald-400" /> : <Menu size={24} className="text-slate-300" />}
    </motion.div>
  </motion.button>
);

// Modern collapse button
const CollapseButton = ({ isCollapsed, onClick }) => (
  <motion.button
    whileHover={{ scale: 1.1 }}
    whileTap={{ scale: 0.9 }}
    onClick={onClick}
    className="hidden md:flex absolute -right-3 top-20 z-10 p-1.5 bg-slate-800 border border-slate-600/50 rounded-full hover:bg-slate-700 hover:border-slate-500 transition-all duration-200 shadow-lg"
  >
    <motion.div
      animate={{ rotate: isCollapsed ? 180 : 0 }}
      transition={{ duration: 0.3 }}
    >
      <ChevronLeft size={16} className="text-slate-400" />
    </motion.div>
  </motion.button>
);

// Nav item with enhanced styling
const NavItem = ({ item, isCollapsed, mobile, isActive }) => {
  const Icon = item.icon;
  
  // Color mapping for different nav items
  const colorMap = {
    'Command Center': { active: 'cyan', hover: 'cyan' },
    'Trading': { active: 'emerald', hover: 'emerald' },
    'AI & Strategy': { active: 'violet', hover: 'violet' },
    'Backtest': { active: 'blue', hover: 'blue' },
    'News & Events': { active: 'pink', hover: 'pink' },
    'Scanner & Social': { active: 'amber', hover: 'amber' },
    'DeFi': { active: 'lime', hover: 'lime' },
    'Settings': { active: 'slate', hover: 'slate' },
  };
  
  const colors = colorMap[item.label] || { active: 'emerald', hover: 'slate' };
  
  // Active styles based on color
  const activeStyles = {
    cyan: 'bg-gradient-to-r from-cyan-500/20 to-cyan-500/5 text-cyan-400 border-cyan-500/40 shadow-cyan-500/20',
    emerald: 'bg-gradient-to-r from-emerald-500/20 to-emerald-500/5 text-emerald-400 border-emerald-500/40 shadow-emerald-500/20',
    violet: 'bg-gradient-to-r from-violet-500/20 to-violet-500/5 text-violet-400 border-violet-500/40 shadow-violet-500/20',
    blue: 'bg-gradient-to-r from-blue-500/20 to-blue-500/5 text-blue-400 border-blue-500/40 shadow-blue-500/20',
    pink: 'bg-gradient-to-r from-pink-500/20 to-pink-500/5 text-pink-400 border-pink-500/40 shadow-pink-500/20',
    amber: 'bg-gradient-to-r from-amber-500/20 to-amber-500/5 text-amber-400 border-amber-500/40 shadow-amber-500/20',
    lime: 'bg-gradient-to-r from-lime-500/20 to-lime-500/5 text-lime-400 border-lime-500/40 shadow-lime-500/20',
    slate: 'bg-gradient-to-r from-slate-500/20 to-slate-500/5 text-slate-300 border-slate-500/40 shadow-slate-500/20',
  };
  
  // Hover styles
  const hoverStyles = {
    cyan: 'hover:text-cyan-400 hover:bg-cyan-500/10 hover:border-cyan-500/30',
    emerald: 'hover:text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/30',
    violet: 'hover:text-violet-400 hover:bg-violet-500/10 hover:border-violet-500/30',
    blue: 'hover:text-blue-400 hover:bg-blue-500/10 hover:border-blue-500/30',
    pink: 'hover:text-pink-400 hover:bg-pink-500/10 hover:border-pink-500/30',
    amber: 'hover:text-amber-400 hover:bg-amber-500/10 hover:border-amber-500/30',
    lime: 'hover:text-lime-400 hover:bg-lime-500/10 hover:border-lime-500/30',
    slate: 'hover:text-slate-300 hover:bg-slate-500/10 hover:border-slate-500/30',
  };

  return (
    <NavLink
      to={item.path}
      className={({ isActive: linkActive }) =>
        `group relative flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-300 border ${
          isCollapsed && !mobile ? 'justify-center' : ''
        } ${
          linkActive
            ? `${activeStyles[colors.active]} border shadow-lg`
            : `text-slate-400 border-transparent ${hoverStyles[colors.hover]}`
        }`
      }
    >
      {({ isActive: linkActive }) => (
        <>
          {/* Active indicator bar */}
          {linkActive && (
            <motion.div
              layoutId="activeIndicator"
              className={`absolute left-0 w-1 h-8 rounded-r-full bg-gradient-to-b ${
                colors.active === 'cyan' ? 'from-cyan-400 to-cyan-600' :
                colors.active === 'emerald' ? 'from-emerald-400 to-emerald-600' :
                colors.active === 'violet' ? 'from-violet-400 to-violet-600' :
                colors.active === 'blue' ? 'from-blue-400 to-blue-600' :
                colors.active === 'pink' ? 'from-pink-400 to-pink-600' :
                colors.active === 'amber' ? 'from-amber-400 to-amber-600' :
                colors.active === 'lime' ? 'from-lime-400 to-lime-600' :
                'from-slate-400 to-slate-600'
              }`}
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
            />
          )}
          
          <motion.div
            whileHover={{ scale: 1.1, rotate: linkActive ? 0 : 5 }}
            whileTap={{ scale: 0.95 }}
            className="flex-shrink-0"
          >
            <Icon size={20} />
          </motion.div>
          
          {(!isCollapsed || mobile) && (
            <span className="font-medium text-sm tracking-wide">{item.label}</span>
          )}
          
          {/* Hover arrow indicator */}
          {(!isCollapsed || mobile) && !linkActive && (
            <ChevronRight 
              size={14} 
              className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-slate-500" 
            />
          )}
        </>
      )}
    </NavLink>
  );
};

// Enhanced Sidebar content
const SidebarContent = ({ isCollapsed, mobile, navItems, tradingMode }) => {
  const [systemHealth, setSystemHealth] = useState('online');
  
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const baseUrl = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || '';
        const res = await fetch(`${baseUrl}/api/health`, { signal: AbortSignal.timeout(5000) });
        setSystemHealth(res.ok ? 'online' : 'degraded');
      } catch {
        setSystemHealth('offline');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, []);

  const healthConfig = {
    online: { color: 'bg-emerald-400', label: 'System Online', textColor: 'text-emerald-400' },
    degraded: { color: 'bg-amber-400', label: 'Degraded', textColor: 'text-amber-400' },
    offline: { color: 'bg-red-400', label: 'Offline', textColor: 'text-red-400' },
  };
  const health = healthConfig[systemHealth];

  return (
    <div className={`flex flex-col h-full ${mobile ? 'pt-16' : ''}`}>
    {/* Header Section */}
    <div className={`${isCollapsed && !mobile ? 'p-3' : 'p-5'} border-b border-slate-800/80`}>
      <div className="flex items-center justify-between">
        {(!isCollapsed || mobile) ? (
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-xl md:text-2xl font-black tracking-tight"
          >
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">AI</span>
            <span className="text-white">Crypto</span>
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">Trade</span>
            <motion.span
              animate={{ rotate: [0, 10, 0] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="inline-block ml-1"
            >
              ⚡
            </motion.span>
          </motion.h1>
        ) : (
          <motion.div 
            whileHover={{ scale: 1.1, rotate: 5 }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 via-cyan-500 to-violet-500 flex items-center justify-center shadow-lg shadow-emerald-500/30"
          >
            <span className="text-black font-bold text-sm">AI</span>
          </motion.div>
        )}
        {(!isCollapsed || mobile) && <NotificationCenter />}
      </div>
      {(!isCollapsed || mobile) && (
        <p className="text-xs text-slate-500 mt-1.5 tracking-wide">Real Money Auto Trading</p>
      )}
      {tradingMode}
    </div>
    
    {/* Navigation Section */}
    <nav className="flex-1 p-3 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
      <ul className="space-y-1.5">
        {navItems.map((item, index) => (
          <motion.li 
            key={item.path}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <NavItem 
              item={item} 
              isCollapsed={isCollapsed} 
              mobile={mobile}
            />
          </motion.li>
        ))}
      </ul>
    </nav>
    
    {/* Footer Section - System Health + User Profile */}
    <div className="p-3 border-t border-slate-800/80 space-y-2">
      {/* System Health Indicator */}
      {(!isCollapsed || mobile) ? (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-800/50 border border-slate-700/30">
          <div className="relative">
            <div className={`w-2 h-2 rounded-full ${health.color}`} />
            {systemHealth === 'online' && (
              <div className={`absolute inset-0 w-2 h-2 rounded-full ${health.color} animate-ping opacity-50`} />
            )}
          </div>
          <span className={`text-xs font-medium ${health.textColor}`}>{health.label}</span>
          <span className="text-[10px] text-slate-600 ml-auto">v2.0</span>
        </div>
      ) : (
        <div className="flex justify-center py-1">
          <div className="relative">
            <div className={`w-2.5 h-2.5 rounded-full ${health.color}`} />
            {systemHealth === 'online' && (
              <div className={`absolute inset-0 w-2.5 h-2.5 rounded-full ${health.color} animate-ping opacity-50`} />
            )}
          </div>
        </div>
      )}

      {/* User Profile */}
      {(!isCollapsed || mobile) ? (
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-gradient-to-r from-slate-800/80 to-slate-800/40 border border-slate-700/30 hover:border-slate-600/50 transition-colors cursor-pointer"
          onClick={() => window.location.href = '/settings'}
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-violet-500 flex items-center justify-center shadow-lg">
            <span className="text-xs font-bold text-white">T</span>
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-xs font-semibold text-white block truncate">Trader</span>
            <span className="text-[10px] text-slate-500">Kraken Connected</span>
          </div>
          <ChevronRight size={14} className="text-slate-600 flex-shrink-0" />
        </div>
      ) : (
        <div className="flex justify-center">
          <motion.div 
            whileHover={{ scale: 1.1 }}
            className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 to-violet-500 flex items-center justify-center shadow-lg cursor-pointer"
            onClick={() => window.location.href = '/settings'}
          >
            <span className="text-xs font-bold text-white">T</span>
          </motion.div>
        </div>
      )}
    </div>
  </div>
  );
};

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const { mode, isRealMode, toggleMode } = useTradingMode();

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

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
    { path: '/', icon: LayoutDashboard, label: 'Command Center' },
    { path: '/trading', icon: Wallet, label: 'Trading' },
    { path: '/ai', icon: Brain, label: 'AI & Strategy' },
    { path: '/backtest', icon: BarChart3, label: 'Backtest' },
    { path: '/news', icon: Newspaper, label: 'News & Events' },
    { path: '/scanner', icon: Radar, label: 'Scanner & Social' },
    { path: '/defi', icon: Sprout, label: 'DeFi' },
    { path: '/error-analytics', icon: Bug, label: 'Error Analytics' },
    { path: '/performance-monitor', icon: Gauge, label: 'Performance' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <>
      <MobileMenuButton isOpen={isOpen} onClick={() => setIsOpen(!isOpen)} />
      
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-md z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>
      
      {/* Mobile sidebar */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: '-100%', opacity: 0.5 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '-100%', opacity: 0.5 }}
            transition={{ type: 'spring', damping: 25, stiffness: 250 }}
            className="md:hidden fixed left-0 top-0 bottom-0 w-72 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 border-r border-slate-800/50 z-40 overflow-hidden shadow-2xl shadow-black/50"
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
      
      {/* Desktop sidebar */}
      <motion.div 
        className={`hidden md:flex flex-col bg-gradient-to-b from-slate-900/95 via-slate-900/90 to-slate-950/95 backdrop-blur-xl border-r border-slate-800/50 relative transition-all duration-300 shadow-2xl shadow-black/30 ${
          isCollapsed ? 'w-[68px]' : 'w-64'
        }`}
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
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
