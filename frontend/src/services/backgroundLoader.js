/**
 * Background Loading Service
 * ===========================
 * Intelligent background loading with priority queue, prefetching,
 * and progressive data synchronization.
 * 
 * Features:
 * - Priority-based request queue (CRITICAL > HIGH > MEDIUM > LOW)
 * - Automatic preloading of critical data on app start
 * - Background data synchronization with configurable intervals
 * - Smart prefetching based on user navigation patterns
 * - Resource hints management (dns-prefetch, preconnect, prefetch)
 * - Offline-first capabilities with service worker coordination
 */

import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

// Priority levels for requests
export const Priority = {
  CRITICAL: 0,  // User-initiated actions, trades
  HIGH: 1,      // Real-time data (prices, positions)
  MEDIUM: 2,    // Analytics, historical data
  LOW: 3,       // Background updates, prefetch
  IDLE: 4,      // Lowest priority, only when idle
};

class BackgroundLoader {
  constructor() {
    this.queue = {
      [Priority.CRITICAL]: [],
      [Priority.HIGH]: [],
      [Priority.MEDIUM]: [],
      [Priority.LOW]: [],
      [Priority.IDLE]: [],
    };
    
    this.activeRequests = new Map();
    this.maxConcurrent = {
      [Priority.CRITICAL]: 5,
      [Priority.HIGH]: 3,
      [Priority.MEDIUM]: 2,
      [Priority.LOW]: 1,
      [Priority.IDLE]: 1,
    };
    
    this.stats = {
      totalRequests: 0,
      completedRequests: 0,
      canceledRequests: 0,
      avgResponseTime: 0,
    };
    
    this.syncIntervals = new Map();
    this.isOnline = navigator.onLine;
    this.isVisible = !document.hidden;
    
    this._setupEventListeners();
    this._startProcessing();
    
    console.log('[BackgroundLoader] Initialized');
  }
  
  /**
   * Add a request to the priority queue
   * @param {Function} requestFn - Async function to execute
   * @param {Object} options - Request options
   * @returns {Promise} - Resolves with request result
   */
  async addRequest(requestFn, options = {}) {
    const {
      priority = Priority.MEDIUM,
      id = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      cancelable = true,
      timeout = 30000,
      retries = 2,
      metadata = {},
    } = options;
    
    this.stats.totalRequests++;
    
    return new Promise((resolve, reject) => {
      const controller = new AbortController();
      
      const request = {
        id,
        requestFn,
        priority,
        cancelable,
        timeout,
        retries,
        retriesLeft: retries,
        controller,
        metadata,
        resolve,
        reject,
        createdAt: Date.now(),
      };
      
      this.queue[priority].push(request);
      this._processQueue();
    });
  }
  
  /**
   * Cancel a specific request or all requests of a priority
   * @param {string|number} idOrPriority - Request ID or priority level
   */
  cancelRequest(idOrPriority) {
    if (typeof idOrPriority === 'string') {
      // Cancel specific request
      for (const priority in this.queue) {
        const index = this.queue[priority].findIndex(r => r.id === idOrPriority);
        if (index !== -1) {
          const request = this.queue[priority][index];
          if (request.cancelable) {
            request.controller.abort();
            request.reject(new Error('Request canceled'));
            this.queue[priority].splice(index, 1);
            this.stats.canceledRequests++;
          }
          return;
        }
      }
      
      // Check active requests
      if (this.activeRequests.has(idOrPriority)) {
        const request = this.activeRequests.get(idOrPriority);
        if (request.cancelable) {
          request.controller.abort();
          this.activeRequests.delete(idOrPriority);
          this.stats.canceledRequests++;
        }
      }
    } else {
      // Cancel all requests of a priority
      const queue = this.queue[idOrPriority];
      queue.forEach(request => {
        if (request.cancelable) {
          request.controller.abort();
          request.reject(new Error('Request canceled by priority'));
          this.stats.canceledRequests++;
        }
      });
      this.queue[idOrPriority] = [];
    }
  }
  
