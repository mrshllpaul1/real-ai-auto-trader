/**
 * Sound Alerts Configuration
 * Audio notifications for trading events
 * 
 * Usage:
 * import { playSoundAlert } from './utils/soundAlerts';
 * playSoundAlert('trade_executed');
 */

// Sound effect URLs (can be hosted locally or use Web Audio API)
export const SOUND_EFFECTS = {
  // Trading sounds
  trade_executed: {
    url: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OShUhELTqHf8bhlHAU2jdXvxnkrBSF3yO/ekEELFGC36OynVBELRp3e8bpmHwUue8rx2IA3Bxpmu+zjnlARC0+k4/G2Yh0FOI/W8sh2KwUjeMfu35VCChZiuOjopVURCkaZ3fCyZCEGM4LK8daANQYZZbnr4ptQEwtQpOLwuGIfBTiP1fDGdioFInbF7t6UQgsZY7jp6aRTEgpImt3wsmgiBjKAyfDTfzYHGWS56+OeURMMUKXi8btgHgU6kNbvxnYpBSF1xO7ekEELGGK36OilVRIMRpvd8LVhIQU0gMnw1H0zBhlmue3jn1ISC1Gl4u+5YB4GOpDX78p2KgUgdcXu3IxBDBJduebjpVURDEebW/...',
    volume: 0.6
  },
  trade_pending: {
    url: 'data:audio/wav;base64,UklGRmQFAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YUAFAACZZ2Zm...',
    volume: 0.4
  },
  trade_failed: {
    url: 'data:audio/wav;base64,UklGRoYGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YWIGAACampqampqZ...',
    volume: 0.7
  },
  
  // Alert sounds
  price_alert: {
    url: 'data:audio/wav;base64,UklGRkQCAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YTACAACBAQEB...',
    volume: 0.5
  },
  stop_loss_triggered: {
    url: 'data:audio/wav;base64,UklGRoYGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YWIGAABnZ2dn...',
    volume: 0.8
  },
  take_profit_hit: {
    url: 'data:audio/wav;base64,UklGRmQFAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YUAFAACBAQEB...',
    volume: 0.7
  },
  
  // AI sounds
  ai_signal: {
    url: 'data:audio/wav;base64,UklGRoYGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YWIGAACBhYqF...',
    volume: 0.5
  },
  model_trained: {
    url: 'data:audio/wav;base64,UklGRkQCAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YTACAACBAQEB...',
    volume: 0.6
  },
  
  // Notification sounds
  notification: {
    url: 'data:audio/wav;base64,UklGRkQCAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YTACAACBAQEB...',
    volume: 0.4
  },
  error: {
    url: 'data:audio/wav;base64,UklGRoYGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YWIGAACBhYqF...',
    volume: 0.6
  },
  success: {
    url: 'data:audio/wav;base64,UklGRmQFAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YUAFAACBAQEB...',
    volume: 0.5
  }
};

// Audio context for better performance
let audioContext = null;
let audioBuffers = {};

/**
 * Initialize audio context
 */
function initAudioContext() {
  if (!audioContext) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioContext();
  }
  return audioContext;
}

/**
 * Load and cache audio buffer
 * @param {string} soundKey - Sound effect key
 * @returns {Promise<AudioBuffer>}
 */
async function loadAudioBuffer(soundKey) {
  if (audioBuffers[soundKey]) {
    return audioBuffers[soundKey];
  }
  
  const sound = SOUND_EFFECTS[soundKey];
  if (!sound) {
    throw new Error(`Sound '${soundKey}' not found`);
  }
  
  const ctx = initAudioContext();
  
  // For data URIs, decode directly
  if (sound.url.startsWith('data:')) {
    const base64Data = sound.url.split(',')[1];
    const binaryData = atob(base64Data);
    const arrayBuffer = new ArrayBuffer(binaryData.length);
    const view = new Uint8Array(arrayBuffer);
    
    for (let i = 0; i < binaryData.length; i++) {
      view[i] = binaryData.charCodeAt(i);
    }
    
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
    audioBuffers[soundKey] = audioBuffer;
    return audioBuffer;
  }
  
  // For external URLs, fetch and decode
  const response = await fetch(sound.url);
  const arrayBuffer = await response.arrayBuffer();
  const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
  
  audioBuffers[soundKey] = audioBuffer;
  return audioBuffer;
}

