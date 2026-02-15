const DEFAULT_BACKEND_URL = 'http://localhost:8000';

export const getBackendUrl = () => {
  // Browser runtime overrides (e.g., injected during deployment)
  if (typeof window !== 'undefined') {
    const runtimeUrl = window.__RUNTIME_CONFIG__?.REACT_APP_BACKEND_URL;
    if (runtimeUrl) {
      return runtimeUrl;
    }
  }

  // Prefer Vite's VITE_BACKEND_URL, fall back to legacy REACT_APP_BACKEND_URL
  const viteUrl = import.meta.env?.VITE_BACKEND_URL || import.meta.env?.REACT_APP_BACKEND_URL;
  if (viteUrl) {
    return viteUrl;
  }

  return DEFAULT_BACKEND_URL;
};

export const getApiBaseUrl = () => {
  const normalizedUrl = getBackendUrl().replace(/\/$/, '');
  return `${normalizedUrl}/api`;
};
