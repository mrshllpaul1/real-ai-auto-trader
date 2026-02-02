const CACHE_NAME = 'crypto-trade-v3';
const API_BASE = '/api';

const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json'
];

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
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Network first for API, cache first for static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // API requests - network first
  if (url.pathname.startsWith('/api')) {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(event.request))
    );
    return;
  }
  
  // Static assets - cache first
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