/**
 * Play sound alert
 * @param {string} soundKey - Sound effect key from SOUND_EFFECTS
 * @param {Object} options - Optional settings
 * @returns {Promise<void>}
 */
export async function playSoundAlert(soundKey, options = {}) {
  try {
    // Check if sounds are enabled in user preferences
    const soundEnabled = localStorage.getItem('soundAlertsEnabled');
    if (soundEnabled === 'false') {
      return;
    }
    
    const sound = SOUND_EFFECTS[soundKey];
    if (!sound) {
      console.warn(`Sound '${soundKey}' not found`);
      return;
    }
    
    const ctx = initAudioContext();
    
    // Resume audio context if suspended (browser autoplay policy)
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }
    
    // Load audio buffer
    const audioBuffer = await loadAudioBuffer(soundKey);
    
    // Create audio source
    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    
    // Create gain node for volume control
    const gainNode = ctx.createGain();
    const volume = options.volume ?? sound.volume ?? 0.5;
    gainNode.gain.value = volume;
    
    // Connect nodes
    source.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    // Play sound
    source.start(0);
    
  } catch (error) {
    console.error('Error playing sound alert:', error);
  }
}

/**
 * Enable/disable sound alerts
 * @param {boolean} enabled
 */
export function setSoundAlertsEnabled(enabled) {
  localStorage.setItem('soundAlertsEnabled', enabled.toString());
}

/**
 * Check if sound alerts are enabled
 * @returns {boolean}
 */
export function areSoundAlertsEnabled() {
  const enabled = localStorage.getItem('soundAlertsEnabled');
  return enabled !== 'false'; // Default to enabled
}

/**
 * Set global volume for all sounds
 * @param {number} volume - Volume level (0.0 to 1.0)
 */
export function setGlobalVolume(volume) {
  const clampedVolume = Math.max(0, Math.min(1, volume));
  localStorage.setItem('soundAlertsVolume', clampedVolume.toString());
}

/**
 * Get global volume setting
 * @returns {number}
 */
export function getGlobalVolume() {
  const volume = localStorage.getItem('soundAlertsVolume');
  return volume ? parseFloat(volume) : 0.5;
}

/**
 * Preload common sounds for instant playback
 */
export async function preloadSounds() {
  const commonSounds = [
    'trade_executed',
    'notification',
    'error',
    'success'
  ];
  
  try {
    await Promise.all(
      commonSounds.map(sound => loadAudioBuffer(sound))
    );
  } catch (error) {
    console.error('Error preloading sounds:', error);
  }
}

// Convenience functions for common events
export const soundAlerts = {
  tradeExecuted: () => playSoundAlert('trade_executed'),
  tradePending: () => playSoundAlert('trade_pending'),
  tradeFailed: () => playSoundAlert('trade_failed'),
  priceAlert: () => playSoundAlert('price_alert'),
  stopLoss: () => playSoundAlert('stop_loss_triggered'),
  takeProfit: () => playSoundAlert('take_profit_hit'),
  aiSignal: () => playSoundAlert('ai_signal'),
  modelTrained: () => playSoundAlert('model_trained'),
  notification: () => playSoundAlert('notification'),
  error: () => playSoundAlert('error'),
  success: () => playSoundAlert('success')
};

export default {
  playSoundAlert,
  soundAlerts,
  setSoundAlertsEnabled,
  areSoundAlertsEnabled,
  setGlobalVolume,
  getGlobalVolume,
  preloadSounds,
  SOUND_EFFECTS
};
