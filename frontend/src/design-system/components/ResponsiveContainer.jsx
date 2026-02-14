/**
 * ResponsiveContainer - Layout wrapper with responsive padding
 */

import React from 'react';
import { cn } from '@/lib/utils';

export const ResponsiveContainer = ({
  children,
  className,
  maxWidth = 'default', // 'sm' | 'default' | 'lg' | 'xl' | 'full'
  padding = true,
  center = true,
}) => {
  const maxWidthStyles = {
    sm: 'max-w-3xl',
    default: 'max-w-6xl',
    lg: 'max-w-7xl',
    xl: 'max-w-[1600px]',
    full: 'max-w-full',
  };

  return (
    <div className={cn(
      'w-full',
      padding && 'px-4 sm:px-6 lg:px-8',
      center && 'mx-auto',
      maxWidthStyles[maxWidth],
      className
    )}>
      {children}
    </div>
  );
};

/**
 * ResponsiveGrid - Grid with responsive columns
 */
export const ResponsiveGrid = ({
  children,
  className,
  cols = { default: 1, sm: 2, lg: 3, xl: 4 },
  gap = 'default', // 'sm' | 'default' | 'lg'
}) => {
  const gapStyles = {
    sm: 'gap-2 sm:gap-3',
    default: 'gap-4 sm:gap-6',
    lg: 'gap-6 sm:gap-8',
  };

  return (
    <div className={cn(
      'grid',
      `grid-cols-${cols.default}`,
      cols.sm && `sm:grid-cols-${cols.sm}`,
      cols.md && `md:grid-cols-${cols.md}`,
      cols.lg && `lg:grid-cols-${cols.lg}`,
      cols.xl && `xl:grid-cols-${cols.xl}`,
      gapStyles[gap],
      className
    )}>
      {children}
    </div>
  );
};

/**
 * ResponsiveStack - Flex stack that switches direction on breakpoints
 */
export const ResponsiveStack = ({
  children,
  className,
  direction = 'col-to-row', // 'col-to-row' | 'row-to-col'
  gap = 'default',
  align = 'stretch',
  justify = 'start',
}) => {
  const gapStyles = {
    sm: 'gap-2 sm:gap-3',
    default: 'gap-4 sm:gap-6',
    lg: 'gap-6 sm:gap-8',
  };

  const directionStyles = {
    'col-to-row': 'flex-col md:flex-row',
    'row-to-col': 'flex-row md:flex-col',
  };

  const alignStyles = {
    start: 'items-start',
    center: 'items-center',
    end: 'items-end',
    stretch: 'items-stretch',
  };

  const justifyStyles = {
    start: 'justify-start',
    center: 'justify-center',
    end: 'justify-end',
    between: 'justify-between',
    around: 'justify-around',
  };

  return (
    <div className={cn(
      'flex',
      directionStyles[direction],
      gapStyles[gap],
      alignStyles[align],
      justifyStyles[justify],
      className
    )}>
      {children}
    </div>
  );
};

export default ResponsiveContainer;
