import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import api from '../services/api';
import toast from '../utils/toast';
import { 
  Volume2, VolumeX, Bell, TrendingUp, AlertTriangle, 
  Bot, Trophy, XCircle, Play, Save, RefreshCcw 
} from 'lucide-react';

const SoundSettings = ({ embedded = false }) => {
  const [settings, setSettings] = useState({
    enabled: true,
    volume: 0.5,
    trade_executed: true,
    trade_copied: true,
    price_alert: true,
    risk_warning: true,
    ai_signal: true,
    achievement_unlocked: true,
    error_alert: false,
    sound_choices: {}
  });
  const [availableSounds, setAvailableSounds] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    loadSettings();
    loadAvailableSounds();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/sound-settings/');
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading sound settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSounds = async () => {
    try {
      const response = await api.get('/sound-settings/available-sounds');
      setAvailableSounds(response.data.sounds || {});
    } catch (error) {
      console.error('Error loading available sounds:', error);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await api.post('/sound-settings/', {
        enabled: settings.enabled,
        volume: settings.volume,
        trade_executed: settings.trade_executed,
        trade_copied: settings.trade_copied,
        price_alert: settings.price_alert,
        risk_warning: settings.risk_warning,
        ai_signal: settings.ai_signal,
        achievement_unlocked: settings.achievement_unlocked,
        error_alert: settings.error_alert
      });
      toast.success('Sound settings saved');
    } catch (error) {
      toast.error('Failed to save settings', { description: error.message });
    } finally {
      setSaving(false);
    }
  };

  const toggleSetting = async (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    try {
      await api.post(`/sound-settings/toggle/${key}`, null, {
        params: { enabled: value }
      });
    } catch (error) {
      console.error('Error toggling setting:', error);
    }
  };

  const setVolume = async (value) => {
    const volume = value[0];
    setSettings(prev => ({ ...prev, volume }));
    try {
      await api.post('/sound-settings/volume', null, {
        params: { volume }
      });
    } catch (error) {
      console.error('Error setting volume:', error);
    }
  };

  const setSoundChoice = async (alertType, soundName) => {
    setSettings(prev => ({
      ...prev,
      sound_choices: { ...prev.sound_choices, [alertType]: soundName }
    }));
    try {
      await api.post('/sound-settings/sound-choice', null, {
        params: { alert_type: alertType, sound_name: soundName }
      });
      toast.success(`Sound updated for ${alertType.replace('_', ' ')}`);
    } catch (error) {
      toast.error('Failed to update sound');
    }
  };

  const playTestSound = () => {
    // Create a simple beep sound
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    gainNode.gain.value = settings.volume;
    
    oscillator.start();
    setTimeout(() => {
      oscillator.stop();
    }, 200);
    
    toast.success('Test sound played', { description: `Volume: ${Math.round(settings.volume * 100)}%` });
  };

  const alertTypes = [
    { key: 'trade_executed', label: 'Trade Executed', icon: TrendingUp, color: 'green', description: 'When a trade is successfully executed' },
    { key: 'trade_copied', label: 'Trade Copied', icon: TrendingUp, color: 'blue', description: 'When a copy trade is executed' },
    { key: 'price_alert', label: 'Price Alert', icon: Bell, color: 'yellow', description: 'When a price alert triggers' },
    { key: 'risk_warning', label: 'Risk Warning', icon: AlertTriangle, color: 'red', description: 'For risk alerts (drawdown, exposure)' },
    { key: 'ai_signal', label: 'AI Signal', icon: Bot, color: 'purple', description: 'When AI generates a trading signal' },
    { key: 'achievement_unlocked', label: 'Achievement', icon: Trophy, color: 'amber', description: 'When earning a badge or achievement' },
    { key: 'error_alert', label: 'Error Alert', icon: XCircle, color: 'slate', description: 'When an error occurs' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
      </div>
    );
  }

  return (
    <div className={embedded ? '' : 'min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6'}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto space-y-6"
      >
        {!embedded && (
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Sound Settings</h1>
              <p className="text-slate-400">Configure audio alerts and notifications</p>
            </div>
            <Badge variant="outline" className="text-cyan-400 border-cyan-400/50">
              <Volume2 className="w-3 h-3 mr-1" />
              Audio Alerts
            </Badge>
          </div>
        )}

        {/* Master Controls */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              {settings.enabled ? <Volume2 className="w-5 h-5 text-green-400" /> : <VolumeX className="w-5 h-5 text-red-400" />}
              Master Controls
            </CardTitle>
            <CardDescription>Global sound settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white">Enable Sound Alerts</Label>
                <p className="text-sm text-slate-400">Turn all sound alerts on or off</p>
              </div>
              <Switch
                checked={settings.enabled}
                onCheckedChange={(checked) => toggleSetting('enabled', checked)}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-white">Volume Level</Label>
                <span className="text-sm text-slate-400">{Math.round(settings.volume * 100)}%</span>
              </div>
              <div className="flex items-center gap-4">
                <VolumeX className="w-4 h-4 text-slate-400" />
                <Slider
                  value={[settings.volume]}
                  onValueChange={setVolume}
                  max={1}
                  step={0.1}
                  className="flex-1"
                  disabled={!settings.enabled}
                />
                <Volume2 className="w-4 h-4 text-slate-400" />
              </div>
            </div>

            <div className="flex gap-3">
              <Button 
                onClick={playTestSound} 
                variant="outline" 
                className="flex-1"
                disabled={!settings.enabled}
              >
                <Play className="w-4 h-4 mr-2" />
                Test Sound
              </Button>
              <Button onClick={saveSettings} className="flex-1" disabled={saving}>
                {saving ? (
                  <RefreshCcw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Save Settings
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Individual Alert Settings */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Alert Types</CardTitle>
            <CardDescription>Configure sounds for different alert types</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {alertTypes.map(({ key, label, icon: Icon, color, description }) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`p-4 rounded-lg bg-slate-900/50 border border-slate-700 ${!settings.enabled ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-${color}-500/20`}>
                      <Icon className={`w-5 h-5 text-${color}-400`} />
                    </div>
                    <div>
                      <Label className="text-white">{label}</Label>
                      <p className="text-xs text-slate-400">{description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {availableSounds[key] && (
                      <Select
                        value={settings.sound_choices?.[key] || availableSounds[key]?.default_sound}
                        onValueChange={(value) => setSoundChoice(key, value)}
                        disabled={!settings.enabled || !settings[key]}
                      >
                        <SelectTrigger className="w-32 bg-slate-800 border-slate-600">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {availableSounds[key]?.options?.map((sound) => (
                            <SelectItem key={sound} value={sound}>
                              {sound.replace('-', ' ')}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                    <Switch
                      checked={settings[key]}
                      onCheckedChange={(checked) => toggleSetting(key, checked)}
                      disabled={!settings.enabled}
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>

        {/* Tips */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Bell className="w-5 h-5 text-cyan-400 mt-0.5" />
              <div>
                <h4 className="font-medium text-white">Sound Alert Tips</h4>
                <ul className="text-sm text-slate-400 mt-2 space-y-1">
                  <li>• Sounds require browser audio permission - click anywhere on the page to enable</li>
                  <li>• Risk warnings help you stay aware of portfolio exposure</li>
                  <li>• AI signals notify you of automated trading opportunities</li>
                  <li>• Achievement sounds provide positive feedback on milestones</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default SoundSettings;
