import axios from 'axios';
import { CachedRequestBatcher } from '../utils/requestBatcher';

// Use environment variable for backend URL (required for deployment)
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

console.log('[API Service] Using backend URL:', BACKEND_URL);

// ============================================
// REQUEST BATCHING FOR 50-70% FEWER API CALLS
// ============================================

// Price batcher - batches multiple price requests into single API call
let priceBatcher = null;
const getPriceBatcher = () => {
  if (!priceBatcher) {
    priceBatcher = new CachedRequestBatcher(
      async (coinIds) => {
        try {
          const response = await axios.get(`${API}/market/prices`, {
            params: { coin_ids: coinIds.join(',') }
          });
          // Return prices keyed by coin ID
          return response.data;
        } catch (error) {
          console.error('[PriceBatcher] Error:', error);
          throw error;
        }
      },
      { delay: 50, maxBatchSize: 20, cacheTTL: 30000 } // 30s cache
    );
  }
  return priceBatcher;
};

// Get single coin price (batched)
export const getBatchedPrice = async (coinId) => {
  return getPriceBatcher().add(coinId, coinId);
};

// Get batcher stats
export const getPriceBatcherStats = () => {
  if (priceBatcher) {
    return {
      ...priceBatcher.getStats(),
      ...priceBatcher.getCacheStats()
    };
  }
  return { message: 'Batcher not initialized' };
};

// ============================================
// CACHING SYSTEM FOR IMPROVED PERFORMANCE
// ============================================
const cache = new Map();
const pendingRequests = new Map();
const CACHE_DURATION = {
  SHORT: 15000,    // 15 seconds - for rapidly changing data
  MEDIUM: 60000,   // 60 seconds - for moderately changing data
  LONG: 180000,    // 3 minutes - for slowly changing data
  STATIC: 600000,  // 10 minutes - for mostly static data
};

// Cache configuration for different endpoints
const CACHE_CONFIG = {
  '/market/prices': CACHE_DURATION.SHORT,
  '/market/trending': CACHE_DURATION.MEDIUM,
  '/tethys/status': CACHE_DURATION.SHORT,
  '/ensemble/status': CACHE_DURATION.MEDIUM,
  '/training/status': CACHE_DURATION.SHORT,
  '/training-progress/active': CACHE_DURATION.SHORT,
  '/universe/coins': CACHE_DURATION.STATIC,
  '/kraken-universe/coins': CACHE_DURATION.STATIC,
  '/coindesk/news': CACHE_DURATION.MEDIUM,
  '/coindesk/sentiment': CACHE_DURATION.MEDIUM,
  '/settings': CACHE_DURATION.STATIC,
  '/gems/top': CACHE_DURATION.MEDIUM,
  '/sound-settings': CACHE_DURATION.STATIC,
  '/email-digest': CACHE_DURATION.LONG,
  '/portfolio-share': CACHE_DURATION.MEDIUM,
  '/achievements': CACHE_DURATION.LONG,
  '/event-countdown': CACHE_DURATION.MEDIUM,
  '/ai-explain': CACHE_DURATION.LONG,
};

const getCacheKey = (config) => {
  const params = config.params ? JSON.stringify(config.params) : '';
  return `${config.method}:${config.url}:${params}`;
};

const getCacheDuration = (url) => {
  for (const [pattern, duration] of Object.entries(CACHE_CONFIG)) {
    if (url.includes(pattern)) return duration;
  }
  return null; // No caching
};

const getFromCache = (key) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < cached.duration) {
    return cached.data;
  }
  cache.delete(key);
  return null;
};

const setCache = (key, data, duration) => {
  cache.set(key, { data, timestamp: Date.now(), duration });
  
  // Cleanup old entries if cache gets too large
  if (cache.size > 100) {
    const now = Date.now();
    for (const [k, v] of cache.entries()) {
      if (now - v.timestamp > v.duration) cache.delete(k);
    }
  }
};

// Request deduplication - prevent duplicate concurrent requests
const deduplicateRequest = async (key, requestFn) => {
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key);
  }
  
  const promise = requestFn().finally(() => {
    pendingRequests.delete(key);
  });
  
  pendingRequests.set(key, promise);
  return promise;
};

// ============================================
// AXIOS INSTANCE WITH OPTIMIZATIONS
// ============================================
const api = axios.create({
  baseURL: API,
  timeout: 30000, // Reduced to 30 seconds for faster failure detection
});

// Request interceptor with performance tracking
api.interceptors.request.use(
  (config) => {
    config.params = {
      ...config.params,
      user_id: localStorage.getItem('user_id') || 'demo_user'
    };
    config._startTime = Date.now();
    return config;
  },
  (error) => Promise.reject(error)
);

