import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    define: {
      // Map environment variables properly for browser
      'process.env': {
        VITE_BACKEND_URL: JSON.stringify(env.VITE_BACKEND_URL),
        REACT_APP_BACKEND_URL: JSON.stringify(env.REACT_APP_BACKEND_URL || env.VITE_BACKEND_URL),
      },
    },
    build: {
      outDir: 'build',
      sourcemap: false,
      // Enable code splitting and chunk optimization
      rollupOptions: {
        output: {
          // Manual chunk splitting for better caching
          manualChunks: {
            // Core vendor libraries
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            // UI component libraries
            'vendor-ui': [
              '@radix-ui/react-dialog',
              '@radix-ui/react-dropdown-menu',
              '@radix-ui/react-select',
              '@radix-ui/react-tabs',
              '@radix-ui/react-toast',
              '@radix-ui/react-tooltip',
              '@radix-ui/react-switch',
              '@radix-ui/react-slider',
              '@radix-ui/react-label',
              '@radix-ui/react-checkbox',
              '@radix-ui/react-radio-group',
              '@radix-ui/react-progress'
            ],
            // Animation libraries
            'vendor-animation': ['framer-motion'],
            // Chart libraries (lazy loaded but separate chunk)
            'vendor-charts': ['recharts', 'lightweight-charts'],
            // Form libraries
            'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
            // Utility libraries
            'vendor-utils': ['axios', 'clsx', 'tailwind-merge', 'date-fns', 'lucide-react']
          },
          // Optimize chunk naming for caching
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
        }
      },
      // Chunk size warnings
      chunkSizeWarningLimit: 1000,
      // Minification settings
      minify: 'esbuild',
      target: 'es2015',
      // Enable CSS code splitting
      cssCodeSplit: true
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      allowedHosts: [
        'deploy-rescue-43.preview.emergentagent.com',
        '.emergentagent.com',
        '.preview.emergentagent.com',
        'localhost',
        '.sslip.io'
      ],
      // Performance optimizations
      hmr: {
        overlay: true
      },
      // Faster file watching
      watch: {
        usePolling: false
      }
    },
    preview: {
      port: 3000,
      host: '0.0.0.0',
      allowedHosts: [
        'deploy-rescue-43.preview.emergentagent.com',
        '.emergentagent.com',
        '.preview.emergentagent.com',
        'localhost',
        '.sslip.io'
      ],
    },
    // Performance optimizations
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom'
      ],
      exclude: [
        'recharts',
        'lightweight-charts'
      ]
    }
  };
});
