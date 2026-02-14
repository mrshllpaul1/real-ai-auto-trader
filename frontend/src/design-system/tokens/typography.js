/**
 * Design System - Typography Tokens
 * Font scales and text styles
 */

export const fontFamily = {
  sans: ['Inter', 'system-ui', 'sans-serif'].join(', '),
  mono: ['JetBrains Mono', 'Menlo', 'monospace'].join(', '),
  heading: ['Chivo', 'Inter', 'system-ui', 'sans-serif'].join(', '),
};

export const fontSize = {
  xs: ['0.75rem', { lineHeight: '1rem' }],        // 12px
  sm: ['0.875rem', { lineHeight: '1.25rem' }],    // 14px
  base: ['1rem', { lineHeight: '1.5rem' }],       // 16px
  lg: ['1.125rem', { lineHeight: '1.75rem' }],    // 18px
  xl: ['1.25rem', { lineHeight: '1.75rem' }],     // 20px
  '2xl': ['1.5rem', { lineHeight: '2rem' }],      // 24px
  '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
  '4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px
  '5xl': ['3rem', { lineHeight: '1' }],           // 48px
  '6xl': ['3.75rem', { lineHeight: '1' }],        // 60px
};

export const fontWeight = {
  thin: '100',
  light: '300',
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  extrabold: '800',
  black: '900',
};

// Predefined text styles
export const textStyles = {
  // Headings
  h1: {
    fontFamily: fontFamily.heading,
    fontSize: '2.25rem',
    fontWeight: fontWeight.bold,
    lineHeight: '2.5rem',
    letterSpacing: '-0.02em',
  },
  h2: {
    fontFamily: fontFamily.heading,
    fontSize: '1.875rem',
    fontWeight: fontWeight.semibold,
    lineHeight: '2.25rem',
    letterSpacing: '-0.01em',
  },
  h3: {
    fontFamily: fontFamily.heading,
    fontSize: '1.5rem',
    fontWeight: fontWeight.semibold,
    lineHeight: '2rem',
  },
  h4: {
    fontFamily: fontFamily.heading,
    fontSize: '1.25rem',
    fontWeight: fontWeight.medium,
    lineHeight: '1.75rem',
  },
  
  // Body text
  bodyLarge: {
    fontFamily: fontFamily.sans,
    fontSize: '1.125rem',
    fontWeight: fontWeight.normal,
    lineHeight: '1.75rem',
  },
  body: {
    fontFamily: fontFamily.sans,
    fontSize: '1rem',
    fontWeight: fontWeight.normal,
    lineHeight: '1.5rem',
  },
  bodySmall: {
    fontFamily: fontFamily.sans,
    fontSize: '0.875rem',
    fontWeight: fontWeight.normal,
    lineHeight: '1.25rem',
  },
  
  // Data/Numbers
  dataLarge: {
    fontFamily: fontFamily.mono,
    fontSize: '1.5rem',
    fontWeight: fontWeight.semibold,
    lineHeight: '2rem',
    fontVariantNumeric: 'tabular-nums',
  },
  data: {
    fontFamily: fontFamily.mono,
    fontSize: '1rem',
    fontWeight: fontWeight.medium,
    lineHeight: '1.5rem',
    fontVariantNumeric: 'tabular-nums',
  },
  dataSmall: {
    fontFamily: fontFamily.mono,
    fontSize: '0.875rem',
    fontWeight: fontWeight.normal,
    lineHeight: '1.25rem',
    fontVariantNumeric: 'tabular-nums',
  },
  
  // Labels
  label: {
    fontFamily: fontFamily.sans,
    fontSize: '0.875rem',
    fontWeight: fontWeight.medium,
    lineHeight: '1rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  
  // Caption
  caption: {
    fontFamily: fontFamily.sans,
    fontSize: '0.75rem',
    fontWeight: fontWeight.normal,
    lineHeight: '1rem',
    color: 'var(--muted-foreground)',
  },
};

export default { fontFamily, fontSize, fontWeight, textStyles };