// ============================================
// RETRY LOGIC WITH EXPONENTIAL BACKOFF
// ============================================
import { reportApiError } from './errorReporting';

const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  retryableStatuses: [408, 429, 500, 502, 503, 504],
  retryableMethods: ['get', 'head', 'options', 'put', 'delete'],
};

/**
 * Calculate delay with exponential backoff and jitter
 */
const calculateDelay = (attempt) => {
  const exponentialDelay = RETRY_CONFIG.baseDelay * Math.pow(2, attempt);
  const jitter = Math.random() * 1000;
  return Math.min(exponentialDelay + jitter, RETRY_CONFIG.maxDelay);
};

/**
 * Check if request should be retried
 */
const shouldRetry = (error, config) => {
  // Don't retry if max retries exceeded
  const retryCount = config._retryCount || 0;
  if (retryCount >= RETRY_CONFIG.maxRetries) return false;
  
  // Don't retry non-retryable methods (unless idempotent)
  if (!RETRY_CONFIG.retryableMethods.includes(config.method?.toLowerCase())) {
    return false;
  }
  
  // Retry on network errors
  if (!error.response) return true;
  
  // Retry on specific status codes
  return RETRY_CONFIG.retryableStatuses.includes(error.response.status);
};

/**
 * Wait for specified milliseconds
 */
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Retry wrapper for API calls
 */
const withRetry = async (requestFn, config = {}) => {
  let lastError;
  const startTime = Date.now();
  
  for (let attempt = 0; attempt <= RETRY_CONFIG.maxRetries; attempt++) {
    try {
      const response = await requestFn();
      
      // Log if this was a retry that succeeded
      if (attempt > 0) {
        console.log(`[API Retry] Success after ${attempt} retries: ${config.url}`);
      }
      
      return response;
    } catch (error) {
      lastError = error;
      const retryConfig = { ...config, _retryCount: attempt };
      
      if (shouldRetry(error, retryConfig)) {
        const delay = calculateDelay(attempt);
        console.warn(
          `[API Retry] Attempt ${attempt + 1}/${RETRY_CONFIG.maxRetries} for ${config.url} ` +
          `(${error.response?.status || 'network error'}). Waiting ${delay}ms...`
        );
        await wait(delay);
      } else {
        // Report error if not retrying
        reportApiError(error, config.url, attempt);
        break;
      }
    }
  }
  
  // All retries failed
  const totalTime = Date.now() - startTime;
  console.error(`[API Retry] All retries failed for ${config.url} after ${totalTime}ms`);
  reportApiError(lastError, config.url, RETRY_CONFIG.maxRetries);
  throw lastError;
};

