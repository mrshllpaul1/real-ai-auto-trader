/**
 * Enhanced useDataLoader Hook
 * ============================
 * Integrates with BackgroundLoader for priority-based data fetching.
 * Provides progressive loading, background sync, and prefetching.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { reportApiError } from '../services/errorReporting';
import { getBackgroundLoader, Priority } from '../services/backgroundLoader';

/**
 * Enhanced hook for loading data with priority support
 * @param {Function} fetchFn - Async function to fetch data
 * @param {Object} options - Configuration options
 * @returns {Object} - { data, loading, error, refetch, setData, ...}
 */
export const useDataLoader = (fetchFn, options = {}) => {
  const {
    initialData = null,
    autoFetch = true,
    dependencies = [],
    onSuccess = null,
    onError = null,
    priority = Priority.MEDIUM,
    cacheKey = null,
    backgroundSync = false,
    syncInterval = 60000,
    progressiveLoad = false,
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState(null);
  const [fetchCount, setFetchCount] = useState(0);
  const [progress, setProgress] = useState(0);
  
  const backgroundLoader = useRef(null);
  const syncId = useRef(null);

  useEffect(() => {
    backgroundLoader.current = getBackgroundLoader();
  }, []);

  const fetch = useCallback(async (showLoading = true, requestPriority = priority) => {
    if (showLoading) setLoading(true);
    setError(null);
    
    // Progressive loading simulation
    if (progressiveLoad) {
      setProgress(0);
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 10, 90));
      }, 100);
      
      try {
        const result = await backgroundLoader.current.addRequest(fetchFn, {
          priority: requestPriority,
          id: cacheKey ? `fetch_${cacheKey}` : undefined,
        });
        
        clearInterval(progressInterval);
        setProgress(100);
        
        setData(result);
        if (onSuccess) onSuccess(result);
        
        setTimeout(() => setProgress(0), 500);
        return result;
      } catch (err) {
        clearInterval(progressInterval);
        setProgress(0);
        setError(err);
        reportApiError(err, cacheKey || 'unknown_endpoint', fetchCount);
        if (onError) onError(err);
        throw err;
      } finally {
        setLoading(false);
        setFetchCount(prev => prev + 1);
      }
    } else {
      try {
        const result = await backgroundLoader.current.addRequest(fetchFn, {
          priority: requestPriority,
          id: cacheKey ? `fetch_${cacheKey}` : undefined,
        });
        
        setData(result);
        if (onSuccess) onSuccess(result);
        return result;
      } catch (err) {
        setError(err);
        reportApiError(err, cacheKey || 'unknown_endpoint', fetchCount);
        if (onError) onError(err);
        throw err;
      } finally {
        setLoading(false);
        setFetchCount(prev => prev + 1);
      }
    }
  }, [fetchFn, onSuccess, onError, cacheKey, fetchCount, priority, progressiveLoad]);

  const refetch = useCallback(() => fetch(true), [fetch]);
  const silentRefetch = useCallback(() => fetch(false), [fetch]);
  const priorityRefetch = useCallback((pri) => fetch(true, pri), [fetch]);

  useEffect(() => {
    if (autoFetch) {
      fetch(true).catch(() => {});
    }
  }, [...dependencies, autoFetch]);

  // Setup background sync if requested
  useEffect(() => {
    if (backgroundSync && cacheKey && backgroundLoader.current) {
      syncId.current = `sync_${cacheKey}`;
      backgroundLoader.current.startBackgroundSync(
        syncId.current,
        fetchFn,
        { interval: syncInterval, priority: Priority.LOW }
      );
      
      return () => {
        if (syncId.current) {
          backgroundLoader.current.stopBackgroundSync(syncId.current);
        }
      };
    }
  }, [backgroundSync, cacheKey, fetchFn, syncInterval]);

  return {
    data,
    loading,
    error,
    refetch,
    silentRefetch,
    priorityRefetch,
    setData,
    progress,
    isFirstLoad: fetchCount === 0 && loading,
  };
};

