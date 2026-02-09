import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'build',
    sourcemap: false,
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
    allowedHosts: 'all', // Allow all hosts for deployment
  },
});
