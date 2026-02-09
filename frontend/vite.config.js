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
