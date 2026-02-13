/**
 * Enhanced PWA Service
 * ====================
 * Provides advanced PWA functionality including:
 * - Install prompts with custom UI
 * - App update detection and handling
 * - Offline status management
 * - Background sync
 * - Push notification management
 */

class PWAService {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.isOnline = navigator.onLine;
    this.swRegistration = null;
    this.updateAvailable = false;
    this.listeners = new Map();
    
    this.init();
  }

  init() {
    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.emit('installable', true);
    });

    // Listen for successful install
    window.addEventListener('appinstalled', () => {
      this.isInstalled = true;
      this.deferredPrompt = null;
      this.emit('installed', true);
      console.log('[PWA] App installed successfully');
    });

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      this.isInstalled = true;
    }

    // Online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.emit('online', true);
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.emit('online', false);
    });

    // Register service worker
    this.registerServiceWorker();
  }

  async registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      console.log('[PWA] Service workers not supported');
      return;
    }

    try {
      this.swRegistration = await navigator.serviceWorker.register('/service-worker.js');
      console.log('[PWA] Service worker registered');

      // Check for updates
      this.swRegistration.addEventListener('updatefound', () => {
        const newWorker = this.swRegistration.installing;
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            this.updateAvailable = true;
            this.emit('updateAvailable', true);
            console.log('[PWA] Update available');
          }
        });
      });

      // Handle controller change (update activated)
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[PWA] New service worker activated');
      });

    } catch (error) {
      console.error('[PWA] Service worker registration failed:', error);
    }
  }

  // Event system
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.listeners.get(event).delete(callback);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(cb => cb(data));
    }
  }

  // Install prompt
  async promptInstall() {
    if (!this.deferredPrompt) {
      console.log('[PWA] Install prompt not available');
      return { outcome: 'unavailable' };
    }

    this.deferredPrompt.prompt();
    const result = await this.deferredPrompt.userChoice;
    
    if (result.outcome === 'accepted') {
      this.deferredPrompt = null;
    }
    
    return result;
  }

  canInstall() {
    return this.deferredPrompt !== null && !this.isInstalled;
  }

  // Update handling
  async applyUpdate() {
    if (!this.swRegistration || !this.swRegistration.waiting) {
      console.log('[PWA] No update waiting');
      return false;
    }

    // Tell service worker to skip waiting
    this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
    
    // Reload page to use new version
    window.location.reload();
    return true;
  }

  // Offline capabilities
  isOffline() {
    return !this.isOnline;
  }

  // Cache management
  async clearCache() {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(name => caches.delete(name))
    );
    console.log('[PWA] All caches cleared');
  }

  async getCacheSize() {
    if (!('storage' in navigator && 'estimate' in navigator.storage)) {
      return null;
    }
    
    const estimate = await navigator.storage.estimate();
    return {
      used: estimate.usage,
      total: estimate.quota,
      usedMB: (estimate.usage / (1024 * 1024)).toFixed(2),
      totalMB: (estimate.quota / (1024 * 1024)).toFixed(2),
      percentUsed: ((estimate.usage / estimate.quota) * 100).toFixed(1)
    };
  }

  // Push notifications
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      return { supported: false };
    }

    const permission = await Notification.requestPermission();
    return { 
      supported: true, 
      permission,
      granted: permission === 'granted'
    };
  }

  async subscribeToPush(vapidPublicKey) {
    if (!this.swRegistration) {
      return { success: false, error: 'Service worker not registered' };
    }

    try {
      const subscription = await this.swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey)
      });

      return { success: true, subscription };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Background sync
  async registerBackgroundSync(tag) {
    if (!this.swRegistration || !('sync' in this.swRegistration)) {
      return { success: false, error: 'Background sync not supported' };
    }

    try {
      await this.swRegistration.sync.register(tag);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Share API
  canShare() {
    return 'share' in navigator;
  }

  async share(data) {
    if (!this.canShare()) {
      return { success: false, error: 'Web Share API not supported' };
    }

    try {
      await navigator.share(data);
      return { success: true };
    } catch (error) {
      if (error.name === 'AbortError') {
        return { success: false, error: 'Share cancelled' };
      }
      return { success: false, error: error.message };
    }
  }

  // Device capabilities
  getDeviceInfo() {
    return {
      standalone: window.matchMedia('(display-mode: standalone)').matches,
      touchScreen: 'ontouchstart' in window,
      deviceMemory: navigator.deviceMemory || 'unknown',
      hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
      platform: navigator.platform,
      userAgent: navigator.userAgent,
      language: navigator.language,
      online: navigator.onLine,
      cookiesEnabled: navigator.cookieEnabled,
      serviceWorkerSupported: 'serviceWorker' in navigator,
      pushSupported: 'PushManager' in window,
      notificationsSupported: 'Notification' in window,
      storageEstimateSupported: 'storage' in navigator && 'estimate' in navigator.storage
    };
  }

  // Vibration
  vibrate(pattern = [200, 100, 200]) {
    if ('vibrate' in navigator) {
      navigator.vibrate(pattern);
      return true;
    }
    return false;
  }

  // Screen wake lock
  async requestWakeLock() {
    if (!('wakeLock' in navigator)) {
      return { success: false, error: 'Wake Lock not supported' };
    }

    try {
      const wakeLock = await navigator.wakeLock.request('screen');
      return { success: true, wakeLock };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

// Create singleton instance
const pwaService = new PWAService();

export default pwaService;

// Named exports for convenience
export const {
  canInstall,
  promptInstall,
  isOffline,
  on: onPWAEvent,
  applyUpdate,
  getDeviceInfo,
  requestNotificationPermission,
  share,
  canShare,
  vibrate,
  getCacheSize,
  clearCache
} = pwaService;
