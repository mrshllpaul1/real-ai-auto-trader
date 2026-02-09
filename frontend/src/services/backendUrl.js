const DEFAULT_BACKEND_URL = 'http://localhost:8000';

export const getBackendUrl = () => {
  if (typeof window !== 'undefined') {
    const runtimeUrl = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL;
    if (runtimeUrl) {
      return runtimeUrl;
    }
  }

  const viteUrl = import.meta.env?.VITE_BACKEND_URL || import.meta.env?.REACT_APP_BACKEND_URL;
  if (viteUrl) {
    return viteUrl;
  }

  if (typeof process !== 'undefined' && process.env?.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }

  return DEFAULT_BACKEND_URL;
};

export const getApiBaseUrl = () => {
  const backendUrl = getBackendUrl();
  const normalizedUrl = backendUrl?.replace(/\/$/, '');
  return normalizedUrl ? `${normalizedUrl}/api` : '/api';
};
