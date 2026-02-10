import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { motion } from 'framer-motion';
import api, { authAPI, riskAPI } from '../services/api';
import toast from '../utils/toast';
import { Shield, Key, Settings as SettingsIcon, Bell, Smartphone, Vibrate, Database, Link2, RefreshCcw } from 'lucide-react';

const Settings = () => {
  // Kraken credentials
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [hasCredentials, setHasCredentials] = useState(false);
  
  // Binance credentials
  const [binanceApiKey, setBinanceApiKey] = useState('');
  const [binanceApiSecret, setBinanceApiSecret] = useState('');
  const [hasBinanceCredentials, setHasBinanceCredentials] = useState(false);
  
  // Crypto.com credentials (best for arbitrage - US friendly)
  const [cryptoComApiKey, setCryptoComApiKey] = useState('');
  const [cryptoComApiSecret, setCryptoComApiSecret] = useState('');
  const [hasCryptoComCredentials, setHasCryptoComCredentials] = useState(false);
  
  const [riskSettings, setRiskSettings] = useState({
    max_investment_per_trade: 1000,
    stop_loss_percentage: 5,
    take_profit_percentage: 15,
    max_daily_trades: 10,
    max_portfolio_allocation: 20,
    risk_level: 'medium'
  });
  const [notificationSettings, setNotificationSettings] = useState({
    push_enabled: true,
    vibration_enabled: true,
    notify_trade_open: true,
    notify_trade_close: true,
    notify_high_alerts: true,
    notify_medium_alerts: false,
    notify_ai_discoveries: true
  });
  
  // Data Provider API Keys
  const [dataProviderKeys, setDataProviderKeys] = useState({
    blockchair_api_key: '',
    glassnode_api_key: '',
    cryptoquant_api_key: '',
    coinglass_api_key: '',
    santiment_api_key: ''
  });
  const [dataProviderStatus, setDataProviderStatus] = useState({});
  const [universeStats, setUniverseStats] = useState(null);
  const [syncingUniverse, setSyncingUniverse] = useState(false);
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkCredentials();
    checkBinanceCredentials();
    checkCryptoComCredentials();
    loadRiskSettings();
    loadNotificationSettings();
    loadDataProviderStatus();
    loadUniverseStats();
  }, []);

  const checkCredentials = async () => {
    try {
      const response = await authAPI.checkCredentials();
      setHasCredentials(response.data.has_credentials);
    } catch (error) {
      console.error('Error checking credentials:', error);
    }
  };

  const checkBinanceCredentials = async () => {
    try {
      const response = await api.get('/auth/binance/check');
      setHasBinanceCredentials(response.data.has_credentials);
    } catch (error) {
      console.error('Error checking Binance credentials:', error);
    }
  };

  const checkCryptoComCredentials = async () => {
    try {
      const response = await api.get('/auth/crypto-com/check');
      setHasCryptoComCredentials(response.data.has_credentials);
    } catch (error) {
      console.error('Error checking Crypto.com credentials:', error);
    }
  };

  const loadRiskSettings = async () => {
    try {
      const response = await riskAPI.getSettings();
      if (response.data) {
        setRiskSettings(response.data);
      }
    } catch (error) {
      console.error('Error loading risk settings:', error);
    }
  };

  const loadNotificationSettings = async () => {
    try {
      const response = await api.get('/notifications/settings');
      if (response.data) {
        setNotificationSettings(response.data);
      }
    } catch (error) {
      console.error('Error loading notification settings:', error);
    }
  };

  const saveCredentials = async () => {
    if (!apiKey || !apiSecret) {
      toast.error('Missing credentials', {
        description: 'Please enter both API key and secret',
      });
      return;
    }

    const loadingToast = toast.loading('Saving API credentials...');
    try {
      setLoading(true);
      await authAPI.storeCredentials(apiKey, apiSecret);
      toast.dismiss(loadingToast);
      toast.success('API credentials saved!', {
        description: 'Your Kraken credentials are now active',
        duration: 5000,
      });
      setHasCredentials(true);
      setApiKey('');
      setApiSecret('');
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save credentials', {
        description: error.response?.data?.detail || 'Please check your API key and secret',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveBinanceCredentials = async () => {
    if (!binanceApiKey || !binanceApiSecret) {
      toast.error('Missing Binance credentials', {
        description: 'Please enter both API key and secret',
      });
      return;
    }

    const loadingToast = toast.loading('Saving Binance credentials...');
    try {
      setLoading(true);
      await api.post('/auth/binance/store', {
        api_key: binanceApiKey,
        api_secret: binanceApiSecret
      });
      toast.dismiss(loadingToast);
      toast.success('Binance credentials saved!', {
        description: 'Your Binance exchange is now connected',
        duration: 5000,
      });
      setHasBinanceCredentials(true);
      setBinanceApiKey('');
      setBinanceApiSecret('');
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save Binance credentials', {
        description: error.response?.data?.detail || 'Please check your API key and secret',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveCryptoComCredentials = async () => {
    if (!cryptoComApiKey || !cryptoComApiSecret) {
      toast.error('Missing Crypto.com credentials', {
        description: 'Please enter both API key and secret',
      });
      return;
    }

    const loadingToast = toast.loading('Saving Crypto.com credentials...');
    try {
      setLoading(true);
      await api.post('/auth/crypto-com/store', {
        api_key: cryptoComApiKey,
        api_secret: cryptoComApiSecret
      });
      toast.dismiss(loadingToast);
      toast.success('Crypto.com credentials saved!', {
        description: 'Your Crypto.com exchange is now connected for arbitrage',
        duration: 5000,
      });
      setHasCryptoComCredentials(true);
      setCryptoComApiKey('');
      setCryptoComApiSecret('');
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save Crypto.com credentials', {
        description: error.response?.data?.detail || 'Please check your credentials',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveRiskSettings = async () => {
    const loadingToast = toast.loading('Updating risk settings...');
    try {
      setLoading(true);
      await riskAPI.updateSettings(riskSettings);
      toast.dismiss(loadingToast);
      toast.success('Risk settings updated!', {
        description: 'Your trading risk parameters have been saved',
        duration: 4000,
      });
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to update risk settings', {
        description: error.response?.data?.detail || 'Please try again',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveNotificationSettings = async () => {
    try {
      setLoading(true);
      await api.post('/notifications/settings', notificationSettings);
      toast.success('Notification settings updated!');
    } catch (error) {
      toast.error('Failed to update notification settings');
    } finally {
      setLoading(false);
    }
  };

  const testPushNotification = async () => {
    try {
      setLoading(true);
      const result = await api.post('/notifications/test-push', {
        title: 'Test Notification',
        body: 'This is a test push notification with vibration!',
        priority: 'high'
      });
      if (result.data.success) {
        toast.success('Test push notification sent!');
      } else {
        toast.error(result.data.error || 'Push notification failed');
      }
    } catch (error) {
      toast.error('Failed to send test notification');
    } finally {
      setLoading(false);
    }
  };

  // Data Provider Functions
  const loadDataProviderStatus = async () => {
    try {
      const response = await api.get('/enhanced-data/provider-keys/status');
      setDataProviderStatus(response.data);
    } catch (error) {
      console.error('Error loading data provider status:', error);
    }
  };

  const loadUniverseStats = async () => {
    try {
      const response = await api.get('/enhanced-data/kraken-universe/stats');
      setUniverseStats(response.data);
    } catch (error) {
      console.error('Error loading universe stats:', error);
    }
  };

  const saveDataProviderKeys = async () => {
    const loadingToast = toast.loading('Saving data provider API keys...');
    try {
      setLoading(true);
      // Only send non-empty keys
      const keysToSave = {};
      Object.entries(dataProviderKeys).forEach(([key, value]) => {
        if (value && value.trim()) {
          keysToSave[key] = value.trim();
        }
      });
      
      if (Object.keys(keysToSave).length === 0) {
        toast.dismiss(loadingToast);
        toast.warning('No API keys to save', {
          description: 'Enter at least one API key to save',
        });
        return;
      }
      
      await api.post('/enhanced-data/provider-keys/save', keysToSave);
      toast.dismiss(loadingToast);
      toast.success('Data provider API keys saved!', {
        description: 'Enhanced on-chain data will now be available',
        duration: 4000,
      });
      
      // Clear inputs and reload status
      setDataProviderKeys({
        blockchair_api_key: '',
        glassnode_api_key: '',
        cryptoquant_api_key: '',
        coinglass_api_key: '',
        santiment_api_key: ''
      });
      loadDataProviderStatus();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to save API keys', {
        description: error.response?.data?.detail || 'Please try again',
      });
    } finally {
      setLoading(false);
    }
  };

  const syncKrakenUniverse = async () => {
    const loadingToast = toast.loading('Syncing Kraken universe...');
    try {
      setSyncingUniverse(true);
      await api.get('/enhanced-data/kraken-universe/sync-now');
      toast.dismiss(loadingToast);
      toast.success('Kraken universe synced!', {
        description: 'All tradeable coins have been updated',
        duration: 4000,
      });
      loadUniverseStats();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to sync universe', {
        description: error.response?.data?.detail || 'Please try again',
      });
    } finally {
      setSyncingUniverse(false);
    }
  };

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="settings">
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="settings-title">
          <SettingsIcon className="inline mr-3" size={48} />
          Settings
        </h1>
        <p className="text-[#A1A1AA]">Configure your trading preferences and API credentials</p>
      </motion.div>

      <Tabs defaultValue="api" className="space-y-6" data-testid="settings-tabs">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="api" data-testid="api-tab">
            <Key size={16} className="mr-2" />
            API Credentials
          </TabsTrigger>
          <TabsTrigger value="risk" data-testid="risk-tab">
            <Shield size={16} className="mr-2" />
            Risk Management
          </TabsTrigger>
          <TabsTrigger value="notifications" data-testid="notifications-tab">
            <Bell size={16} className="mr-2" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* API Credentials Tab */}
        <TabsContent value="api">
          <div className="space-y-6">
            {/* Kraken */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="kraken-credentials-card">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#5741D9]/20 flex items-center justify-center">
                    <span className="text-lg font-bold text-[#5741D9]">K</span>
                  </div>
                  <div>
                    <CardTitle className="text-xl font-heading">Kraken Exchange</CardTitle>
                    <CardDescription>
                      Primary trading exchange
                      {hasCredentials && (
                        <span className="text-[#00FF94] ml-2">✓ Connected</span>
                      )}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-[#5741D9]/10 border border-[#5741D9]/30 rounded-lg p-4">
                  <p className="text-sm text-[#A1A1AA]">
                    <strong className="text-[#5741D9]">How to get your API keys:</strong><br />
                    1. Log into your Kraken account<br />
                    2. Go to Settings → API<br />
                    3. Click Generate New Key<br />
                    4. Enable: Query Funds, Create/Modify Orders, Cancel/Close Orders<br />
                    5. <span className="text-[#FF0055]">Never enable Withdraw permission</span>
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-[#A1A1AA]">API Key</Label>
                    <Input
                      type="text"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your Kraken API key"
                      className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                      data-testid="kraken-api-key-input"
                    />
                  </div>
                  <div>
                    <Label className="text-[#A1A1AA]">API Secret</Label>
                    <Input
                      type="password"
                      value={apiSecret}
                      onChange={(e) => setApiSecret(e.target.value)}
                      placeholder="Enter your Kraken API secret"
                      className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                      data-testid="kraken-api-secret-input"
                    />
                  </div>
                </div>

                <Button
                  onClick={saveCredentials}
                  className="w-full bg-[#5741D9] hover:bg-[#5741D9]/80 text-white font-bold rounded-full"
                  disabled={loading}
                  data-testid="save-kraken-credentials-btn"
                >
                  {loading ? 'Saving...' : hasCredentials ? 'Update Kraken Credentials' : 'Save Kraken Credentials'}
                </Button>
              </CardContent>
            </Card>

            {/* Binance */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="binance-credentials-card">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#F0B90B]/20 flex items-center justify-center">
                    <span className="text-lg font-bold text-[#F0B90B]">B</span>
                  </div>
                  <div>
                    <CardTitle className="text-xl font-heading">Binance Exchange</CardTitle>
                    <CardDescription>
                      World's largest crypto exchange by volume
                      {hasBinanceCredentials && (
                        <span className="text-[#00FF94] ml-2">✓ Connected</span>
                      )}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-[#F0B90B]/10 border border-[#F0B90B]/30 rounded-lg p-4">
                  <p className="text-sm text-[#A1A1AA]">
                    <strong className="text-[#F0B90B]">How to get your API keys:</strong><br />
                    1. Log into your Binance account<br />
                    2. Go to Account → API Management<br />
                    3. Create a new API key<br />
                    4. Enable: Spot Trading, Read Info<br />
                    5. <span className="text-[#FF0055]">Never enable Withdrawals</span>
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-[#A1A1AA]">API Key</Label>
                    <Input
                      type="text"
                      value={binanceApiKey}
                      onChange={(e) => setBinanceApiKey(e.target.value)}
                      placeholder="Enter your Binance API key"
                      className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                      data-testid="binance-api-key-input"
                    />
                  </div>
                  <div>
                    <Label className="text-[#A1A1AA]">API Secret</Label>
                    <Input
                      type="password"
                      value={binanceApiSecret}
                      onChange={(e) => setBinanceApiSecret(e.target.value)}
                      placeholder="Enter your Binance API secret"
                      className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                      data-testid="binance-api-secret-input"
                    />
                  </div>
                </div>

                <Button
                  onClick={saveBinanceCredentials}
                  className="w-full bg-[#F0B90B] hover:bg-[#F0B90B]/80 text-black font-bold rounded-full"
                  disabled={loading}
                  data-testid="save-binance-credentials-btn"
                >
                  {loading ? 'Saving...' : hasBinanceCredentials ? 'Update Binance Credentials' : 'Save Binance Credentials'}
                </Button>
              </CardContent>
            </Card>

            {/* Crypto.com - Best for Arbitrage (US Friendly) */}
            <Card className="bg-[#0A0A0A] border-[#00FF94]/30" data-testid="crypto-com-credentials-card">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#00FF94]/20 flex items-center justify-center">
                    <span className="text-lg font-bold text-[#00FF94]">C</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl font-heading">Crypto.com Exchange</CardTitle>
                      <span className="px-2 py-0.5 text-xs font-bold bg-[#00FF94]/20 text-[#00FF94] rounded-full border border-[#00FF94]/30">
                        Best for Arbitrage
                      </span>
                    </div>
                    <CardDescription>
                      US-friendly exchange with excellent liquidity for cross-exchange arbitrage
                      {hasCryptoComCredentials && (
                        <span className="text-[#00FF94] ml-2">✓ Connected</span>
                      )}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg p-4">
                  <p className="text-sm text-[#A1A1AA]">
                    <strong className="text-[#00FF94]">How to get your API keys:</strong><br />
                    1. Log into your Crypto.com Exchange account<br />
                    2. Go to Settings → API Keys<br />
                    3. Create a new API key<br />
                    4. Enable: Spot Trading, Read permissions<br />
                    5. <span className="text-[#FF0055]">Never enable Withdrawals</span>
                  </p>
                  <div className="mt-3 p-2 bg-[#9D00FF]/10 border border-[#9D00FF]/30 rounded">
                    <p className="text-xs text-[#9D00FF]">
                      💡 <strong>Why Crypto.com for Arbitrage?</strong> US-compliant, competitive fees (0.075%), 
                      250+ trading pairs, and frequent price discrepancies vs Kraken/Binance.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-[#A1A1AA]">API Key</Label>
                    <Input
                      type="text"
                      value={cryptoComApiKey}
                      onChange={(e) => setCryptoComApiKey(e.target.value)}
                      placeholder="Enter your Crypto.com API key"
                      className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                      data-testid="crypto-com-api-key-input"
                    />
                  </div>
                  <div>
                    <Label className="text-[#A1A1AA]">API Secret</Label>
                    <Input
                      type="password"
                      value={cryptoComApiSecret}
                      onChange={(e) => setCryptoComApiSecret(e.target.value)}
                      placeholder="Enter your Crypto.com API secret"
                      className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                      data-testid="crypto-com-api-secret-input"
                    />
                  </div>
                </div>

                <Button
                  onClick={saveCryptoComCredentials}
                  className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                  disabled={loading}
                  data-testid="save-crypto-com-credentials-btn"
                >
                  {loading ? 'Saving...' : hasCryptoComCredentials ? 'Update Crypto.com Credentials' : 'Save Crypto.com Credentials'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Risk Management Tab */}
        <TabsContent value="risk">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="risk-settings-card">
            <CardHeader>
              <CardTitle className="text-2xl font-heading">Risk Management Settings</CardTitle>
              <CardDescription>
                Configure your trading risk parameters to protect your capital
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-[#A1A1AA]">Max Investment Per Trade (USD)</Label>
                  <Input
                    type="number"
                    value={riskSettings.max_investment_per_trade}
                    onChange={(e) => setRiskSettings({
                      ...riskSettings,
                      max_investment_per_trade: parseFloat(e.target.value)
                    })}
                    className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                    data-testid="max-investment-input"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Stop Loss (%)</Label>
                  <Input
                    type="number"
                    value={riskSettings.stop_loss_percentage}
                    onChange={(e) => setRiskSettings({
                      ...riskSettings,
                      stop_loss_percentage: parseFloat(e.target.value)
                    })}
                    className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                    data-testid="stop-loss-input"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Take Profit (%)</Label>
                  <Input
                    type="number"
                    value={riskSettings.take_profit_percentage}
                    onChange={(e) => setRiskSettings({
                      ...riskSettings,
                      take_profit_percentage: parseFloat(e.target.value)
                    })}
                    className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                    data-testid="take-profit-input"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Max Daily Trades</Label>
                  <Input
                    type="number"
                    value={riskSettings.max_daily_trades}
                    onChange={(e) => setRiskSettings({
                      ...riskSettings,
                      max_daily_trades: parseInt(e.target.value)
                    })}
                    className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                    data-testid="max-daily-trades-input"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Max Portfolio Allocation per Coin (%)</Label>
                  <Input
                    type="number"
                    value={riskSettings.max_portfolio_allocation}
                    onChange={(e) => setRiskSettings({
                      ...riskSettings,
                      max_portfolio_allocation: parseFloat(e.target.value)
                    })}
                    className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                    data-testid="max-allocation-input"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Risk Level</Label>
                  <Select 
                    value={riskSettings.risk_level} 
                    onValueChange={(value) => setRiskSettings({
                      ...riskSettings,
                      risk_level: value
                    })}
                  >
                    <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1" data-testid="risk-level-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#0A0A0A] border-[#1F1F1F]">
                      <SelectItem value="low">Low - Conservative</SelectItem>
                      <SelectItem value="medium">Medium - Balanced</SelectItem>
                      <SelectItem value="high">High - Aggressive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="bg-[#9D00FF]/10 border border-[#9D00FF]/30 rounded-lg p-4">
                <h4 className="font-bold text-[#9D00FF] mb-2">Risk Level Guidelines</h4>
                <ul className="text-sm text-[#A1A1AA] space-y-1">
                  <li>• Low: Smaller position sizes, tighter stop losses</li>
                  <li>• Medium: Balanced approach with moderate risk</li>
                  <li>• High: Larger positions, wider stop losses</li>
                </ul>
              </div>

              <Button
                onClick={saveRiskSettings}
                className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                disabled={loading}
                data-testid="save-risk-settings-btn"
              >
                {loading ? 'Saving...' : 'Save Risk Settings'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="notification-settings-card">
            <CardHeader>
              <CardTitle className="text-2xl font-heading">Notification Settings</CardTitle>
              <CardDescription>
                Configure push notifications with vibration for trades and alerts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Push Notifications Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Bell size={20} className="text-[#00FF94]" />
                  Push Notifications
                </h3>
                
                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>Enable Push Notifications</Label>
                    <p className="text-xs text-[#A1A1AA]">Receive in-app notifications</p>
                  </div>
                  <Switch
                    checked={notificationSettings.push_enabled}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      push_enabled: checked
                    })}
                    data-testid="push-enabled-switch"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>Enable Vibration</Label>
                    <p className="text-xs text-[#A1A1AA]">Vibrate phone for important alerts</p>
                  </div>
                  <Switch
                    checked={notificationSettings.vibration_enabled}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      vibration_enabled: checked
                    })}
                    data-testid="vibration-enabled-switch"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>Trade Open Notifications</Label>
                    <p className="text-xs text-[#A1A1AA]">Notify when trades are opened</p>
                  </div>
                  <Switch
                    checked={notificationSettings.notify_trade_open}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      notify_trade_open: checked
                    })}
                    data-testid="trade-open-switch"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>Trade Close Notifications</Label>
                    <p className="text-xs text-[#A1A1AA]">Notify when trades are closed</p>
                  </div>
                  <Switch
                    checked={notificationSettings.notify_trade_close}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      notify_trade_close: checked
                    })}
                    data-testid="trade-close-switch"
                  />
                </div>
              </div>

              {/* Alert Priority Section */}
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Smartphone size={20} className="text-[#9D00FF]" />
                  Alert Priorities
                </h3>

                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>HIGH Priority Alerts</Label>
                    <p className="text-xs text-[#A1A1AA]">Urgent vibration for high priority gems</p>
                  </div>
                  <Switch
                    checked={notificationSettings.notify_high_alerts}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      notify_high_alerts: checked
                    })}
                    data-testid="high-alerts-switch"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>MEDIUM Priority Alerts</Label>
                    <p className="text-xs text-[#A1A1AA]">Normal vibration for medium alerts</p>
                  </div>
                  <Switch
                    checked={notificationSettings.notify_medium_alerts}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      notify_medium_alerts: checked
                    })}
                    data-testid="medium-alerts-switch"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                  <div>
                    <Label>AI Discovery Alerts</Label>
                    <p className="text-xs text-[#A1A1AA]">Notify when AI discovers new coins</p>
                  </div>
                  <Switch
                    checked={notificationSettings.notify_ai_discoveries}
                    onCheckedChange={(checked) => setNotificationSettings({
                      ...notificationSettings,
                      notify_ai_discoveries: checked
                    })}
                    data-testid="ai-discoveries-switch"
                  />
                </div>
              </div>

              {/* Info Box */}
              <div className="bg-[#00FF94]/10 border border-[#00FF94]/30 rounded-lg p-4">
                <h4 className="font-bold text-[#00FF94] mb-2">Vibration Patterns</h4>
                <ul className="text-sm text-[#A1A1AA] space-y-1">
                  <li>• <span className="text-red-400">Critical:</span> Long urgent pattern (moonshots, 100%+ gains)</li>
                  <li>• <span className="text-[#FFB800]">High:</span> Medium urgent pattern (gem alerts, major trades)</li>
                  <li>• <span className="text-[#00FF94]">Normal:</span> Standard pattern (trade updates)</li>
                  <li>• <span className="text-[#A1A1AA]">Low:</span> Subtle single vibration</li>
                </ul>
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={saveNotificationSettings}
                  className="flex-1 bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full"
                  disabled={loading}
                  data-testid="save-notification-settings-btn"
                >
                  {loading ? 'Saving...' : 'Save Settings'}
                </Button>
                <Button
                  onClick={testPushNotification}
                  variant="outline"
                  className="border-[#00FF94] text-[#00FF94] hover:bg-[#00FF94]/10"
                  disabled={loading}
                  data-testid="test-push-btn"
                >
                  <Bell size={16} className="mr-2" />
                  Test Push
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;
