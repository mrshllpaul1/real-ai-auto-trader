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
import { toast } from 'sonner';
import { Shield, Key, Settings as SettingsIcon, Bell, Phone, MessageSquare } from 'lucide-react';

const Settings = () => {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [hasCredentials, setHasCredentials] = useState(false);
  const [riskSettings, setRiskSettings] = useState({
    max_investment_per_trade: 1000,
    stop_loss_percentage: 5,
    take_profit_percentage: 15,
    max_daily_trades: 10,
    max_portfolio_allocation: 20,
    risk_level: 'medium'
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkCredentials();
    loadRiskSettings();
  }, []);

  const checkCredentials = async () => {
    try {
      const response = await authAPI.checkCredentials();
      setHasCredentials(response.data.has_credentials);
    } catch (error) {
      console.error('Error checking credentials:', error);
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

  const saveCredentials = async () => {
    if (!apiKey || !apiSecret) {
      toast.error('Please enter both API key and secret');
      return;
    }

    try {
      setLoading(true);
      await authAPI.storeCredentials(apiKey, apiSecret);
      toast.success('API credentials saved successfully!');
      setHasCredentials(true);
      setApiKey('');
      setApiSecret('');
    } catch (error) {
      toast.error('Failed to save credentials');
    } finally {
      setLoading(false);
    }
  };

  const saveRiskSettings = async () => {
    try {
      setLoading(true);
      await riskAPI.updateSettings(riskSettings);
      toast.success('Risk settings updated successfully!');
    } catch (error) {
      toast.error('Failed to update risk settings');
    } finally {
      setLoading(false);
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
        </TabsList>

        {/* API Credentials Tab */}
        <TabsContent value="api">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="api-credentials-card">
            <CardHeader>
              <CardTitle className="text-2xl font-heading">Kraken API Credentials</CardTitle>
              <CardDescription>
                Enter your Kraken API credentials to enable real trading. 
                {hasCredentials && (
                  <span className="text-[#00FF94] block mt-2">
                    ✓ API credentials are configured
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-[#007AFF]/10 border border-[#007AFF]/30 rounded-lg p-4">
                <p className="text-sm text-[#007AFF]">
                  <strong>How to get your API keys:</strong><br />
                  1. Log into your Kraken account<br />
                  2. Go to Settings → API<br />
                  3. Click "Generate New Key"<br />
                  4. Enable: Query Funds, Create & Modify Orders, Cancel/Close Orders<br />
                  5. Never enable "Withdraw" permission
                </p>
              </div>

              <div>
                <Label className="text-[#A1A1AA]">API Key</Label>
                <Input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your Kraken API key"
                  className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                  data-testid="api-key-input"
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
                  data-testid="api-secret-input"
                />
              </div>

              <Button
                onClick={saveCredentials}
                className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                disabled={loading}
                data-testid="save-credentials-btn"
              >
                {loading ? 'Saving...' : 'Save Credentials'}
              </Button>
            </CardContent>
          </Card>
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
      </Tabs>
    </div>
  );
};

export default Settings;
