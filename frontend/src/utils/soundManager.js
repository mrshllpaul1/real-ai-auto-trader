/**
 * Sound Manager for trading alerts and notifications
 * Uses Web Audio API for low-latency playback
 */

class SoundManager {
  constructor() {
    this.audioContext = null;
    this.sounds = {};
    this.enabled = true;
    this.volume = 0.5;
    this.settings = {
      trade_executed: true,
      trade_copied: true,
      price_alert: true,
      risk_warning: true,
      ai_signal: true,
      achievement_unlocked: true,
      error_alert: false
    };
  }

  // Initialize audio context (must be called after user interaction)
  async init() {
    if (this.audioContext) return;
    
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      await this.loadSounds();
      console.log('[SoundManager] Initialized');
    } catch (error) {
      console.error('[SoundManager] Failed to initialize:', error);
    }
  }

  // Load default sounds (using oscillator-generated sounds for now)
  async loadSounds() {
    // We'll generate sounds programmatically for reliability
    this.sounds = {
      'success-chime': { frequency: 880, duration: 0.15, type: 'sine' },
      'cash-register': { frequency: 1000, duration: 0.1, type: 'square' },
      'notification': { frequency: 660, duration: 0.1, type: 'sine' },
      'bell': { frequency: 830, duration: 0.2, type: 'sine' },
      'alert': { frequency: 440, duration: 0.3, type: 'sawtooth' },
      'warning': { frequency: 330, duration: 0.4, type: 'triangle' },
      'alarm': { frequency: 550, duration: 0.5, type: 'square' },
      'digital': { frequency: 1200, duration: 0.08, type: 'square' },
      'tech': { frequency: 900, duration: 0.12, type: 'sine' },
      'ping': { frequency: 1400, duration: 0.05, type: 'sine' },
      'fanfare': { frequency: 523, duration: 0.3, type: 'sine' },
      'celebration': { frequency: 698, duration: 0.25, type: 'sine' },
      'level-up': { frequency: 784, duration: 0.2, type: 'sine' },
      'victory': { frequency: 880, duration: 0.35, type: 'sine' },
      'error': { frequency: 200, duration: 0.3, type: 'sawtooth' },
      'buzz': { frequency: 150, duration: 0.2, type: 'square' },
      'beep': { frequency: 800, duration: 0.1, type: 'square' },
      'pop': { frequency: 600, duration: 0.05, type: 'sine' },
      'ding': { frequency: 1000, duration: 0.15, type: 'sine' },
      'swoosh': { frequency: 400, duration: 0.2, type: 'triangle' }
    };
  }

  // Play a sound by name
  play(soundName) {
    if (!this.enabled || !this.audioContext) return;
    
    const sound = this.sounds[soundName];
    if (!sound) {
      console.warn(`[SoundManager] Sound not found: ${soundName}`);
      return;
    }

    try {
      // Resume audio context if suspended
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();
      
      oscillator.type = sound.type;
      oscillator.frequency.setValueAtTime(sound.frequency, this.audioContext.currentTime);
      
      gainNode.gain.setValueAtTime(this.volume, this.audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(
        0.01, 
        this.audioContext.currentTime + sound.duration
      );
      
      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      oscillator.start(this.audioContext.currentTime);
      oscillator.stop(this.audioContext.currentTime + sound.duration);
    } catch (error) {
      console.error('[SoundManager] Error playing sound:', error);
    }
  }

  // Play alert by type
  playAlert(alertType) {
    if (!this.settings[alertType]) return;

    const soundMap = {
      trade_executed: 'cash-register',
      trade_copied: 'notification',
      price_alert: 'alert',
      risk_warning: 'warning',
      ai_signal: 'digital',
      achievement_unlocked: 'fanfare',
      error_alert: 'error'
    };

    const soundName = soundMap[alertType];
    if (soundName) {
      this.play(soundName);
    }
  }

  // Convenience methods
  playTradeExecuted() { this.playAlert('trade_executed'); }
  playTradeCopied() { this.playAlert('trade_copied'); }
  playPriceAlert() { this.playAlert('price_alert'); }
  playRiskWarning() { this.playAlert('risk_warning'); }
  playAISignal() { this.playAlert('ai_signal'); }
  playAchievement() { this.playAlert('achievement_unlocked'); }
  playError() { this.playAlert('error_alert'); }

  // Settings
  setEnabled(enabled) {
    this.enabled = enabled;
    localStorage.setItem('sound_enabled', JSON.stringify(enabled));
  }

  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    localStorage.setItem('sound_volume', JSON.stringify(this.volume));
  }

  updateSettings(settings) {
    this.settings = { ...this.settings, ...settings };
    localStorage.setItem('sound_settings', JSON.stringify(this.settings));
  }

  loadSettings() {
    try {
      const enabled = localStorage.getItem('sound_enabled');
      const volume = localStorage.getItem('sound_volume');
      const settings = localStorage.getItem('sound_settings');

      if (enabled !== null) this.enabled = JSON.parse(enabled);
      if (volume !== null) this.volume = JSON.parse(volume);
      if (settings !== null) this.settings = { ...this.settings, ...JSON.parse(settings) };
    } catch (error) {
      console.error('[SoundManager] Error loading settings:', error);
    }
  }

  // Test all sounds
  async testAllSounds() {
    if (!this.audioContext) await this.init();
    
    const soundNames = Object.keys(this.sounds);
    for (let i = 0; i < soundNames.length; i++) {
      this.play(soundNames[i]);
      await new Promise(resolve => setTimeout(resolve, 400));
    }
  }
}

// Singleton instance
export const soundManager = new SoundManager();

// Initialize on first user interaction
if (typeof window !== 'undefined') {
  const initOnInteraction = async () => {
    await soundManager.init();
    soundManager.loadSettings();
    window.removeEventListener('click', initOnInteraction);
    window.removeEventListener('keydown', initOnInteraction);
  };
  
  window.addEventListener('click', initOnInteraction, { once: true });
  window.addEventListener('keydown', initOnInteraction, { once: true });
}

export default soundManager;
