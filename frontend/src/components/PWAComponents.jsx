import React, { useState, useEffect, useCallback } from 'react';
import { Download, X, Wifi, WifiOff, RefreshCw, Smartphone, CheckCircle2 } from 'lucide-react';
import pwaService from '../services/pwaService';

/**
 * PWA Install Banner
 * Shows an install prompt when the app can be installed
 */
export function PWAInstallBanner() {
  const [canInstall, setCanInstall] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [installing, setInstalling] = useState(false);

  useEffect(() => {
    // Check if user previously dismissed
    const wasDismissed = localStorage.getItem('pwa-install-dismissed');
    if (wasDismissed) {
      const dismissedAt = new Date(wasDismissed);
      const daysSince = (Date.now() - dismissedAt.getTime()) / (1000 * 60 * 60 * 24);
      // Show again after 7 days
      if (daysSince < 7) {
        setDismissed(true);
      }
    }

    // Listen for installable event
    const unsubscribe = pwaService.on('installable', (isInstallable) => {
      setCanInstall(isInstallable);
    });

    // Check initial state
    setCanInstall(pwaService.canInstall());

    return unsubscribe;
  }, []);

  const handleInstall = async () => {
    setInstalling(true);
    const result = await pwaService.promptInstall();
    setInstalling(false);
    
    if (result.outcome === 'accepted') {
      setCanInstall(false);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('pwa-install-dismissed', new Date().toISOString());
  };

  if (!canInstall || dismissed) return null;

  return (
    <div 
      className="fixed bottom-20 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-in slide-in-from-bottom-4"
      data-testid="pwa-install-banner"
    >
      <div className="bg-gradient-to-r from-purple-900/95 to-indigo-900/95 backdrop-blur-xl rounded-2xl border border-purple-500/30 shadow-2xl p-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
            <Smartphone className="w-6 h-6 text-white" />
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white text-sm">Install Tethys AI</h3>
            <p className="text-xs text-gray-300 mt-0.5">
              Get faster access, offline support & push notifications
            </p>
            
            <div className="flex items-center gap-2 mt-3">
              <button
                onClick={handleInstall}
                disabled={installing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-purple-600 to-cyan-600 rounded-lg text-white text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                data-testid="pwa-install-button"
              >
                {installing ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                Install App
              </button>
              
              <button
                onClick={handleDismiss}
                className="px-3 py-1.5 text-gray-400 hover:text-white text-xs transition-colors"
                data-testid="pwa-dismiss-button"
              >
                Not now
              </button>
            </div>
          </div>
          
          <button
            onClick={handleDismiss}
            className="p-1 text-gray-400 hover:text-white transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * PWA Update Banner
 * Shows when a new version is available
 */
export function PWAUpdateBanner() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const unsubscribe = pwaService.on('updateAvailable', (available) => {
      setUpdateAvailable(available);
    });

    return unsubscribe;
  }, []);

  const handleUpdate = async () => {
    setUpdating(true);
    await pwaService.applyUpdate();
  };

  if (!updateAvailable) return null;

  return (
    <div 
      className="fixed top-4 left-4 right-4 md:left-auto md:right-4 md:w-80 z-50 animate-in slide-in-from-top-4"
      data-testid="pwa-update-banner"
    >
      <div className="bg-emerald-900/95 backdrop-blur-xl rounded-xl border border-emerald-500/30 shadow-xl p-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
            <RefreshCw className="w-4 h-4 text-emerald-400" />
          </div>
          
          <div className="flex-1">
            <p className="text-sm font-medium text-white">Update Available</p>
            <p className="text-xs text-emerald-300/80">Refresh to get the latest version</p>
          </div>
          
          <button
            onClick={handleUpdate}
            disabled={updating}
            className="px-3 py-1.5 bg-emerald-600 rounded-lg text-white text-xs font-medium hover:bg-emerald-500 transition-colors disabled:opacity-50"
            data-testid="pwa-update-button"
          >
            {updating ? 'Updating...' : 'Update'}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Offline Indicator
 * Shows when the app goes offline
 */
export function OfflineIndicator() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const unsubscribe = pwaService.on('online', (online) => {
      setIsOffline(!online);
      setShowBanner(!online);
      
      // Auto-hide after coming back online
      if (online) {
        setTimeout(() => setShowBanner(false), 3000);
      }
    });

    return unsubscribe;
  }, []);

  if (!showBanner) return null;

  return (
    <div 
      className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-in fade-in ${
        isOffline ? 'slide-in-from-top-2' : 'slide-out-to-top-2'
      }`}
      data-testid="offline-indicator"
    >
      <div className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg backdrop-blur-xl ${
        isOffline 
          ? 'bg-orange-900/95 border border-orange-500/30' 
          : 'bg-emerald-900/95 border border-emerald-500/30'
      }`}>
        {isOffline ? (
          <>
            <WifiOff className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-orange-200">You're offline</span>
          </>
        ) : (
          <>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span className="text-sm text-emerald-200">Back online</span>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * PWA Status Badge
 * Shows PWA installation and network status in a compact format
 */
export function PWAStatusBadge({ className = '' }) {
  const [isInstalled, setIsInstalled] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // Check if running as installed PWA
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    setIsInstalled(isStandalone);

    const unsubscribe = pwaService.on('online', setIsOnline);
    return unsubscribe;
  }, []);

  return (
    <div className={`flex items-center gap-2 ${className}`} data-testid="pwa-status-badge">
      {isInstalled && (
        <span className="flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 rounded text-xs text-purple-300">
          <Smartphone className="w-3 h-3" />
          App
        </span>
      )}
      <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
        isOnline 
          ? 'bg-emerald-500/20 text-emerald-300' 
          : 'bg-orange-500/20 text-orange-300'
      }`}>
        {isOnline ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
        {isOnline ? 'Online' : 'Offline'}
      </span>
    </div>
  );
}

/**
 * Mobile-optimized PWA container that handles safe areas
 */
export function PWAContainer({ children }) {
  return (
    <div className="min-h-screen safe-area-top safe-area-bottom">
      {children}
      <PWAInstallBanner />
      <PWAUpdateBanner />
      <OfflineIndicator />
    </div>
  );
}

export default PWAContainer;
