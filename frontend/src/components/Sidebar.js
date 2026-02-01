import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TrendingUp, 
  BarChart3, 
  Settings, 
  Sparkles,
  Brain,
  Newspaper,
  Zap,
  Radar,
  Bot,
  FlaskConical,
  BookOpen,
  Menu,
  X,
  ChevronLeft
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import NotificationCenter from './NotificationCenter';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  // Close mobile menu on route change
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Check screen size and set initial state
  useEffect(() => {
    const checkMobile = () => {
      const isMobile = window.innerWidth < 768;
      if (isMobile) {
        setIsCollapsed(true);
      }
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/scanner', icon: Radar, label: 'Gem Scanner', highlight: true },
    { path: '/auto-exec', icon: Bot, label: 'Auto Execute', highlight: true },
    { path: '/advanced', icon: FlaskConical, label: 'Advanced' },
    { path: '/strategies', icon: Sparkles, label: 'AI Strategies' },
    { path: '/auto-trading', icon: Zap, label: 'Auto Trading' },
    { path: '/trading', icon: TrendingUp, label: 'Trading' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/learning', icon: Brain, label: 'AI Learning' },
    { path: '/news', icon: Newspaper, label: 'News & Intel' },
    { path: '/guide', icon: BookOpen, label: 'Guide' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  // Mobile menu toggle button (fixed position)
  const MobileMenuButton = () => (
    <button
      onClick={() => setIsOpen(!isOpen)}
      className="md:hidden fixed top-4 left-4 z-50 p-3 bg-[#0A0A0A] border border-[#1F1F1F] rounded-xl shadow-lg active:scale-95 transition-transform"
      data-testid="mobile-menu-btn"
    >
      {isOpen ? (
        <X size={24} className="text-[#00FF94]" />
      ) : (
        <Menu size={24} className="text-white" />
      )}
    </button>
  );

  // Desktop collapse button
  const CollapseButton = () => (
    <button
      onClick={() => setIsCollapsed(!isCollapsed)}
      className="hidden md:flex absolute -right-3 top-20 z-10 p-1.5 bg-[#1F1F1F] border border-[#333] rounded-full hover:bg-[#333] transition-colors"
      data-testid="collapse-btn"
    >
      <ChevronLeft 
        size={16} 
        className={`text-[#A1A1AA] transition-transform ${isCollapsed ? 'rotate-180' : ''}`} 
      />
    </button>
  );

  // Sidebar content
  const SidebarContent = ({ mobile = false }) => (
    <div className={`flex flex-col h-full ${mobile ? 'pt-16' : ''}`}>
      {/* Logo */}
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
        {(!isCollapsed || mobile) && (
          <p className="text-xs text-[#A1A1AA] mt-1">Real Money Auto Trading</p>
        )}
      </div>

      {/* Navigation */}
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
                {(!isCollapsed || mobile) && (
                  <span className="font-medium text-sm">{item.label}</span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer - only show when expanded */}
      {(!isCollapsed || mobile) && (
        <div className="p-4 border-t border-[#1F1F1F]">
          <div className="bg-gradient-to-r from-[#9D00FF]/20 to-[#00FF94]/20 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles size={14} className="text-[#9D00FF]" />
              <span className="text-xs font-bold text-white">AI-Powered</span>
            </div>
            <p className="text-xs text-[#A1A1AA]">
              Strategies updated weekly
            </p>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <MobileMenuButton />

      {/* Mobile Overlay */}
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

      {/* Mobile Sidebar */}
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
            <SidebarContent mobile={true} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop Sidebar */}
      <motion.div 
        className={`hidden md:flex flex-col glass-card border-r border-[#1F1F1F] relative transition-all duration-300 ${
          isCollapsed ? 'w-16' : 'w-64'
        }`}
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        data-testid="desktop-sidebar"
      >
        <CollapseButton />
        <SidebarContent mobile={false} />
      </motion.div>
    </>
  );
};

export default Sidebar;
