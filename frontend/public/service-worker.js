const CACHE_NAME = 'crypto-trade-v4';  // Bump version for performance improvements
const RUNTIME_CACHE = 'runtime-cache-v1';
const API_BASE = '/api';

const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json'
];

// Cache strategies with TTL
const CACHE_STRATEGIES = {
  // Market data - short TTL
  '/api/market/prices': { strategy: 'network-first', maxAge: 30000 }, // 30s
  '/api/market/global': { strategy: 'network-first', maxAge: 60000 }, // 1min
  '/api/market/trending': { strategy: 'cache-first', maxAge: 300000 }, // 5min
  '/api/market/news': { strategy: 'cache-first', maxAge: 180000 }, // 3min
  
  // Portfolio data - medium TTL
  '/api/portfolio': { strategy: 'network-first', maxAge: 10000 }, // 10s
  '/api/positions': { strategy: 'network-first', maxAge: 10000 }, // 10s
  
  // Static data - long TTL
  '/api/strategies': { strategy: 'cache-first', maxAge: 600000 }, // 10min
  '/api/triggers/templates': { strategy: 'cache-first', maxAge: 600000 }, // 10min
};

// Install service worker and cache assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

// Activate and clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== RUNTIME_CACHE)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Smart caching with TTL and strategies
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Find matching strategy
  let cacheConfig = null;
  for (const [path, config] of Object.entries(CACHE_STRATEGIES)) {
    if (url.pathname.startsWith(path)) {
      cacheConfig = config;
      break;
    }
  }
  
  // API requests with smart caching
  if (url.pathname.startsWith('/api')) {
    if (cacheConfig) {
      if (cacheConfig.strategy === 'cache-first') {
        event.respondWith(cacheFirst(event.request, cacheConfig.maxAge));
      } else {
        event.respondWith(networkFirst(event.request, cacheConfig.maxAge));
      }
    } else {
      // Default: network first without caching
      event.respondWith(
        fetch(event.request)
          .catch(() => caches.match(event.request))
      );
    }
    return;
  }
  
  // Static assets - cache first
  event.respondWith(
    caches.match(event.request)
      .then((response) => response || fetch(event.request))
  );
});

// Cache First strategy with TTL
async function cacheFirst(request, maxAge) {
  const cached = await caches.match(request);
  
  if (cached) {
    const cacheTime = parseInt(cached.headers.get('sw-cache-time') || '0');
    const now = Date.now();
    
    // Return cached if still valid
    if (now - cacheTime < maxAge) {
      return cached;
    }
  }
  
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      const clonedResponse = response.clone();
      
      // Add cache timestamp
      const responseBlob = await clonedResponse.blob();
      const headers = new Headers(clonedResponse.headers);
      headers.set('sw-cache-time', Date.now().toString());
      
      const cacheResponse = new Response(responseBlob, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });
      
      await cache.put(request, cacheResponse);
    }
    
    return response;
  } catch (error) {
    // Network failed, return stale cache if available
    if (cached) {
      return cached;
    }
    throw error;
  }
}

// Network First strategy with TTL
async function networkFirst(request, maxAge) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(RUNTIME_CACHE);
      const clonedResponse = response.clone();
      
      // Add cache timestamp
      const responseBlob = await clonedResponse.blob();
      const headers = new Headers(clonedResponse.headers);
      headers.set('sw-cache-time', Date.now().toString());
      
      const cacheResponse = new Response(responseBlob, {
        status: clonedResponse.status,
        statusText: clonedResponse.statusText,
        headers: headers
      });
      
      await cache.put(request, cacheResponse);
    }
    
    return response;
  } catch (error) {
    // Network failed, try cache
    const cached = await caches.match(request);
    
    if (cached) {
      return cached;
    }
    
    throw error;
  }
}

// Background sync for trades
self.addEventListener('sync', (event) => {
  console.log('[SW] Sync event:', event.tag);
  
  if (event.tag === 'sync-trades') {
    event.waitUntil(syncTrades());
  }
  
  if (event.tag === 'check-scanner') {
    event.waitUntil(checkScanner());
  }
});

// Periodic sync for background updates
self.addEventListener('periodicsync', (event) => {
  console.log('[SW] Periodic sync:', event.tag);
  
  if (event.tag === 'update-trades') {
    event.waitUntil(updateTrades());
  }
  
  if (event.tag === 'check-alerts') {
    event.waitUntil(checkAlerts());
  }
});

