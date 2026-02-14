/**
 * Design System - Index
 * Export all design tokens and utilities
 */

export * from './tokens/colors';
export * from './tokens/spacing';
export * from './tokens/typography';
export * from './tokens/breakpoints';

// Re-export defaults
import colors, { gradients } from './tokens/colors';
import spacing, { componentSpacing } from './tokens/spacing';
import typography from './tokens/typography';
import breakpoints from './tokens/breakpoints';

export const designTokens = {
  colors,
  gradients,
  spacing,
  componentSpacing,
  typography,
  breakpoints,
};

export default designTokens;
