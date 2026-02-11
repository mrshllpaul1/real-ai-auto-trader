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
      // Performance optimizations
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          // Manual chunking for better code splitting
          manualChunks: {
            // Vendor chunk for core React dependencies
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            // Charts chunk for visualization libraries
            'vendor-charts': ['recharts', 'lightweight-charts'],
            // UI components chunk
            'vendor-ui': ['framer-motion', 'lucide-react', 'sonner'],
            // Date utilities
            'vendor-date': ['date-fns'],
          },
          // Optimize chunk file names
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash].[ext]',
        },
      },
      // Minification options
      minify: 'esbuild',
      target: 'es2020',
      // CSS code splitting
      cssCodeSplit: true,
    },
    // Optimize dependencies
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'recharts',
        'framer-motion',
        'lucide-react',
        'axios',
        'date-fns',
      ],
      // Exclude large dependencies that should be loaded on-demand
      exclude: ['lightweight-charts'],
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
  };
});
