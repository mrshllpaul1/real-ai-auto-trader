const CACHE_NAME = 'crypto-trade-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json'
];

// Install service worker and cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Fetch from cache first, then network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => response || fetch(event.request))
  );
});

// Background sync for trades
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-trades') {
    event.waitUntil(syncTrades());
  }
});

// Keep-alive ping
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'KEEP_ALIVE') {
    event.ports[0].postMessage({ alive: true });
  }
});

async function syncTrades() {
  try {
    const response = await fetch('/api/trading/sync');
    return response.json();
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

// Background fetch for auto-trading updates
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'update-trades') {
    event.waitUntil(updateTrades());
  }
});

async function updateTrades() {
  try {
    const response = await fetch('/api/auto-trading/status');
    const data = await response.json();
    
    // Show notification if significant event
    if (data.newTrades > 0) {
      self.registration.showNotification('Trade Executed', {
        body: `${data.newTrades} new auto-trades executed`,
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: 'trade-notification'
      });
    }
  } catch (error) {
    console.error('Update failed:', error);
  }
}