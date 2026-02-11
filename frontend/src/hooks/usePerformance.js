/**
 * Performance Optimization Utilities for React
 * Provides hooks and utilities to optimize frontend performance
 */

import { useCallback, useEffect, useRef, useState, useMemo } from 'react';

/**
 * Debounce hook - delays execution until user stops typing/interacting
 * Useful for search boxes, real-time filters, etc.
 * 
 * @param {*} value - Value to debounce
 * @param {number} delay - Delay in milliseconds (default: 500ms)
 * @returns {*} Debounced value
 */
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Throttle hook - limits how often a function can be called
 * Useful for scroll handlers, resize handlers, etc.
 * 
 * @param {Function} callback - Function to throttle
 * @param {number} delay - Minimum time between calls in milliseconds
 * @returns {Function} Throttled function
 */
export function useThrottle(callback, delay = 1000) {
  const lastRan = useRef(Date.now());
  const timeoutRef = useRef(null);

  return useCallback(
    (...args) => {
      const now = Date.now();
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      if (now - lastRan.current >= delay) {
        callback(...args);
        lastRan.current = now;
      } else {
        timeoutRef.current = setTimeout(() => {
          callback(...args);
          lastRan.current = Date.now();
        }, delay - (now - lastRan.current));
      }
    },
    [callback, delay]
  );
}

/**
 * Lazy load hook - only load data when component becomes visible
 * Uses Intersection Observer API
 * 
 * @param {Object} options - Intersection Observer options
 * @returns {Array} [ref, isIntersecting]
 */
export function useLazyLoad(options = {}) {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true);
          // Once loaded, stop observing
          if (ref.current) {
            observer.unobserve(ref.current);
          }
        }
      },
      {
        threshold: 0.1,
        ...options
      }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [options]);

  return [ref, isIntersecting];
}

/**
 * Virtual scrolling hook for large lists
 * Only renders visible items to improve performance
 * 
 * @param {Array} items - All items in the list
 * @param {number} itemHeight - Height of each item in pixels
 * @param {number} containerHeight - Height of the container in pixels
 * @param {number} overscan - Number of extra items to render (default: 3)
 * @returns {Object} Scroll state and visible items
 */
export function useVirtualScroll(items, itemHeight, containerHeight, overscan = 3) {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(items.length, startIndex + visibleCount + overscan * 2);

  const visibleItems = useMemo(
    () => items.slice(startIndex, endIndex),
    [items, startIndex, endIndex]
  );

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    startIndex,
    endIndex
  };
}

/**
 * Memoize expensive computations
 * Wrapper around useMemo with dependency array optimization
 * 
 * @param {Function} factory - Function that computes the value
 * @param {Array} deps - Dependencies array
 * @returns {*} Memoized value
 */
export function useOptimizedMemo(factory, deps = []) {
  return useMemo(factory, deps);
}

/**
 * Batch state updates to reduce re-renders
 * Collects multiple state updates and applies them together
 * 
 * @param {Object} initialState - Initial state
 * @returns {Array} [state, batchUpdate, flushUpdates]
 */
export function useBatchState(initialState = {}) {
  const [state, setState] = useState(initialState);
  const pendingUpdates = useRef({});
  const timeoutRef = useRef(null);

  const flushUpdates = useCallback(() => {
    if (Object.keys(pendingUpdates.current).length > 0) {
      setState((prev) => ({
        ...prev,
        ...pendingUpdates.current
      }));
      pendingUpdates.current = {};
    }
  }, []);

  const batchUpdate = useCallback((updates) => {
    pendingUpdates.current = {
      ...pendingUpdates.current,
      ...updates
    };

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Flush after 16ms (roughly one frame)
    timeoutRef.current = setTimeout(flushUpdates, 16);
  }, [flushUpdates]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return [state, batchUpdate, flushUpdates];
}

/**
 * Performance monitoring hook
 * Tracks render count and timing
 * 
 * @param {string} componentName - Name of the component to monitor
 */
export function usePerformanceMonitor(componentName) {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(Date.now());

  useEffect(() => {
    renderCount.current += 1;
    const now = Date.now();
    const timeSinceLastRender = now - lastRenderTime.current;
    lastRenderTime.current = now;

    if (process.env.NODE_ENV === 'development') {
      console.log(
        `[Performance] ${componentName} - Render #${renderCount.current} (${timeSinceLastRender}ms since last render)`
      );
    }
  });
}

/**
 * Optimize WebSocket updates by batching messages
 * Prevents too many re-renders from rapid updates
 * 
 * @param {WebSocket} ws - WebSocket instance
 * @param {Function} onMessage - Message handler
 * @param {number} batchInterval - Batching interval in ms (default: 100ms)
 */
export function useOptimizedWebSocket(ws, onMessage, batchInterval = 100) {
  const messageQueue = useRef([]);
  const timeoutRef = useRef(null);

  const flushMessages = useCallback(() => {
    if (messageQueue.current.length > 0) {
      onMessage(messageQueue.current);
      messageQueue.current = [];
    }
  }, [onMessage]);

  useEffect(() => {
    if (!ws) return;

    const handleMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        messageQueue.current.push(data);

        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(flushMessages, batchInterval);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    ws.addEventListener('message', handleMessage);

    return () => {
      ws.removeEventListener('message', handleMessage);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      flushMessages();
    };
  }, [ws, flushMessages, batchInterval]);
}

/**
 * Cancel pending async operations on unmount
 * Prevents memory leaks and state updates after unmount
 */
export function useAbortController() {
  const abortControllerRef = useRef(null);

  useEffect(() => {
    abortControllerRef.current = new AbortController();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return abortControllerRef.current;
}

/**
 * Optimize image loading with lazy loading
 * 
 * @param {string} src - Image source URL
 * @param {string} placeholder - Placeholder image URL
 * @returns {Object} Image state
 */
export function useLazyImage(src, placeholder = '') {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [isLoading, setIsLoading] = useState(true);
  const [ref, isIntersecting] = useLazyLoad();

  useEffect(() => {
    if (isIntersecting && src) {
      const img = new Image();
      img.src = src;
      img.onload = () => {
        setImageSrc(src);
        setIsLoading(false);
      };
      img.onerror = () => {
        setIsLoading(false);
      };
    }
  }, [isIntersecting, src]);

  return { ref, imageSrc, isLoading };
}

/**
 * Request Animation Frame hook for smooth animations
 * 
 * @param {Function} callback - Animation callback
 * @param {boolean} isRunning - Whether animation should run
 */
export function useAnimationFrame(callback, isRunning = true) {
  const requestRef = useRef();
  const previousTimeRef = useRef();

  const animate = useCallback((time) => {
    if (previousTimeRef.current !== undefined) {
      const deltaTime = time - previousTimeRef.current;
      callback(deltaTime);
    }
    previousTimeRef.current = time;
    requestRef.current = requestAnimationFrame(animate);
  }, [callback]);

  useEffect(() => {
    if (isRunning) {
      requestRef.current = requestAnimationFrame(animate);
      return () => {
        if (requestRef.current) {
          cancelAnimationFrame(requestRef.current);
        }
      };
    }
  }, [isRunning, animate]);
}

export default {
  useDebounce,
  useThrottle,
  useLazyLoad,
  useVirtualScroll,
  useOptimizedMemo,
  useBatchState,
  usePerformanceMonitor,
  useOptimizedWebSocket,
  useAbortController,
  useLazyImage,
  useAnimationFrame
};
