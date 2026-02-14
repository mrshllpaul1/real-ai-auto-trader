/**
 * MobileNav - Bottom navigation for mobile devices
 */

import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  TrendingUp, 
  Brain, 
  Wallet, 
  Settings,
  BarChart3,
  Bell
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Home' },
  { path: '/trading', icon: TrendingUp, label: 'Trade' },
  { path: '/ai-hub', icon: Brain, label: 'AI' },
  { path: '/portfolio', icon: Wallet, label: 'Portfolio' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export const MobileNav = ({ className }) => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav className={cn(
      'fixed bottom-0 left-0 right-0 z-50',
      'bg-background/95 backdrop-blur-lg border-t border-border',
      'px-2 pb-safe pt-2',
      'md:hidden', // Hide on desktop
      className
    )}>
      <div className="flex items-center justify-around">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname === path || 
            (path !== '/' && location.pathname.startsWith(path));
          
          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={cn(
                'flex flex-col items-center justify-center',
                'min-w-[64px] py-2 px-3 rounded-lg',
                'transition-all duration-200',
                isActive 
                  ? 'text-primary bg-primary/10' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
            >
              <Icon className={cn(
                'h-5 w-5 mb-1',
                isActive && 'scale-110'
              )} />
              <span className={cn(
                'text-[10px] font-medium',
                isActive && 'font-semibold'
              )}>
                {label}
              </span>
            </button>
          );
        })}  
      </div>
    </nav>
  );
};

export default MobileNav;
