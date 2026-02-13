import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import api from '../services/api';
import toast from '../utils/toast';
import { 
  Mail, Clock, Calendar, Send, Eye, History, 
  TrendingUp, PieChart, Bot, Newspaper, Save, RefreshCcw,
  CheckCircle, AlertCircle, AlertTriangle, Key, Zap, Bell, Trash2, BellRing
} from 'lucide-react';
import { 
  requestNotificationPermission, 
  isPushSupported, 
  showLocalNotification 
} from '../services/pushNotifications';

const EmailDigest = ({ embedded = false }) => {
  const [settings, setSettings] = useState({
    email: '',
    enabled: true,
    daily_digest: true,
    weekly_digest: true,
    daily_time: '08:00',
    weekly_day: 0,
    include_pnl: true,
    include_trades: true,
    include_ai_insights: true,
    include_market_summary: true
  });
  const [digestHistory, setDigestHistory] = useState([]);
  const [previewDigest, setPreviewDigest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  
  // Error Alerting State
  const [alertConfig, setAlertConfig] = useState({
    resend_api_key: '',
    recipient_emails: [],
    enabled: false,
    thresholds: {
      errors_per_hour: 50,
      critical_errors_trigger: 5
    },
    cooldown_minutes: 30,
    push_notifications_enabled: false
  });
  const [alertStatus, setAlertStatus] = useState(null);
  const [alertHistory, setAlertHistory] = useState([]);
  const [savingAlerts, setSavingAlerts] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [newRecipientEmail, setNewRecipientEmail] = useState('');
  const [pushSupported, setPushSupported] = useState(false);
  const [pushPermission, setPushPermission] = useState('default');

  const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const TIMES = Array.from({ length: 24 }, (_, i) => {
    const hour = i.toString().padStart(2, '0');
    return { value: `${hour}:00`, label: `${hour}:00 UTC` };
  });

  useEffect(() => {
    loadSettings();
    loadHistory();
    loadAlertConfig();
    loadAlertHistory();
    
    // Check push notification support
    setPushSupported(isPushSupported());
    if ('Notification' in window) {
      setPushPermission(Notification.permission);
    }
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/email-digest/settings');
      if (response.data.configured) {
        setSettings(prev => ({ ...prev, ...response.data }));
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await api.get('/email-digest/history');
      setDigestHistory(response.data.digests || []);
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };
  
  // Error Alerting Functions
  const loadAlertConfig = async () => {
    try {
      const response = await api.get('/error-alerting/config');
      setAlertConfig(prev => ({ 
        ...prev, 
        ...response.data,
        resend_api_key: '' // Don't populate key for security
      }));
      setAlertStatus(response.data);
    } catch (error) {
      console.error('Error loading alert config:', error);
    }
  };
  
  const loadAlertHistory = async () => {
    try {
      const response = await api.get('/error-alerting/history');
      setAlertHistory(response.data.alerts || []);
    } catch (error) {
      console.error('Error loading alert history:', error);
    }
  };
  
  const saveAlertConfig = async () => {
    setSavingAlerts(true);
    try {
      const configToSave = { ...alertConfig };
      // Only include API key if it's been changed
      if (!configToSave.resend_api_key) {
        delete configToSave.resend_api_key;
      }
      await api.post('/error-alerting/config', configToSave);
      toast.success('Error alert settings saved');
      loadAlertConfig();
    } catch (error) {
      toast.error('Failed to save alert settings', { description: error.message });
    } finally {
      setSavingAlerts(false);
    }
  };
  
  const enablePushNotifications = async () => {
    try {
      const result = await requestNotificationPermission();
      setPushPermission(result.granted ? 'granted' : 'denied');
      
      if (result.granted) {
        setAlertConfig(prev => ({ ...prev, push_notifications_enabled: true }));
        toast.success('Push notifications enabled!');
        
        // Send test notification
        await showLocalNotification('🔔 Notifications Enabled', {
          body: 'You will now receive push notifications for error alerts',
          tag: 'push-enabled'
        });
      } else {
        toast.error('Push notifications blocked', { 
          description: 'Please enable notifications in your browser settings' 
        });
      }
    } catch (error) {
      toast.error('Failed to enable push notifications');
    }
  };
  
  const testPushNotification = async () => {
    const sent = await showLocalNotification('🚨 Test Error Alert', {
      body: 'This is a test error alert notification',
      tag: 'test-alert',
      vibrate: [200, 100, 200, 100, 400],
      requireInteraction: true
    });
    
    if (sent) {
      toast.success('Test notification sent!');
    } else {
      toast.error('Could not send test notification');
    }
  };
  
  const testResendConnection = async () => {
    if (!alertConfig.resend_api_key) {
      toast.error('Please enter your Resend API key first');
      return;
    }
    if (!newRecipientEmail && alertConfig.recipient_emails.length === 0) {
      toast.error('Please add a recipient email first');
      return;
    }
    
    setTestingConnection(true);
    try {
      const testEmail = newRecipientEmail || alertConfig.recipient_emails[0];
      await api.post('/error-alerting/test-connection', {
        api_key: alertConfig.resend_api_key,
        recipient_email: testEmail
      });
      toast.success('Test email sent!', { description: `Check ${testEmail}` });
    } catch (error) {
      toast.error('Connection test failed', { description: error.response?.data?.detail || error.message });
    } finally {
      setTestingConnection(false);
    }
  };
  
  const addRecipientEmail = () => {
    if (!newRecipientEmail || !newRecipientEmail.includes('@')) {
      toast.error('Please enter a valid email');
      return;
    }
    if (alertConfig.recipient_emails.includes(newRecipientEmail)) {
      toast.error('Email already added');
      return;
    }
    setAlertConfig(prev => ({
      ...prev,
      recipient_emails: [...prev.recipient_emails, newRecipientEmail]
    }));
    setNewRecipientEmail('');
  };
  
  const removeRecipientEmail = (email) => {
    setAlertConfig(prev => ({
      ...prev,
      recipient_emails: prev.recipient_emails.filter(e => e !== email)
    }));
  };

  const saveSettings = async () => {
    if (!settings.email) {
      toast.error('Please enter your email address');
      return;
    }
    
    setSaving(true);
    try {
      await api.post('/email-digest/settings', settings);
      toast.success('Email digest settings saved');
    } catch (error) {
      toast.error('Failed to save settings', { description: error.message });
    } finally {
      setSaving(false);
    }
  };

  const generateDailyDigest = async () => {
    setGenerating(true);
    try {
      const response = await api.post('/email-digest/generate-daily');
      setPreviewDigest(response.data);
      toast.success('Daily digest generated');
      loadHistory();
    } catch (error) {
      toast.error('Failed to generate digest');
    } finally {
      setGenerating(false);
    }
  };

  const generateWeeklyDigest = async () => {
    setGenerating(true);
    try {
      const response = await api.post('/email-digest/generate-weekly');
      setPreviewDigest(response.data);
      toast.success('Weekly digest generated');
      loadHistory();
    } catch (error) {
      toast.error('Failed to generate digest');
    } finally {
      setGenerating(false);
    }
  };

  const sendTestEmail = async () => {
    if (!settings.email) {
      toast.error('Please enter your email address first');
      return;
    }
    
    setSendingTest(true);
    try {
      const response = await api.post('/email-digest/send-test');
      toast.success('Test email generated', { 
        description: response.data.note || 'Check your inbox'
      });
      setPreviewDigest(response.data.digest_preview);
    } catch (error) {
      toast.error('Failed to send test email', { description: error.response?.data?.detail });
    } finally {
      setSendingTest(false);
    }
  };

  const viewDigest = async (digestId) => {
    try {
      const response = await api.get(`/email-digest/preview/${digestId}`);
      setPreviewDigest(response.data);
    } catch (error) {
      toast.error('Failed to load digest');
    }
  };

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
        className="max-w-5xl mx-auto space-y-6"
      >
        {!embedded && (
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Email Digest</h1>
              <p className="text-slate-400">Receive daily and weekly trading summaries</p>
            </div>
            <Badge variant="outline" className="text-cyan-400 border-cyan-400/50">
              <Mail className="w-3 h-3 mr-1" />
              Email Reports
            </Badge>
          </div>
        )}

        <Tabs defaultValue="settings" className="space-y-6">
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="settings">Digest Settings</TabsTrigger>
            <TabsTrigger value="alerts">Error Alerts</TabsTrigger>
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            {/* Email Configuration */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Mail className="w-5 h-5 text-cyan-400" />
                  Email Configuration
                </CardTitle>
                <CardDescription>Configure your email digest delivery</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label className="text-white">Email Address</Label>
                  <Input
                    type="email"
                    placeholder="your@email.com"
                    value={settings.email}
                    onChange={(e) => setSettings(prev => ({ ...prev, email: e.target.value }))}
                    className="bg-slate-900 border-slate-600"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-white">Enable Email Digests</Label>
                    <p className="text-sm text-slate-400">Receive trading summaries via email</p>
                  </div>
                  <Switch
                    checked={settings.enabled}
                    onCheckedChange={(checked) => setSettings(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Schedule */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Daily Digest */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Clock className="w-5 h-5 text-green-400" />
                    Daily Digest
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Enable Daily Digest</Label>
                    <Switch
                      checked={settings.daily_digest}
                      onCheckedChange={(checked) => setSettings(prev => ({ ...prev, daily_digest: checked }))}
                      disabled={!settings.enabled}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-400 text-sm">Delivery Time</Label>
                    <Select
                      value={settings.daily_time}
                      onValueChange={(value) => setSettings(prev => ({ ...prev, daily_time: value }))}
                      disabled={!settings.enabled || !settings.daily_digest}
                    >
                      <SelectTrigger className="bg-slate-900 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TIMES.map(({ value, label }) => (
                          <SelectItem key={value} value={value}>{label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button 
                    onClick={generateDailyDigest} 
                    variant="outline" 
                    className="w-full"
                    disabled={generating}
                  >
                    {generating ? <RefreshCcw className="w-4 h-4 mr-2 animate-spin" /> : <Eye className="w-4 h-4 mr-2" />}
                    Generate Preview
                  </Button>
                </CardContent>
              </Card>

              {/* Weekly Digest */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Calendar className="w-5 h-5 text-purple-400" />
                    Weekly Digest
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-white">Enable Weekly Digest</Label>
                    <Switch
                      checked={settings.weekly_digest}
                      onCheckedChange={(checked) => setSettings(prev => ({ ...prev, weekly_digest: checked }))}
                      disabled={!settings.enabled}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-400 text-sm">Delivery Day</Label>
                    <Select
                      value={settings.weekly_day.toString()}
                      onValueChange={(value) => setSettings(prev => ({ ...prev, weekly_day: parseInt(value) }))}
                      disabled={!settings.enabled || !settings.weekly_digest}
                    >
                      <SelectTrigger className="bg-slate-900 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DAYS.map((day, index) => (
                          <SelectItem key={index} value={index.toString()}>{day}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button 
                    onClick={generateWeeklyDigest} 
                    variant="outline" 
                    className="w-full"
                    disabled={generating}
                  >
                    {generating ? <RefreshCcw className="w-4 h-4 mr-2 animate-spin" /> : <Eye className="w-4 h-4 mr-2" />}
                    Generate Preview
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Content Options */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Content Options</CardTitle>
                <CardDescription>Choose what to include in your digests</CardDescription>
              </CardHeader>
              <CardContent className="grid md:grid-cols-2 gap-4">
                {[
                  { key: 'include_pnl', label: 'P&L Summary', icon: TrendingUp, color: 'green' },
                  { key: 'include_trades', label: 'Trade History', icon: History, color: 'blue' },
                  { key: 'include_ai_insights', label: 'AI Insights', icon: Bot, color: 'purple' },
                  { key: 'include_market_summary', label: 'Market Summary', icon: Newspaper, color: 'amber' }
                ].map(({ key, label, icon: Icon, color }) => (
                  <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg bg-${color}-500/20`}>
                        <Icon className={`w-4 h-4 text-${color}-400`} />
                      </div>
                      <Label className="text-white">{label}</Label>
                    </div>
                    <Switch
                      checked={settings[key]}
                      onCheckedChange={(checked) => setSettings(prev => ({ ...prev, [key]: checked }))}
                      disabled={!settings.enabled}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex gap-4">
              <Button onClick={saveSettings} className="flex-1" disabled={saving}>
                {saving ? <RefreshCcw className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save Settings
              </Button>
              <Button onClick={sendTestEmail} variant="outline" className="flex-1" disabled={sendingTest}>
                {sendingTest ? <RefreshCcw className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
                Send Test Email
              </Button>
            </div>
          </TabsContent>

          {/* Error Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            {/* Resend API Configuration */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Key className="w-5 h-5 text-purple-400" />
                  Resend API Configuration
                </CardTitle>
                <CardDescription>
                  Configure Resend to receive error alerts via email.{' '}
                  <a 
                    href="https://resend.com" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-purple-400 hover:underline"
                  >
                    Get API key from Resend →
                  </a>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label className="text-white">Resend API Key</Label>
                  <div className="flex gap-2">
                    <Input
                      type="password"
                      placeholder="re_..."
                      value={alertConfig.resend_api_key}
                      onChange={(e) => setAlertConfig(prev => ({ ...prev, resend_api_key: e.target.value }))}
                      className="bg-slate-900 border-slate-600 font-mono"
                    />
                    <Button
                      onClick={testResendConnection}
                      disabled={testingConnection || !alertConfig.resend_api_key}
                      variant="outline"
                      className="border-purple-500/50 text-purple-400"
                    >
                      {testingConnection ? (
                        <RefreshCcw className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Zap className="w-4 h-4 mr-1" />
                          Test
                        </>
                      )}
                    </Button>
                  </div>
                  {alertStatus?.has_api_key && (
                    <p className="text-sm text-green-400 flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      API key configured: {alertStatus.resend_api_key_masked}
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-white">Enable Error Alerts</Label>
                    <p className="text-sm text-slate-400">Receive email when error thresholds are exceeded</p>
                  </div>
                  <Switch
                    checked={alertConfig.enabled}
                    onCheckedChange={(checked) => setAlertConfig(prev => ({ ...prev, enabled: checked }))}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Push Notifications */}
            {pushSupported && (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <BellRing className="w-5 h-5 text-yellow-400" />
                    Push Notifications
                  </CardTitle>
                  <CardDescription>
                    Receive browser notifications for error alerts
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-white">Enable Push Notifications</Label>
                      <p className="text-sm text-slate-400">
                        Get instant alerts even when the app is in background
                      </p>
                    </div>
                    {pushPermission === 'granted' ? (
                      <div className="flex items-center gap-2">
                        <Badge className="bg-green-500/20 text-green-400">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Enabled
                        </Badge>
                        <Button
                          onClick={testPushNotification}
                          variant="outline"
                          size="sm"
                          className="border-yellow-500/50 text-yellow-400"
                        >
                          Test
                        </Button>
                      </div>
                    ) : pushPermission === 'denied' ? (
                      <Badge className="bg-red-500/20 text-red-400">
                        Blocked
                      </Badge>
                    ) : (
                      <Button
                        onClick={enablePushNotifications}
                        variant="outline"
                        className="border-yellow-500/50 text-yellow-400"
                      >
                        <BellRing className="w-4 h-4 mr-2" />
                        Enable
                      </Button>
                    )}
                  </div>
                  
                  {pushPermission === 'denied' && (
                    <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <p className="text-sm text-red-400">
                        Push notifications are blocked. To enable them, click the lock icon in your browser's address bar and allow notifications.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Recipient Emails */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Mail className="w-5 h-5 text-cyan-400" />
                  Alert Recipients
                </CardTitle>
                <CardDescription>
                  Add email addresses to receive error alerts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="alert@example.com"
                    value={newRecipientEmail}
                    onChange={(e) => setNewRecipientEmail(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addRecipientEmail()}
                    className="bg-slate-900 border-slate-600"
                  />
                  <Button onClick={addRecipientEmail} variant="outline" className="border-cyan-500/50">
                    Add
                  </Button>
                </div>
                
                <div className="space-y-2">
                  {alertConfig.recipient_emails.map((email) => (
                    <div key={email} className="flex items-center justify-between bg-slate-900/50 p-3 rounded-lg">
                      <span className="text-white">{email}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeRecipientEmail(email)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                  {alertConfig.recipient_emails.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">No recipients added yet</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Alert Thresholds */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  Alert Thresholds
                </CardTitle>
                <CardDescription>
                  Configure when to trigger error alerts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label className="text-white">Errors per Hour</Label>
                    <Input
                      type="number"
                      min="10"
                      max="500"
                      value={alertConfig.thresholds?.errors_per_hour ?? 50}
                      onChange={(e) => setAlertConfig(prev => ({
                        ...prev,
                        thresholds: { ...prev.thresholds, errors_per_hour: parseInt(e.target.value) || 50 }
                      }))}
                      className="bg-slate-900 border-slate-600"
                    />
                    <p className="text-xs text-slate-500">Alert when errors exceed this count in 1 hour</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-white">Critical Errors Trigger</Label>
                    <Input
                      type="number"
                      min="1"
                      max="50"
                      value={alertConfig.thresholds?.critical_errors_trigger ?? 5}
                      onChange={(e) => setAlertConfig(prev => ({
                        ...prev,
                        thresholds: { ...prev.thresholds, critical_errors_trigger: parseInt(e.target.value) || 5 }
                      }))}
                      className="bg-slate-900 border-slate-600"
                    />
                    <p className="text-xs text-slate-500">Alert when critical errors reach this count</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-white">Cooldown (minutes)</Label>
                  <Select 
                    value={String(alertConfig.cooldown_minutes)} 
                    onValueChange={(v) => setAlertConfig(prev => ({ ...prev, cooldown_minutes: parseInt(v) }))}
                  >
                    <SelectTrigger className="bg-slate-900 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                      <SelectItem value="60">1 hour</SelectItem>
                      <SelectItem value="120">2 hours</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">Minimum time between alerts</p>
                </div>
              </CardContent>
            </Card>

            {/* Alert History */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Bell className="w-5 h-5 text-orange-400" />
                  Recent Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                {alertHistory.length > 0 ? (
                  <div className="space-y-2">
                    {alertHistory.slice(0, 5).map((alert, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-slate-900/50 p-3 rounded-lg">
                        <div>
                          <p className="text-white text-sm">
                            {alert.triggers?.map(t => t.type.replace('_', ' ')).join(', ') || 'Alert triggered'}
                          </p>
                          <p className="text-xs text-slate-500">
                            {new Date(alert.sent_at).toLocaleString()}
                          </p>
                        </div>
                        <Badge variant="outline" className="text-orange-400">
                          {alert.recipients?.length || 0} sent
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-4">No alerts sent yet</p>
                )}
              </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex justify-end">
              <Button
                onClick={saveAlertConfig}
                disabled={savingAlerts}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {savingAlerts ? (
                  <RefreshCcw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Save Alert Settings
              </Button>
            </div>
          </TabsContent>

          {/* Preview Tab */}
          <TabsContent value="preview">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Digest Preview</CardTitle>
                <CardDescription>
                  {previewDigest ? `Generated at ${new Date(previewDigest.generated_at).toLocaleString()}` : 'Generate a digest to see preview'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {previewDigest ? (
                  <div className="space-y-6">
                    <div className="flex items-center gap-2">
                      <Badge className={previewDigest.type === 'daily' ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'}>
                        {previewDigest.type === 'daily' ? 'Daily Digest' : 'Weekly Digest'}
                      </Badge>
                      <span className="text-slate-400 text-sm">
                        {previewDigest.date || `${previewDigest.week_start} - ${previewDigest.week_end}`}
                      </span>
                    </div>

                    {/* Summary */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 rounded-lg bg-slate-900/50">
                        <p className="text-slate-400 text-sm">Portfolio Value</p>
                        <p className="text-xl font-bold text-white">
                          ${(previewDigest?.summary?.portfolio_value ?? 0).toLocaleString() || '0'}
                        </p>
                      </div>
                      <div className="p-4 rounded-lg bg-slate-900/50">
                        <p className="text-slate-400 text-sm">Total Trades</p>
                        <p className="text-xl font-bold text-white">{previewDigest.summary?.total_trades || 0}</p>
                      </div>
                      <div className="p-4 rounded-lg bg-slate-900/50">
                        <p className="text-slate-400 text-sm">Total P&L</p>
                        <p className={`text-xl font-bold ${(previewDigest.summary?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          ${(previewDigest?.summary?.total_pnl ?? 0).toFixed(2) || '0'}
                        </p>
                      </div>
                      <div className="p-4 rounded-lg bg-slate-900/50">
                        <p className="text-slate-400 text-sm">Win Rate</p>
                        <p className="text-xl font-bold text-white">{previewDigest.summary?.win_rate || 0}%</p>
                      </div>
                    </div>

                    {/* AI Insights */}
                    {previewDigest.ai_insights && previewDigest.ai_insights.length > 0 && (
                      <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                        <h4 className="font-medium text-purple-400 mb-2 flex items-center gap-2">
                          <Bot className="w-4 h-4" />
                          AI Insights
                        </h4>
                        <ul className="space-y-1">
                          {previewDigest.ai_insights.map((insight, i) => (
                            <li key={i} className="text-sm text-slate-300">• {insight}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Mail className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No digest generated yet</p>
                    <p className="text-sm text-slate-500 mt-2">Click "Generate Preview" in the settings tab</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Digest History</CardTitle>
                <CardDescription>Previously generated digests</CardDescription>
              </CardHeader>
              <CardContent>
                {digestHistory.length > 0 ? (
                  <div className="space-y-3">
                    {digestHistory.map((digest) => (
                      <motion.div
                        key={digest.digest_id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center justify-between p-4 rounded-lg bg-slate-900/50 hover:bg-slate-900/70 transition-colors cursor-pointer"
                        onClick={() => viewDigest(digest.digest_id)}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${digest.type === 'daily' ? 'bg-green-500/20' : 'bg-purple-500/20'}`}>
                            {digest.type === 'daily' ? (
                              <Clock className="w-5 h-5 text-green-400" />
                            ) : (
                              <Calendar className="w-5 h-5 text-purple-400" />
                            )}
                          </div>
                          <div>
                            <p className="text-white font-medium">
                              {digest.type === 'daily' ? 'Daily Digest' : 'Weekly Digest'}
                            </p>
                            <p className="text-sm text-slate-400">
                              {digest.date || `${digest.week_start} - ${digest.week_end}`}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant="outline" className="text-slate-400">
                            {digest.summary?.total_trades || 0} trades
                          </Badge>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <History className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No digests generated yet</p>
                    <p className="text-sm text-slate-500 mt-2">Generate your first digest to see it here</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Note about email delivery */}
        <Card className="bg-amber-500/10 border-amber-500/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5" />
              <div>
                <h4 className="font-medium text-amber-400">Email Delivery Note</h4>
                <p className="text-sm text-slate-400 mt-1">
                  Email delivery requires SMTP configuration. Currently, digests are generated and stored for preview. 
                  Contact support to enable email delivery to your inbox.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default EmailDigest;
