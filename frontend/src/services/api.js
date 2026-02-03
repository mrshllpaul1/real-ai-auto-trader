import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  timeout: 30000,  // Increased timeout for slow API calls
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add user_id to requests (in production, use proper auth)
    config.params = {
      ...config.params,
      user_id: localStorage.getItem('user_id') || 'demo_user'
    };
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  storeCredentials: (api_key, api_secret) =>
    api.post('/auth/store-credentials', { api_key, api_secret }),
  checkCredentials: () => api.get('/auth/check-credentials'),
};

// Trading APIs
export const tradingAPI = {
  executeTrade: (data) => api.post('/trading/execute', data),
  getTradeHistory: (mode = 'all', limit = 100) =>
    api.get(`/trading/history/${localStorage.getItem('user_id') || 'demo_user'}`, {
      params: { mode, limit }
    }),
  getPortfolio: () => api.get(`/trading/portfolio/${localStorage.getItem('user_id') || 'demo_user'}`),
  getKrakenPortfolio: () => api.get('/trading/kraken/portfolio'),
  getKrakenTrades: (limit = 50) => api.get('/trading/kraken/trades', { params: { limit } }),
  getKrakenOrders: (limit = 50) => api.get('/trading/kraken/orders', { params: { limit } }),
};

// Strategy APIs
export const strategyAPI = {
  generateStrategies: (coin_pairs) =>
    api.post('/strategies/generate', {
      user_id: localStorage.getItem('user_id') || 'demo_user',
      coin_pairs
    }, { timeout: 90000 }),  // 90 second timeout for AI strategy generation
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
  getPrices: (coin_ids) => api.get('/market/prices', { params: { coin_ids } }),
  getHistoricalData: (coin_id, days = 30) =>
    api.get(`/market/historical/${coin_id}`, { params: { days } }),
  getTrendingCoins: () => api.get('/market/trending'),
  getCryptoNews: () => api.get('/market/news'),
};

// Risk Management APIs
export const riskAPI = {
  getSettings: () => api.get(`/risk/settings/${localStorage.getItem('user_id') || 'demo_user'}`),
  updateSettings: (settings) =>
    api.put(`/risk/settings/${localStorage.getItem('user_id') || 'demo_user'}`, settings),
};

export default api;