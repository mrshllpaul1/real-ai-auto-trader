/**
 * StatWidget - Compact stat display widget
 * For dashboards and summaries
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

export const StatWidget = ({
  label,
  value,
  change,
  prefix = '',
  suffix = '',
  trend, // 'up' | 'down' | 'neutral'
  size = 'default', // 'sm' | 'default' | 'lg'
  inline = false,
  className,
}) => {
  const getTrendIcon = () => {
    const iconClass = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4';
    if (trend === 'up') return <ArrowUp className={cn(iconClass, 'text-green-500')} />;
    if (trend === 'down') return <ArrowDown className={cn(iconClass, 'text-red-500')} />;
    return <Minus className={cn(iconClass, 'text-muted-foreground')} />;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-500';
    if (trend === 'down') return 'text-red-500';
    return 'text-muted-foreground';
  };

  const sizeStyles = {
    sm: {
      label: 'text-[10px] sm:text-xs',
      value: 'text-sm sm:text-base',
      change: 'text-[10px] sm:text-xs',
    },
    default: {
      label: 'text-xs sm:text-sm',
      value: 'text-lg sm:text-xl',
      change: 'text-xs sm:text-sm',
    },
    lg: {
      label: 'text-sm',
      value: 'text-2xl sm:text-3xl',
      change: 'text-sm',
    },
  };

  if (inline) {
    return (
      <div className={cn('flex items-center gap-2 sm:gap-3', className)}>
        <span className={cn('text-muted-foreground', sizeStyles[size].label)}>
          {label}:
        </span>
        <span className={cn('font-semibold font-mono', sizeStyles[size].value)}>
          {prefix}{value}{suffix}
        </span>
        {change !== undefined && (
          <span className={cn('flex items-center gap-0.5', getTrendColor(), sizeStyles[size].change)}>
            {getTrendIcon()}
            {Math.abs(change)}%
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col', className)}>
      <span className={cn(
        'text-muted-foreground uppercase tracking-wide mb-1',
        sizeStyles[size].label
      )}>
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className={cn('font-bold font-mono', sizeStyles[size].value)}>
          {prefix}{value}{suffix}
        </span>
        {change !== undefined && (
          <span className={cn('flex items-center gap-0.5', getTrendColor(), sizeStyles[size].change)}>
            {getTrendIcon()}
            {change > 0 ? '+' : ''}{change}%
          </span>
        )}
      </div>
    </div>
  );
};

export default StatWidget;