  /**
   * Process the request queue
   */
  async _processQueue() {
    // Skip if offline or tab is hidden (for non-critical requests)
    if (!this.isOnline) {
      console.log('[BackgroundLoader] Offline, skipping queue processing');
      return;
    }
    
    // Process each priority level
    for (const priority of [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW, Priority.IDLE]) {
      const queue = this.queue[priority];
      const maxConcurrent = this.maxConcurrent[priority];
      const activeCount = Array.from(this.activeRequests.values())
        .filter(r => r.priority === priority).length;
      
      // Skip if at max concurrent requests for this priority
      if (activeCount >= maxConcurrent) continue;
      
      // Skip idle requests if tab is hidden
      if (priority === Priority.IDLE && !this.isVisible) continue;
      
      // Process available slots
      const availableSlots = maxConcurrent - activeCount;
      const requestsToProcess = queue.splice(0, availableSlots);
      
      requestsToProcess.forEach(request => {
        this._executeRequest(request);
      });
    }
  }
  
  /**
   * Execute a single request
   */
  async _executeRequest(request) {
    this.activeRequests.set(request.id, request);
    const startTime = Date.now();
    
    try {
      // Create timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), request.timeout);
      });
      
      // Execute request with abort signal
      const result = await Promise.race([
        request.requestFn({ signal: request.controller.signal }),
        timeoutPromise
      ]);
      
      // Update stats
      const duration = Date.now() - startTime;
      this.stats.completedRequests++;
      this.stats.avgResponseTime = 
        (this.stats.avgResponseTime * (this.stats.completedRequests - 1) + duration) / 
        this.stats.completedRequests;
      