/**
 * Hook for prefetching data with low priority
 * @param {Function} fetchFn - Async function to fetch data
 * @param {Object} options - Prefetch options
 */
export const usePrefetch = (fetchFn, options = {}) => {
  const {
    dependencies = [],
    delay = 0,
    condition = true,
  } = options;
  
  const backgroundLoader = useRef(null);
  
  useEffect(() => {
    backgroundLoader.current = getBackgroundLoader();
  }, []);
  
  useEffect(() => {
    if (!condition) return;
    
    const timer = setTimeout(() => {
      if (backgroundLoader.current) {
        backgroundLoader.current.addRequest(fetchFn, {
          priority: Priority.IDLE,
          cancelable: true,
        }).catch(() => {});
      }
    }, delay);
    
    return () => clearTimeout(timer);
  }, [...dependencies, condition, delay]);
};

/**
 * Hook for background data synchronization
 * @param {string} id - Unique sync identifier
 * @param {Function} fetchFn - Async function to fetch data
 * @param {Object} options - Sync options
 * @returns {Object} - { data, error, lastSync }
 */
export const useBackgroundSync = (id, fetchFn, options = {}) => {
  const {
    interval = 60000,
    priority = Priority.LOW,
    enabled = true,
    onUpdate = null,
  } = options;
  
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [lastSync, setLastSync] = useState(null);
  
  const backgroundLoader = useRef(null);
  
  useEffect(() => {
    backgroundLoader.current = getBackgroundLoader();
  }, []);
  
  useEffect(() => {
    if (!enabled || !backgroundLoader.current) return;
    
    const wrappedFetchFn = async () => {
      try {
        const result = await fetchFn();
        setData(result);
        setError(null);
        setLastSync(new Date());
        if (onUpdate) onUpdate(result);
        return result;
      } catch (err) {
        setError(err);
        throw err;
      }
    };
    
    backgroundLoader.current.startBackgroundSync(id, wrappedFetchFn, {
      interval,
      priority,
    });
    
    return () => {
      if (backgroundLoader.current) {
        backgroundLoader.current.stopBackgroundSync(id);
      }
    };
  }, [id, fetchFn, interval, priority, enabled, onUpdate]);
  
  return { data, error, lastSync };
};

/**
 * Hook for progressive data loading with chunks
 * @param {Function} fetchFn - Function that returns chunks of data
 * @param {Object} options - Options
 * @returns {Object} - { data, loading, error, loadMore, hasMore }
 */
export const useProgressiveLoader = (fetchFn, options = {}) => {
  const {
    chunkSize = 20,
    initialChunks = 1,
    priority = Priority.MEDIUM,
  } = options;
  
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  
  const backgroundLoader = useRef(null);
  
  useEffect(() => {
    backgroundLoader.current = getBackgroundLoader();
  }, []);
  
  const loadChunk = useCallback(async (chunkIndex) => {
    if (!backgroundLoader.current) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await backgroundLoader.current.addRequest(
        () => fetchFn(chunkIndex, chunkSize),
        { priority, id: `chunk_${chunkIndex}` }
      );
      
      if (result && result.length > 0) {
        setData(prev => [...prev, ...result]);
        setHasMore(result.length === chunkSize);
        setCurrentChunk(chunkIndex);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchFn, chunkSize, priority]);
  
  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      loadChunk(currentChunk + 1);
    }
  }, [loading, hasMore, currentChunk, loadChunk]);
  
  // Load initial chunks
  useEffect(() => {
    const loadInitial = async () => {
      for (let i = 0; i < initialChunks; i++) {
        await loadChunk(i);
      }
    };
    loadInitial();
  }, []);
  
  return { data, loading, error, loadMore, hasMore, currentChunk };
};

export default useDataLoader;
