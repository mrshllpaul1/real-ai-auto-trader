/**
 * Push Notification Service
 * Handles browser push notification subscriptions and preferences
 */

const VAPID_PUBLIC_KEY = 'BLBx-hf5j3t9Z...' // Placeholder - needs real VAPID key

/**
 * Request notification permission from user
 */
export const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.warn('Push notifications not supported');
    return { granted: false, reason: 'not_supported' };
  }

  if (Notification.permission === 'granted') {
    return { granted: true };
  }

  if (Notification.permission === 'denied') {
    return { granted: false, reason: 'denied' };
  }

  const permission = await Notification.requestPermission();
  return { granted: permission === 'granted' };
};

/**
 * Check if service worker and push are supported
 */
export const isPushSupported = () => {
  return 'serviceWorker' in navigator && 'PushManager' in window;
};

/**
 * Get current push subscription
 */
export const getSubscription = async () => {
  if (!isPushSupported()) return null;

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return subscription;
  } catch (error) {
    console.error('Error getting push subscription:', error);
    return null;
  }
};

/**
 * Subscribe to push notifications
 */
export const subscribeToPush = async () => {
  if (!isPushSupported()) {
    throw new Error('Push notifications not supported');
  }

  const permission = await requestNotificationPermission();
  if (!permission.granted) {
    throw new Error(`Notification permission ${permission.reason || 'not granted'}`);
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    
    // Check for existing subscription
    let subscription = await registration.pushManager.getSubscription();
    
    if (!subscription) {
      // Create new subscription
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });
    }

    return {
      endpoint: subscription.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(subscription.getKey('p256dh')),
        auth: arrayBufferToBase64(subscription.getKey('auth'))
      }
    };
  } catch (error) {
    console.error('Push subscription error:', error);
    throw error;
  }
};

/**
 * Unsubscribe from push notifications
 */
export const unsubscribeFromPush = async () => {
  try {
    const subscription = await getSubscription();
    if (subscription) {
      await subscription.unsubscribe();
      return true;
    }
    return false;
  } catch (error) {
    console.error('Push unsubscribe error:', error);
    throw error;
  }
};

/**
 * Show a local notification (not via push server)
 */
export const showLocalNotification = async (title, options = {}) => {
  const permission = await requestNotificationPermission();
  if (!permission.granted) return false;

  try {
    const registration = await navigator.serviceWorker.ready;
    
    await registration.showNotification(title, {
      body: options.body || '',
      icon: options.icon || '/logo192.png',
      badge: '/logo192.png',
      tag: options.tag || 'local-notification',
      vibrate: options.vibrate || [200, 100, 200],
      requireInteraction: options.requireInteraction || false,
      data: options.data || {},
      actions: options.actions || []
    });

    return true;
  } catch (error) {
    console.error('Show notification error:', error);
    return false;
  }
};

/**
 * Show error alert notification
 */
export const showErrorAlertNotification = async (alert) => {
  const triggers = alert.triggers || [];
  const triggerText = triggers.map(t => t.type.replace('_', ' ')).join(', ');
  
  return showLocalNotification('🚨 Error Alert', {
    body: `Threshold exceeded: ${triggerText}`,
    tag: 'error-alert',
    vibrate: [200, 100, 200, 100, 400],
    requireInteraction: true,
    data: { url: '/error-analytics' },
    actions: [
      { action: 'view', title: 'View Dashboard' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  });
};

// Utility functions
function urlBase64ToUint8Array(base64String) {
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

function arrayBufferToBase64(buffer) {
  if (!buffer) return '';
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

export default {
  requestNotificationPermission,
  isPushSupported,
  getSubscription,
  subscribeToPush,
  unsubscribeFromPush,
  showLocalNotification,
  showErrorAlertNotification
};
