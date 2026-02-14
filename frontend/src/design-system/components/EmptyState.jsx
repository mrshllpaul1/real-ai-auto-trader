/**
 * EmptyState - Consistent empty state component
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Inbox, Search, FileX, TrendingUp, AlertCircle } from 'lucide-react';

const presets = {
  default: {
    icon: Inbox,
    title: 'No data available',
    description: 'There\'s nothing here yet.',
  },
  search: {
    icon: Search,
    title: 'No results found',
    description: 'Try adjusting your search or filters.',
  },
  trades: {
    icon: TrendingUp,
    title: 'No trades yet',
    description: 'Start trading to see your history here.',
  },
  error: {
    icon: AlertCircle,
    title: 'Something went wrong',
    description: 'Unable to load data. Please try again.',
  },
  file: {
    icon: FileX,
    title: 'No files found',
    description: 'Upload files to get started.',
  },
};

export const EmptyState = ({
  preset,
  icon: CustomIcon,
  title,
  description,
  action,
  actionLabel,
  onAction,
  secondaryAction,
  secondaryActionLabel,
  onSecondaryAction,
  size = 'default', // 'sm' | 'default' | 'lg'
  className,
  children,
}) => {
  const presetConfig = preset ? presets[preset] : presets.default;
  const Icon = CustomIcon || presetConfig.icon;
  const displayTitle = title || presetConfig.title;
  const displayDescription = description || presetConfig.description;

  const sizeStyles = {
    sm: {
      container: 'py-6 sm:py-8',
      icon: 'h-8 w-8 sm:h-10 sm:w-10',
      iconWrapper: 'p-3 sm:p-4',
      title: 'text-base sm:text-lg',
      description: 'text-xs sm:text-sm',
    },
    default: {
      container: 'py-8 sm:py-12',
      icon: 'h-10 w-10 sm:h-12 sm:w-12',
      iconWrapper: 'p-4 sm:p-5',
      title: 'text-lg sm:text-xl',
      description: 'text-sm',
    },
    lg: {
      container: 'py-12 sm:py-16',
      icon: 'h-12 w-12 sm:h-16 sm:w-16',
      iconWrapper: 'p-5 sm:p-6',
      title: 'text-xl sm:text-2xl',
      description: 'text-sm sm:text-base',
    },
  };

  const styles = sizeStyles[size];

  return (
    <div className={cn(
      'flex flex-col items-center justify-center text-center px-4',
      styles.container,
      className
    )}>
      {/* Icon */}
      <div className={cn(
        'rounded-full bg-muted mb-4',
        styles.iconWrapper
      )}>
        <Icon className={cn(styles.icon, 'text-muted-foreground')} />
      </div>

      {/* Title */}
      <h3 className={cn(
        'font-semibold text-foreground mb-1 sm:mb-2',
        styles.title
      )}>
        {displayTitle}
      </h3>

      {/* Description */}
      <p className={cn(
        'text-muted-foreground max-w-sm mb-4 sm:mb-6',
        styles.description
      )}>
        {displayDescription}
      </p>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        {(action || onAction) && (
          <Button onClick={onAction} size={size === 'sm' ? 'sm' : 'default'}>
            {actionLabel || action || 'Take Action'}
          </Button>
        )}
        {(secondaryAction || onSecondaryAction) && (
          <Button 
            variant="outline" 
            onClick={onSecondaryAction}
            size={size === 'sm' ? 'sm' : 'default'}
          >
            {secondaryActionLabel || secondaryAction || 'Learn More'}
          </Button>
        )}
      </div>

      {/* Custom Children */}
      {children}
    </div>
  );
};

export default EmptyState;
