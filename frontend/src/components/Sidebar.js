import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TrendingUp, 
  BarChart3, 
  Settings, 
  Sparkles,
  Brain,
  Newspaper,
  Zap,
  Radar
} from 'lucide-react';
import { motion } from 'framer-motion';

const Sidebar = () => {
  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/scanner', icon: Radar, label: 'Gem Scanner', highlight: true },
    { path: '/strategies', icon: Sparkles, label: 'AI Strategies' },
    { path: '/auto-trading', icon: Zap, label: 'Auto Trading' },
    { path: '/trading', icon: TrendingUp, label: 'Trading' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/learning', icon: Brain, label: 'AI Learning' },
    { path: '/news', icon: Newspaper, label: 'News & Intel' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <motion.div 
      className="w-64 glass-card border-r border-[#1F1F1F] flex flex-col"
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      data-testid="sidebar"
    >
      {/* Logo */}
      <div className="p-6 border-b border-[#1F1F1F]">
        <h1 className="text-2xl font-heading font-black tracking-tight" data-testid="app-logo">
          <span className="text-[#00FF94]">AI</span>
          <span className="text-white">Crypto</span>
          <span className="text-[#9D00FF]">Trade</span>
        </h1>
        <p className="text-xs text-[#A1A1AA] mt-1">Real Money Auto Trading</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4" data-testid="sidebar-nav">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-[#00FF94]/10 text-[#00FF94] border border-[#00FF94]/30'
                      : item.highlight 
                        ? 'text-[#FF0055] hover:text-[#FF0055] hover:bg-[#FF0055]/10 border border-[#FF0055]/30'
                        : 'text-[#A1A1AA] hover:text-white hover:bg-white/5'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <item.icon size={20} />
                    <span className="font-medium">{item.label}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#1F1F1F]">
        <div className="bg-gradient-to-r from-[#9D00FF]/20 to-[#00FF94]/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={16} className="text-[#9D00FF]" />
            <span className="text-xs font-bold text-white">AI-Powered</span>
          </div>
          <p className="text-xs text-[#A1A1AA]">
            Strategies updated weekly
          </p>
        </div>
      </div>
    </motion.div>
  );
};

export default Sidebar;