const CACHE_NAME = 'tethys-ai-v4';
const STATIC_CACHE = 'tethys-static-v4';
const DYNAMIC_CACHE = 'tethys-dynamic-v4';
const API_CACHE = 'tethys-api-v4';

// API base URL - defaults to same origin, can be overridden via message
let API_BASE = self.location.origin + '/api';

const urlsToCache = [
  '/',
  '/manifest.json',
  '/offline.html'
];

// Static assets to cache during install
const staticAssets = [
  '/static/css/main.css',
  '/static/js/main.js',
  '/logo192.png',
  '/logo512.png',
  '/favicon.ico'
];

// API routes to cache with stale-while-revalidate
const apiCacheRoutes = [
  '/api/health',
  '/api/portfolio/visualization/summary',
  '/api/market/overview',
  '/api/coins/universe'
];

// Install service worker and cache assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Tethys AI Service Worker...');
  event.waitUntil(
    Promise.all([
      caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache)),
      caches.open(STATIC_CACHE).then((cache) => {
        return cache.addAll(staticAssets).catch(err => {
          console.log('[SW] Static assets cache failed (non-critical):', err);
        });
      })
    ]).then(() => self.skipWaiting())
  );
});

// Activate and clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  const currentCaches = [CACHE_NAME, STATIC_CACHE, DYNAMIC_CACHE, API_CACHE];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => !currentCaches.includes(name))
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Network first for API, cache first for static, stale-while-revalidate for dynamic
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip WebSocket connections
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;
  
  // API requests - network first with cache fallback
  if (url.pathname.startsWith('/api')) {
    // Use stale-while-revalidate for common API routes
    const shouldCache = apiCacheRoutes.some(route => url.pathname.includes(route));
    
    if (shouldCache) {
      event.respondWith(
        caches.open(API_CACHE).then(cache => {
          return cache.match(event.request).then(cachedResponse => {
            const fetchPromise = fetch(event.request)
              .then(networkResponse => {
                if (networkResponse && networkResponse.ok) {
                  cache.put(event.request, networkResponse.clone());
                }
                return networkResponse;
              })
              .catch(() => cachedResponse);
            
            return cachedResponse || fetchPromise;
          });
        })
      );
    } else {
      // Network first for non-cached API
      event.respondWith(
        fetch(event.request)
          .catch(() => caches.match(event.request))
      );
    }
    return;
  }
  
  // Static assets - cache first
  if (url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff2?|ttf|eot)$/)) {
    event.respondWith(
      caches.match(event.request).then(response => {
        return response || fetch(event.request).then(fetchResponse => {
          return caches.open(STATIC_CACHE).then(cache => {
            cache.put(event.request, fetchResponse.clone());
            return fetchResponse;
          });
        });
      })
    );
    return;
  }
  
  // HTML - network first with offline fallback
  if (event.request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          caches.open(DYNAMIC_CACHE).then(cache => {
            cache.put(event.request, response.clone());
          });
          return response;
        })
        .catch(() => {
          return caches.match(event.request)
            .then(cachedResponse => cachedResponse || caches.match('/offline.html'));
        })
    );
    return;
  }
  
  // Default - network with cache fallback
  event.respondWith(
    caches.match(event.request)
      .then((response) => response || fetch(event.request))
  );
});

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
  
  // Allow client to set API base URL
  if (event.data && event.data.type === 'SET_API_BASE') {
    API_BASE = event.data.url;
    console.log('[SW] API_BASE set to:', API_BASE);
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
