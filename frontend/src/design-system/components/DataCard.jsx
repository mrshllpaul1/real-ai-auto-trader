/**
 * DataCard - Standardized card for displaying data/metrics
 * Mobile-responsive with consistent styling
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const DataCard = ({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  trend, // 'up' | 'down' | 'neutral'
  footer,
  className,
  loading = false,
  size = 'default', // 'sm' | 'default' | 'lg'
  variant = 'default', // 'default' | 'success' | 'danger' | 'warning' | 'glass'
  onClick,
  children,
}) => {
  const sizeStyles = {
    sm: 'p-3 sm:p-4',
    default: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
  };

  const variantStyles = {
    default: 'bg-card border border-border',
    success: 'bg-green-500/10 border border-green-500/20',
    danger: 'bg-red-500/10 border border-red-500/20',
    warning: 'bg-yellow-500/10 border border-yellow-500/20',
    glass: 'bg-white/5 backdrop-blur-md border border-white/10',
  };

  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend === 'down') return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-500';
    if (trend === 'down') return 'text-red-500';
    return 'text-muted-foreground';
  };

  if (loading) {
    return (
      <div className={cn(
        'rounded-xl animate-pulse',
        sizeStyles[size],
        variantStyles[variant],
        className
      )}>
        <div className="h-4 bg-muted rounded w-1/3 mb-3" />
        <div className="h-8 bg-muted rounded w-2/3 mb-2" />
        <div className="h-3 bg-muted rounded w-1/4" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        'rounded-xl transition-all duration-200',
        sizeStyles[size],
        variantStyles[variant],
        onClick && 'cursor-pointer hover:scale-[1.02] hover:shadow-lg',
        className
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2 sm:mb-3">
        <span className="text-xs sm:text-sm font-medium text-muted-foreground uppercase tracking-wide">
          {title}
        </span>
        {Icon && (
          <div className="p-1.5 sm:p-2 rounded-lg bg-primary/10">
            <Icon className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
          </div>
        )}
      </div>

      {/* Value */}
      <div className="flex items-end gap-2 sm:gap-3">
        <span className={cn(
          'font-bold font-mono tracking-tight',
          size === 'sm' ? 'text-xl sm:text-2xl' : size === 'lg' ? 'text-3xl sm:text-4xl' : 'text-2xl sm:text-3xl'
        )}>
          {value}
        </span>
        
        {change !== undefined && (
          <div className={cn('flex items-center gap-1 mb-1', getTrendColor())}>
            {getTrendIcon()}
            <span className="text-xs sm:text-sm font-medium">
              {change > 0 ? '+' : ''}{change}%
            </span>
          </div>
        )}
      </div>

      {/* Change Label */}
      {changeLabel && (
        <p className="text-xs sm:text-sm text-muted-foreground mt-1">
          {changeLabel}
        </p>
      )}

      {/* Custom Children */}
      {children}

      {/* Footer */}
      {footer && (
        <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-border">
          {footer}
        </div>
      )}
    </div>
  );
};

export default DataCard;
