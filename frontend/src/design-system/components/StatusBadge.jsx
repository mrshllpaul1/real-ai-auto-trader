/**
 * StatusBadge - Consistent status indicators
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock, 
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';

const statusConfig = {
  success: {
    bg: 'bg-green-500/10',
    text: 'text-green-500',
    border: 'border-green-500/20',
    icon: CheckCircle,
  },
  error: {
    bg: 'bg-red-500/10',
    text: 'text-red-500',
    border: 'border-red-500/20',
    icon: XCircle,
  },
  warning: {
    bg: 'bg-yellow-500/10',
    text: 'text-yellow-500',
    border: 'border-yellow-500/20',
    icon: AlertCircle,
  },
  info: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-500',
    border: 'border-blue-500/20',
    icon: AlertCircle,
  },
  pending: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-500',
    border: 'border-orange-500/20',
    icon: Clock,
  },
  loading: {
    bg: 'bg-primary/10',
    text: 'text-primary',
    border: 'border-primary/20',
    icon: Loader2,
  },
  neutral: {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-border',
    icon: Minus,
  },
  bullish: {
    bg: 'bg-green-500/10',
    text: 'text-green-500',
    border: 'border-green-500/20',
    icon: TrendingUp,
  },
  bearish: {
    bg: 'bg-red-500/10',
    text: 'text-red-500',
    border: 'border-red-500/20',
    icon: TrendingDown,
  },
};

export const StatusBadge = ({
  status,
  label,
  showIcon = true,
  size = 'default', // 'sm' | 'default' | 'lg'
  variant = 'filled', // 'filled' | 'outline' | 'dot'
  pulse = false,
  className,
}) => {
  const config = statusConfig[status] || statusConfig.neutral;
  const Icon = config.icon;

  const sizeStyles = {
    sm: 'text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5',
    default: 'text-xs sm:text-sm px-2 sm:px-3 py-1',
    lg: 'text-sm px-3 sm:px-4 py-1.5',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    default: 'h-3.5 w-3.5 sm:h-4 sm:w-4',
    lg: 'h-4 w-4 sm:h-5 sm:w-5',
  };

  if (variant === 'dot') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <div className={cn(
          'rounded-full',
          size === 'sm' ? 'h-2 w-2' : size === 'lg' ? 'h-3 w-3' : 'h-2.5 w-2.5',
          config.bg,
          pulse && 'animate-pulse'
        )} />
        {label && (
          <span className={cn(
            'font-medium',
            size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm',
            config.text
          )}>
            {label}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={cn(
      'inline-flex items-center gap-1 sm:gap-1.5 rounded-full font-medium',
      sizeStyles[size],
      variant === 'filled' ? config.bg : 'bg-transparent border',
      config.text,
      variant === 'outline' && config.border,
      pulse && 'animate-pulse',
      className
    )}>
      {showIcon && (
        <Icon className={cn(
          iconSizes[size],
          status === 'loading' && 'animate-spin'
        )} />
      )}
      {label && <span>{label}</span>}
    </div>
  );
};

export default StatusBadge;