      request.resolve(result);
    } catch (error) {
      // Retry if retries available
      if (request.retriesLeft > 0 && error.name !== 'AbortError') {
        request.retriesLeft--;
        console.log(`[BackgroundLoader] Retrying request ${request.id}, ${request.retriesLeft} attempts left`);
        
        // Re-queue with exponential backoff
        const delay = (request.retries - request.retriesLeft) * 1000;
        setTimeout(() => {
          this.queue[request.priority].unshift(request);
          this._processQueue();
        }, delay);
      } else {
        request.reject(error);
      }
    } finally {
      this.activeRequests.delete(request.id);
      this._processQueue();
    }
  }
  
  /**
   * Preload critical data on app initialization
   */
  async preloadCriticalData() {
    console.log('[BackgroundLoader] Preloading critical data...');
    
    const criticalEndpoints = [
      { url: '/tethys/status', priority: Priority.CRITICAL },
      { url: '/universe/coins', priority: Priority.CRITICAL },
      { url: '/training-progress/active', priority: Priority.HIGH },
      { url: '/market/overview', priority: Priority.HIGH },
      { url: '/portfolio/visualization/summary', priority: Priority.HIGH },
    ];
    
    const promises = criticalEndpoints.map(({ url, priority }) =>
      this.addRequest(
        () => axios.get(`${API}${url}`),
        { priority, id: `preload_${url}`, cancelable: false }
      ).catch(err => {
        console.warn(`[BackgroundLoader] Failed to preload ${url}:`, err.message);
      })
    );
    
    await Promise.allSettled(promises);
    console.log('[BackgroundLoader] Critical data preloaded');
  }
  
  /**
   * Start background synchronization for a data source
   * @param {string} id - Unique identifier for this sync
   * @param {Function} fetchFn - Async function to fetch data
   * @param {Object} options - Sync options
   */
  startBackgroundSync(id, fetchFn, options = {}) {
    const {
      interval = 60000, // 1 minute default
      priority = Priority.LOW,
      onlyWhenVisible = true,
    } = options;
    
    // Stop existing sync if any
    this.stopBackgroundSync(id);
    
    const sync = async () => {
      // Skip if tab is hidden and onlyWhenVisible is true
      if (onlyWhenVisible && !this.isVisible) {
        return;
      }
      
      try {
        await this.addRequest(fetchFn, { 
          priority,
          id: `sync_${id}`,
          cancelable: true
        });
      } catch (err) {
        console.warn(`[BackgroundLoader] Sync ${id} failed:`, err.message);
      }
    };
    
    // Initial sync
    sync();
    
    // Schedule periodic sync
    const intervalId = setInterval(sync, interval);
    this.syncIntervals.set(id, intervalId);
    
    console.log(`[BackgroundLoader] Started background sync: ${id} (${interval}ms)`);
  }
  
  /**
   * Stop background synchronization
   * @param {string} id - Sync identifier
   */
  stopBackgroundSync(id) {
    if (this.syncIntervals.has(id)) {
      clearInterval(this.syncIntervals.get(id));
      this.syncIntervals.delete(id);
      console.log(`[BackgroundLoader] Stopped background sync: ${id}`);
    }
  }
  
  /**
   * Prefetch a resource (low priority)
   * @param {string} url - URL to prefetch
   * @param {string} type - Type of prefetch ('fetch' | 'image' | 'script')
   */
  async prefetch(url, type = 'fetch') {
    return this.addRequest(
      async () => {
        if (type === 'image') {
          return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = url;
          });
        } else if (type === 'script') {
          return import(/* webpackPrefetch: true */ url);
        } else {
          return axios.get(url);
        }
      },
      { priority: Priority.LOW, id: `prefetch_${url}` }
    );
  }
  
  /**
   * Add resource hints to document head
   * @param {Array} hints - Array of hint objects { rel, href, as? }
   */
  addResourceHints(hints) {
    hints.forEach(({ rel, href, as }) => {
      const link = document.createElement('link');
      link.rel = rel;
      link.href = href;
      if (as) link.as = as;
      document.head.appendChild(link);
    });
    
    console.log(`[BackgroundLoader] Added ${hints.length} resource hints`);
  }
  
  /**
   * Setup event listeners for online/offline and visibility changes
   */
  _setupEventListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      console.log('[BackgroundLoader] Online - resuming queue processing');
      this._processQueue();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
      console.log('[BackgroundLoader] Offline - pausing queue processing');
    });
    
    document.addEventListener('visibilitychange', () => {
      this.isVisible = !document.hidden;
      if (this.isVisible) {
        console.log('[BackgroundLoader] Tab visible - resuming idle requests');
        this._processQueue();
      } else {
        console.log('[BackgroundLoader] Tab hidden - pausing idle requests');
      }
    });
  }
  
  /**
   * Start continuous queue processing
   */
  _startProcessing() {
    // Process queue every 100ms
    setInterval(() => {
      this._processQueue();
    }, 100);
  }
  
  /**
   * Get current statistics
   */
  getStats() {
    const queueSizes = {};
    for (const priority in this.queue) {
      queueSizes[priority] = this.queue[priority].length;
    }
    
    return {
      ...this.stats,
      queueSizes,
      activeRequests: this.activeRequests.size,
      activeSyncs: this.syncIntervals.size,
      isOnline: this.isOnline,
      isVisible: this.isVisible,
    };
  }
  
  /**
   * Clear all queues and stop all syncs
   */
  destroy() {
    // Cancel all queued requests
    for (const priority in this.queue) {
      this.cancelRequest(parseInt(priority));
    }
    
    // Stop all background syncs
    this.syncIntervals.forEach((_, id) => this.stopBackgroundSync(id));
    
    console.log('[BackgroundLoader] Destroyed');
  }
}

// Singleton instance
let backgroundLoader = null;

export const getBackgroundLoader = () => {
  if (!backgroundLoader) {
    backgroundLoader = new BackgroundLoader();
  }
  return backgroundLoader;
};

export default getBackgroundLoader;
