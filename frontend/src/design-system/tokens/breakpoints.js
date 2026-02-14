/**
 * Design System - Breakpoints & Responsive Utilities
 * Mobile-first responsive design system
 */

export const breakpoints = {
  xs: '375px',   // Small phones
  sm: '640px',   // Large phones
  md: '768px',   // Tablets
  lg: '1024px',  // Small laptops
  xl: '1280px',  // Desktops
  '2xl': '1536px', // Large desktops
};

export const mediaQueries = {
  xs: `@media (min-width: ${breakpoints.xs})`,
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
  '2xl': `@media (min-width: ${breakpoints['2xl']})`,
  
  // Max-width queries (for targeting smaller screens)
  maxXs: `@media (max-width: ${breakpoints.xs})`,
  maxSm: `@media (max-width: ${breakpoints.sm})`,
  maxMd: `@media (max-width: ${breakpoints.md})`,
  maxLg: `@media (max-width: ${breakpoints.lg})`,
  
  // Special queries
  touch: '@media (hover: none) and (pointer: coarse)',
  mouse: '@media (hover: hover) and (pointer: fine)',
  reducedMotion: '@media (prefers-reduced-motion: reduce)',
  dark: '@media (prefers-color-scheme: dark)',
  light: '@media (prefers-color-scheme: light)',
};

// Tailwind-compatible responsive classes
export const responsiveClasses = {
  // Grid columns by breakpoint
  gridCols: {
    mobile: 'grid-cols-1',
    tablet: 'md:grid-cols-2',
    desktop: 'lg:grid-cols-3',
    wide: 'xl:grid-cols-4',
  },
  
  // Flex direction by breakpoint
  flexDirection: {
    stackOnMobile: 'flex-col md:flex-row',
    reverseOnMobile: 'flex-col-reverse md:flex-row',
  },
  
  // Visibility
  visibility: {
    mobileOnly: 'block md:hidden',
    tabletUp: 'hidden md:block',
    desktopOnly: 'hidden lg:block',
    hideOnMobile: 'hidden sm:block',
  },
  
  // Spacing
  padding: {
    page: 'px-4 sm:px-6 lg:px-8',
    section: 'py-8 sm:py-12 lg:py-16',
    card: 'p-4 sm:p-6',
  },
  
  // Text size
  text: {
    heading: 'text-2xl sm:text-3xl lg:text-4xl',
    subheading: 'text-lg sm:text-xl lg:text-2xl',
    body: 'text-sm sm:text-base',
  },
};

// Hook for checking breakpoints in React
export const useBreakpoint = () => {
  if (typeof window === 'undefined') return 'lg';
  
  const width = window.innerWidth;
  if (width < 640) return 'xs';
  if (width < 768) return 'sm';
  if (width < 1024) return 'md';
  if (width < 1280) return 'lg';
  if (width < 1536) return 'xl';
  return '2xl';
};

export const isMobile = () => {
  if (typeof window === 'undefined') return false;
  return window.innerWidth < 768;
};

export const isTablet = () => {
  if (typeof window === 'undefined') return false;
  return window.innerWidth >= 768 && window.innerWidth < 1024;
};

export const isDesktop = () => {
  if (typeof window === 'undefined') return true;
  return window.innerWidth >= 1024;
};

export default { breakpoints, mediaQueries, responsiveClasses };
