/**
 * Custom hook for fetching and caching Kraken trading pairs
 * Use this hook in any component that needs the trading pair dropdown
 */
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

// Cache the pairs to avoid refetching
let cachedPairs = null;
let cacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export const useTradingPairs = () => {
  const [pairs, setPairs] = useState(cachedPairs || []);
  const [loading, setLoading] = useState(!cachedPairs);
  const [error, setError] = useState(null);

  const fetchPairs = useCallback(async (forceRefresh = false) => {
    // Check cache
    if (!forceRefresh && cachedPairs && cacheTimestamp && (Date.now() - cacheTimestamp < CACHE_DURATION)) {
      setPairs(cachedPairs);
      setLoading(false);
      return cachedPairs;
    }

    try {
      setLoading(true);
      const response = await api.get('/spot/pairs/all');
      const fetchedPairs = response.data?.pairs || [];
      
      // Update cache
      cachedPairs = fetchedPairs;
      cacheTimestamp = Date.now();
      
      setPairs(fetchedPairs);
      setError(null);
      return fetchedPairs;
    } catch (err) {
      console.error('Failed to fetch trading pairs:', err);
      setError(err.message || 'Failed to fetch trading pairs');
      
      // Return fallback pairs if API fails
      const fallbackPairs = [
        { symbol: 'BTC', display: 'BTC/USD', pair: 'XXBTZUSD' },
        { symbol: 'ETH', display: 'ETH/USD', pair: 'XETHZUSD' },
        { symbol: 'SOL', display: 'SOL/USD', pair: 'SOLUSD' },
        { symbol: 'XRP', display: 'XRP/USD', pair: 'XXRPZUSD' },
        { symbol: 'ADA', display: 'ADA/USD', pair: 'ADAUSD' },
        { symbol: 'DOGE', display: 'DOGE/USD', pair: 'XDGUSD' },
        { symbol: 'DOT', display: 'DOT/USD', pair: 'DOTUSD' },
        { symbol: 'LINK', display: 'LINK/USD', pair: 'LINKUSD' },
        { symbol: 'AVAX', display: 'AVAX/USD', pair: 'AVAXUSD' },
        { symbol: 'MATIC', display: 'MATIC/USD', pair: 'POLUSD' },
      ];
      setPairs(fallbackPairs);
      return fallbackPairs;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPairs();
  }, [fetchPairs]);

  // Helper to get pair options for Select component
  const getPairOptions = useCallback(() => {
    return pairs.map(p => ({
      value: `${p.symbol}/USD`,
      label: p.display || `${p.symbol}/USD`,
      symbol: p.symbol,
      pair: p.pair
    }));
  }, [pairs]);

  // Helper to search pairs
  const searchPairs = useCallback((query) => {
    if (!query) return pairs;
    const q = query.toUpperCase();
    return pairs.filter(p => 
      p.symbol.includes(q) || 
      (p.display && p.display.includes(q))
    );
  }, [pairs]);

  return {
    pairs,
    loading,
    error,
    refresh: fetchPairs,
    getPairOptions,
    searchPairs,
    totalCount: pairs.length
  };
};

export default useTradingPairs;