// Response interceptor with caching and performance logging
api.interceptors.response.use(
  (response) => {
    // Log slow requests for debugging
    const duration = Date.now() - (response.config._startTime || Date.now());
    if (duration > 2000) {
      console.warn(`[API Slow] ${response.config.url} took ${duration}ms`);
    }
    
    // Cache GET responses (only if not a forced refresh)
    if (response.config.method === 'get' && !response.config._skipCache) {
      const cacheDuration = getCacheDuration(response.config.url);
      if (cacheDuration) {
        const cacheKey = getCacheKey(response.config);
        setCache(cacheKey, response, cacheDuration);
      }
    }
    return response;
  },
  async (error) => {
    const config = error.config || {};
    
    // Check if we should retry
    if (shouldRetry(error, config)) {
      const retryCount = (config._retryCount || 0) + 1;
      config._retryCount = retryCount;
      
      const delay = calculateDelay(retryCount - 1);
      console.warn(
        `[API Retry] Attempt ${retryCount}/${RETRY_CONFIG.maxRetries} for ${config.url} ` +
        `(${error.response?.status || 'network error'}). Waiting ${delay}ms...`
      );
      
      await wait(delay);
      return api.request(config);
    }
    
    // Report non-retryable errors
    reportApiError(error, config.url, config._retryCount || 0);
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Wrapper for cached GET requests with cache-first strategy
const cachedGet = async (url, config = {}) => {
  const fullConfig = { ...config, url, method: 'get' };
  const cacheKey = getCacheKey(fullConfig);
  const duration = getCacheDuration(url);
  
  // Return cached if available and not forcing refresh
  if (duration && !config._skipCache) {
    const cached = getFromCache(cacheKey);
    if (cached) {
      console.log('[API Cache] Hit:', url);
      return cached;
    }
  }
  
  // Deduplicate concurrent requests
  return deduplicateRequest(cacheKey, () => api.get(url, config));
};

// Force refresh - bypasses cache
export const forceRefresh = async (url, config = {}) => {
  // Clear cache for this URL pattern
  clearCache(url);
  // Make request with skip cache flag
  return api.get(url, { ...config, _skipCache: true });
};

// Clear cache utility
export const clearCache = (pattern = null) => {
  if (pattern) {
    for (const key of cache.keys()) {
      if (key.includes(pattern)) cache.delete(key);
    }
  } else {
    cache.clear();
  }
  console.log('[API Cache] Cleared:', pattern || 'all');
};

// Clear all cache and force refresh
export const clearAllCacheAndRefresh = () => {
  cache.clear();
  pendingRequests.clear();
  console.log('[API Cache] All cache cleared');
};

// Preload critical data
export const preloadCriticalData = async () => {
  const criticalEndpoints = [
    '/tethys/status',
    '/universe/coins',
    '/training-progress/active',
  ];
  
  await Promise.allSettled(
    criticalEndpoints.map(endpoint => cachedGet(endpoint))
  );
};

// ============================================
// API EXPORTS
// ============================================

// Auth APIs
export const authAPI = {
  storeCredentials: (api_key, api_secret) =>
    api.post('/auth/store-credentials', { api_key, api_secret }),
  checkCredentials: () => cachedGet('/auth/check-credentials'),
  findKrakenKeys: () => api.get('/auth/kraken/find-keys'),
};

// Trading APIs
export const tradingAPI = {
  executeTrade: (data) => api.post('/trading/execute', data),
  getTradeHistory: (mode = 'all', limit = 100) =>
    api.get(`/trading/history/${localStorage.getItem('user_id') || 'demo_user'}`, {
      params: { mode, limit }
    }),
  getPortfolio: () => api.get(`/trading/portfolio/${localStorage.getItem('user_id') || 'demo_user'}`),
  getKrakenPortfolio: () => cachedGet('/trading/kraken/portfolio'),
  getKrakenTrades: (limit = 50) => api.get('/trading/kraken/trades', { params: { limit } }),
  getKrakenOrders: (limit = 50) => api.get('/trading/kraken/orders', { params: { limit } }),
};

// Strategy APIs
export const strategyAPI = {
  generateStrategies: (coin_pairs) =>
    api.post('/strategies/generate', {
      user_id: localStorage.getItem('user_id') || 'demo_user',
      coin_pairs
    }, { timeout: 90000 }),
  getStrategies: (status = 'active', limit = 10) =>
    api.get(`/strategies/list/${localStorage.getItem('user_id') || 'demo_user'}`, {
      params: { status, limit }
    }),
  getStrategyDetail: (strategy_id) => api.get(`/strategies/detail/${strategy_id}`),
  activateStrategy: (strategy_id) =>
    api.post(`/strategies/activate/${strategy_id}`, null, {
      params: { user_id: localStorage.getItem('user_id') || 'demo_user' }
    }),
  deactivateStrategy: (strategy_id) =>
    api.post(`/strategies/deactivate/${strategy_id}`, null, {
      params: { user_id: localStorage.getItem('user_id') || 'demo_user' }
    }),
};

// Market Data APIs
export const marketAPI = {
  getPrices: (coin_ids) => cachedGet('/market/prices', { params: { coin_ids } }),
  getHistoricalData: (coin_id, days = 30) =>
    cachedGet(`/market/historical/${coin_id}`, { params: { days } }),
  getTrendingCoins: () => cachedGet('/market/trending'),
  getCryptoNews: () => cachedGet('/market/news'),
};

// CoinDesk News APIs
export const coindeskAPI = {
  getNews: (limit = 20, lang = 'EN') => cachedGet('/coindesk/news', { params: { limit, lang } }),
  getCoinNews: (symbol, limit = 10) => cachedGet(`/coindesk/news/coin/${symbol}`, { params: { limit } }),
  getSentiment: () => cachedGet('/coindesk/sentiment'),
  getNewsBySentiment: (sentiment, limit = 10) => cachedGet(`/coindesk/news/sentiment/${sentiment}`, { params: { limit } }),
  getStatus: () => cachedGet('/coindesk/status'),
  getCategories: () => cachedGet('/coindesk/categories'),
};

// Risk Management APIs
export const riskAPI = {
  getSettings: () => cachedGet(`/risk/settings/${localStorage.getItem('user_id') || 'demo_user'}`),
  updateSettings: (settings) =>
    api.put(`/risk/settings/${localStorage.getItem('user_id') || 'demo_user'}`, settings),
};

export default api;