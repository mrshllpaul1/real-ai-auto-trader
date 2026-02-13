/**
 * useDataLoader Hook
 * Consistent data loading with skeleton states and error handling
 */

import { useState, useEffect, useCallback } from 'react';
import { reportApiError } from '../services/errorReporting';

/**
 * Hook for loading data with automatic skeleton/error states
 * @param {Function} fetchFn - Async function to fetch data
 * @param {Object} options - Configuration options
 * @returns {Object} - { data, loading, error, refetch, setData }
 */
export const useDataLoader = (fetchFn, options = {}) => {
  const {
    initialData = null,
    autoFetch = true,
    dependencies = [],
    onSuccess = null,
    onError = null,
    retryCount = 0,
    cacheKey = null,
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState(null);
  const [fetchCount, setFetchCount] = useState(0);

  const fetch = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
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
  }, [fetchFn, onSuccess, onError, cacheKey, fetchCount]);

  const refetch = useCallback(() => fetch(true), [fetch]);
  const silentRefetch = useCallback(() => fetch(false), [fetch]);

  useEffect(() => {
    if (autoFetch) {
      fetch(true).catch(() => {});
    }
  }, [...dependencies, autoFetch]);

  return {
    data,
    loading,
    error,
    refetch,
    silentRefetch,
    setData,
    isFirstLoad: fetchCount === 0 && loading,
  };
};

/**
 * Hook for loading multiple data sources in parallel
 * @param {Object} loaders - Object with loader configs { key: { fetch, options } }
 * @returns {Object} - Combined state for all loaders
 */
export const useMultiDataLoader = (loaders) => {
  const results = {};
  let anyLoading = false;
  let anyError = null;

  for (const [key, config] of Object.entries(loaders)) {
    const { fetch: fetchFn, ...options } = config;
    const result = useDataLoader(fetchFn, options);
    results[key] = result;
    if (result.loading) anyLoading = true;
    if (result.error && !anyError) anyError = result.error;
  }

  const refetchAll = useCallback(async () => {
    const promises = Object.values(results).map(r => r.refetch().catch(() => {}));
    await Promise.all(promises);
  }, [results]);

  return {
    ...results,
    anyLoading,
    anyError,
    refetchAll,
  };
};

/**
 * Hook for infinite scroll / pagination
 * @param {Function} fetchFn - Async function that takes (page, limit) params
 * @param {Object} options - Configuration options
 */
export const usePaginatedLoader = (fetchFn, options = {}) => {
  const {
    pageSize = 20,
    initialPage = 1,
    onSuccess = null,
  } = options;

  const [data, setData] = useState([]);
  const [page, setPage] = useState(initialPage);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  const fetchPage = useCallback(async (pageNum, append = false) => {
    const isFirstPage = pageNum === initialPage;
    if (isFirstPage) setLoading(true);
    else setLoadingMore(true);
    setError(null);

    try {
      const result = await fetchFn(pageNum, pageSize);
      const items = result.items || result.data || result;
      
      setData(prev => append ? [...prev, ...items] : items);
      setHasMore(items.length === pageSize);
      setPage(pageNum);
      if (onSuccess) onSuccess(items);
      return items;
    } catch (err) {
      setError(err);
      reportApiError(err, 'paginated_load');
      throw err;
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [fetchFn, pageSize, initialPage, onSuccess]);

  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore) {
      fetchPage(page + 1, true).catch(() => {});
    }
  }, [fetchPage, page, loadingMore, hasMore]);

  const refresh = useCallback(() => {
    setData([]);
    fetchPage(initialPage, false).catch(() => {});
  }, [fetchPage, initialPage]);

  // Initial load
  useEffect(() => {
    fetchPage(initialPage, false).catch(() => {});
  }, []);

  return {
    data,
    loading,
    loadingMore,
    error,
    hasMore,
    loadMore,
    refresh,
    page,
  };
};

export default useDataLoader;