// Handle push notifications with vibration
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');
  
  let data = { 
    title: 'AI Crypto Trading', 
    body: 'New notification',
    priority: 'normal',
    vibrate: true
  };
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  // Vibration patterns based on priority
  const vibrationPatterns = {
    critical: [200, 100, 200, 100, 200, 100, 400],
    high: [200, 100, 200, 100, 400],
    normal: [200, 100, 200],
    low: [100]
  };
  
  const vibrationPattern = data.vibration_pattern || 
    vibrationPatterns[data.priority] || 
    vibrationPatterns.normal;
  
  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: data.vibrate !== false ? vibrationPattern : [],
    tag: data.tag || 'default',
    data: data.data || {},
    requireInteraction: data.priority === 'high' || data.priority === 'critical',
    actions: [
      { action: 'view', title: 'View' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification click:', event.action);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  // Focus or open app
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus();
        }
      }
      return clients.openWindow('/');
    })
  );
});

// Keep-alive ping handler
self.addEventListener('message', (event) => {
  console.log('[SW] Message:', event.data);
  
  if (event.data && event.data.type === 'KEEP_ALIVE') {
    event.ports[0].postMessage({ alive: true, timestamp: Date.now() });
  }
  
  if (event.data && event.data.type === 'START_BACKGROUND') {
    startBackgroundTasks();
  }
  
  if (event.data && event.data.type === 'STOP_BACKGROUND') {
    stopBackgroundTasks();
  }
});

// Background task functions
let backgroundInterval = null;

function startBackgroundTasks() {
  console.log('[SW] Starting background tasks');
  
  if (backgroundInterval) {
    clearInterval(backgroundInterval);
  }
  
  // Check every 5 minutes
  backgroundInterval = setInterval(async () => {
    await updateTrades();
    await checkAlerts();
  }, 5 * 60 * 1000);
  
  // Initial check
  updateTrades();
}

function stopBackgroundTasks() {
  console.log('[SW] Stopping background tasks');
  if (backgroundInterval) {
    clearInterval(backgroundInterval);
    backgroundInterval = null;
  }
}

async function syncTrades() {
  try {
    const response = await fetch(`${API_BASE}/trading/sync`);
    return response.json();
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

async function updateTrades() {
  try {
    const response = await fetch(`${API_BASE}/auto-exec/status`);
    const data = await response.json();
    
    // Notify if there are new trades
    if (data.recent_trades && data.recent_trades.length > 0) {
      const latestTrade = data.recent_trades[0];
      
      self.registration.showNotification('Trade Update', {
        body: `${latestTrade.action} ${latestTrade.symbol} at $${latestTrade.price}`,
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: 'trade-update',
        vibrate: [200, 100, 200]
      });
    }
  } catch (error) {
    console.error('[SW] Update failed:', error);
  }
}

async function checkScanner() {
  try {
    const response = await fetch(`${API_BASE}/scanner/alerts`);
    const data = await response.json();
    
    // Notify for HIGH priority alerts with urgent vibration
    const highAlerts = (data.alerts || []).filter(a => a.alert_level === 'HIGH');
    
    if (highAlerts.length > 0) {
      const alert = highAlerts[0];
      
      self.registration.showNotification('🚨 HIGH Priority Gem', {
        body: `${alert.symbol}: Score ${alert.match_score} - ${alert.potential_multiplier}`,
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: 'gem-alert',
        requireInteraction: true,
        vibrate: [200, 100, 200, 100, 400]  // Urgent pattern
      });
    }
  } catch (error) {
    console.error('[SW] Scanner check failed:', error);
  }
}

async function checkAlerts() {
  try {
    const response = await fetch(`${API_BASE}/notifications/`);
    const data = await response.json();
    
    // Show unread notifications with appropriate vibration
    const unread = (data.notifications || []).filter(n => !n.read);
    
    if (unread.length > 0) {
      const notif = unread[0];
      
      // Get vibration pattern based on priority
      const vibrationPatterns = {
        critical: [200, 100, 200, 100, 200, 100, 400],
        high: [200, 100, 200, 100, 400],
        normal: [200, 100, 200],
        low: [100]
      };
      
      const vibration = notif.vibrate !== false ? 
        (notif.vibration_pattern || vibrationPatterns[notif.priority] || vibrationPatterns.normal) : 
        [];
      
      self.registration.showNotification(notif.title, {
        body: notif.body,
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: `notif-${notif.id}`,
        vibrate: vibration,
        requireInteraction: notif.priority === 'high' || notif.priority === 'critical'
      });
    }
  } catch (error) {
    console.error('[SW] Alerts check failed:', error);
  }
}

console.log('[SW] Service Worker loaded with vibration support');
