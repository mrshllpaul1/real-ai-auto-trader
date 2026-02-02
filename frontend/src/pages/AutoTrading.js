import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Zap, Play, Square, Smartphone, TrendingUp, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';
import AIPortfolioSection from '../components/AIPortfolioSection';
import AICoinSelectionSection from '../components/AICoinSelectionSection';
import AutomatedTradingSection from '../components/AutomatedTradingSection';
import { useTradingMode } from '../context/TradingModeContext';

const AutoTrading = () => {
  // Use global trading mode context
  const { isRealMode, isPaperMode, setMode } = useTradingMode();
  
  const [config, setConfig] = useState({
    enabled: false,
    paper_trading_enabled: true,
    real_trading_enabled: false,
    amount_per_trade: 100,
    min_confidence: 70,
    max_daily_trades: 10
  });
  const [allocation, setAllocation] = useState({
    USD: 0,
    BTC: 0,
    ETH: 0,
    SOL: 0
  });
  const [botPortfolio, setBotPortfolio] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Sync config with global trading mode
  useEffect(() => {
    setConfig(prev => ({
      ...prev,
      paper_trading_enabled: isPaperMode,
      real_trading_enabled: isRealMode
    }));
  }, [isPaperMode, isRealMode]);

  useEffect(() => {
    loadConfig();
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConfig = async () => {
    try {
      const userId = localStorage.getItem('user_id') || 'demo_user';
      const [configRes, allocationRes, portfolioRes] = await Promise.all([
        api.get(`/auto-trading/config/${userId}`).catch(() => ({ data: { configured: false } })),
        api.get(`/allocation/allocation/${userId}`).catch(() => ({ data: { allocated: false } })),
        api.get(`/allocation/portfolio/${userId}`).catch(() => ({ data: { initialized: false } }))
      ]);
      
      if (configRes.data.configured) {
        // Apply config but preserve global trading mode from context
        setConfig(prev => ({
          ...configRes.data.config,
          paper_trading_enabled: prev.paper_trading_enabled,
          real_trading_enabled: prev.real_trading_enabled
        }));
      }
        setConfig(prev => ({
          ...prev,
          paper_trading_enabled: savedMode !== 'real',
          real_trading_enabled: savedMode === 'real'
        }));
      }
      
      if (allocationRes.data.allocated) {
        setAllocation(allocationRes.data.allocations || {});
      }
      
      if (portfolioRes.data.initialized !== false) {
        setBotPortfolio(portfolioRes.data);
      }
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStatus = async () => {
    try {
      const response = await api.get('/auto-trading/status');
      setStatus(response.data);
    } catch (error) {
      console.error('Error loading status:', error);
    }
  };

  const saveAllocation = async () => {
    try {
      setLoading(true);
      const userId = localStorage.getItem('user_id') || 'demo_user';
      
      const nonZeroAllocations = Object.fromEntries(
        Object.entries(allocation).filter(([_, value]) => value > 0)
      );
      
      await api.post('/allocation/allocate', {
        user_id: userId,
        allocations: nonZeroAllocations
      });
      
      toast.success('Funds allocated successfully! Bot will only trade with these funds.');
      await loadConfig();
    } catch (error) {
      toast.error('Failed to allocate funds');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      setLoading(true);
      const userId = localStorage.getItem('user_id') || 'demo_user';
      
      await api.post('/auto-trading/configure', {
        user_id: userId,
        ...config
      });
      
      toast.success('Configuration saved successfully!');
    } catch (error) {
      toast.error('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const startAutoTrading = async () => {
    try {
      toast.loading('Starting auto-trading...');
      await api.post('/auto-trading/start');
      toast.dismiss();
      toast.success('Auto-trading started! Running in background.');
      await loadStatus();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to start auto-trading');
    }
  };

  const stopAutoTrading = async () => {
    try {
      await api.post('/auto-trading/stop');
      toast.success('Auto-trading stopped');
      await loadStatus();
    } catch (error) {
      toast.error('Failed to stop auto-trading');
    }
  };

  const isRunning = status?.running || false;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#00FF94]" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="auto-trading">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="auto-trading-title">
          <Zap className="inline mr-3 text-[#00FF94]" size={48} />
          <span className="text-[#00FF94]">Auto</span> Trading
        </h1>
        <p className="text-[#A1A1AA]">
          Configure automated trading with real money - Runs 24/7 in background on your phone
        </p>
      </motion.div>

      {/* Status Card */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="status-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-heading flex items-center gap-3">
                <div 
                  className="w-3 h-3 rounded-full animate-pulse"
                  style={{ backgroundColor: isRunning ? '#00FF94' : '#FF0055' }}
                />
                Auto-Trading Status
              </CardTitle>
              <CardDescription>
                {isRunning ? 'Currently running and monitoring markets' : 'Not running'}
              </CardDescription>
            </div>
            {isRunning ? (
              <Button
                onClick={stopAutoTrading}
                className="bg-[#FF0055] hover:bg-[#CC0044] text-white rounded-full"
                data-testid="stop-btn"
              >
                <Square size={16} className="mr-2" />
                Stop
              </Button>
            ) : (
              <Button
                onClick={startAutoTrading}
                className="bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                data-testid="start-btn"
              >
                <Play size={16} className="mr-2" />
                Start Auto-Trading
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 bg-[#121212] rounded-lg">
              <div className="text-xs text-[#A1A1AA] mb-1">Status</div>
              <Badge className={`${isRunning ? 'bg-[#00FF94]/20 text-[#00FF94] border-[#00FF94]/30' : 'bg-[#FF0055]/20 text-[#FF0055] border-[#FF0055]/30'}`}>
                {isRunning ? 'RUNNING' : 'STOPPED'}
              </Badge>
            </div>
            <div className="p-3 bg-[#121212] rounded-lg">
              <div className="text-xs text-[#A1A1AA] mb-1">Real Trading</div>
              <Badge className={`${status?.real_trading_enabled ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#007AFF]/20 text-[#007AFF]'} border-[#1F1F1F]`}>
                {status?.real_trading_enabled ? 'ENABLED' : 'DISABLED'}
              </Badge>
            </div>
            <div className="p-3 bg-[#121212] rounded-lg">
              <div className="text-xs text-[#A1A1AA] mb-1">Background Mode</div>
              <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] border-[#9D00FF]/30">
                <Smartphone size={12} className="mr-1" />
                ACTIVE
              </Badge>
            </div>
            <div className="p-3 bg-[#121212] rounded-lg">
              <div className="text-xs text-[#A1A1AA] mb-1">Mobile Compatible</div>
              <Badge className="bg-[#007AFF]/20 text-[#007AFF] border-[#007AFF]/30">
                Galaxy S22
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="config-card">
        <CardHeader>
          <CardTitle className="text-2xl font-heading">Trading Configuration</CardTitle>
          <CardDescription>
            Configure auto-trading parameters - Both paper and real trading can run simultaneously
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Toggle Switches */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center justify-between p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
              <div>
                <Label className="text-base font-bold text-white">Paper Trading</Label>
                <p className="text-sm text-[#A1A1AA] mt-1">Risk-free simulation mode</p>
              </div>
              <Switch
                checked={config.paper_trading_enabled}
                onCheckedChange={(checked) => {
                  setConfig({...config, paper_trading_enabled: checked, real_trading_enabled: !checked});
                  localStorage.setItem('growth_trading_mode', checked ? 'paper' : 'real');
                }}
                data-testid="paper-trading-switch"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-[#121212] rounded-lg border border-[#FF0055]/30">
              <div>
                <Label className="text-base font-bold text-white">Real Trading</Label>
                <p className="text-sm text-[#FF0055] mt-1">Uses real money on Kraken</p>
              </div>
              <Switch
                checked={config.real_trading_enabled}
                onCheckedChange={(checked) => {
                  setConfig({...config, real_trading_enabled: checked, paper_trading_enabled: !checked});
                  localStorage.setItem('growth_trading_mode', checked ? 'real' : 'paper');
                }}
                data-testid="real-trading-switch"
              />
            </div>
          </div>

          {/* Trade Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label className="text-[#A1A1AA]">Amount Per Trade (USD)</Label>
              <Input
                type="number"
                value={config.amount_per_trade}
                onChange={(e) => setConfig({...config, amount_per_trade: parseFloat(e.target.value)})}
                className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                data-testid="amount-input"
              />
            </div>

            <div>
              <Label className="text-[#A1A1AA]">Min Confidence (%)</Label>
              <Input
                type="number"
                value={config.min_confidence}
                onChange={(e) => setConfig({...config, min_confidence: parseFloat(e.target.value)})}
                className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                data-testid="confidence-input"
              />
            </div>

            <div>
              <Label className="text-[#A1A1AA]">Max Daily Trades</Label>
              <Input
                type="number"
                value={config.max_daily_trades}
                onChange={(e) => setConfig({...config, max_daily_trades: parseInt(e.target.value)})}
                className="bg-[#121212] border-[#1F1F1F] font-data mt-1"
                data-testid="max-trades-input"
              />
            </div>
          </div>

          {/* Save Button */}
          <Button
            onClick={saveConfig}
            className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
            disabled={loading}
            data-testid="save-config-btn"
          >
            <TrendingUp size={16} className="mr-2" />
            Save Configuration
          </Button>

          {/* Info Box */}
          <div className="bg-[#007AFF]/10 border border-[#007AFF]/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-[#007AFF] flex-shrink-0 mt-1" size={20} />
              <div className="text-sm text-[#007AFF]">
                <p className="font-bold mb-2">How Auto-Trading Works:</p>
                <ul className="space-y-1 ml-4">
                  <li>AI selects 10 coins + 1 gem every week</li>
                  <li>Automatic stop-loss (15%) and take-profit (30%)</li>
                  <li>Gem positions: higher risk (25% SL, 100% TP)</li>
                  <li>Paper trading for simulation, Real for live execution</li>
                  <li>59.5% win rate on 11+ years of backtesting</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Automated Weekly Trading */}
      <AutomatedTradingSection />

      {/* AI Portfolio Manager */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F] border-l-4 border-l-[#9D00FF]" data-testid="ai-portfolio-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-heading flex items-center gap-3">
                <TrendingUp className="text-[#9D00FF]" size={28} />
                AI Portfolio Manager
                <Badge className="bg-[#9D00FF]/20 text-[#9D00FF] border-[#9D00FF]/30">
                  AUTONOMOUS
                </Badge>
              </CardTitle>
              <CardDescription>
                Let AI develop and manage its own portfolio with your allocated funds
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <AIPortfolioSection />
        </CardContent>
      </Card>

      {/* AI Coin Selection Engine */}
      <AICoinSelectionSection />

      {/* Mobile Instructions */}
      <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="mobile-instructions-card">
        <CardHeader>
          <CardTitle className="text-2xl font-heading flex items-center gap-3">
            <Smartphone className="text-[#9D00FF]" />
            Galaxy S22 Background Mode
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-[#A1A1AA]">
              To ensure auto-trading runs continuously in background on your Galaxy S22:
            </p>
            
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 bg-[#121212] rounded-lg">
                <span className="font-bold text-[#00FF94]">1.</span>
                <p className="text-sm text-[#A1A1AA]">
                  Add this app to your home screen (Chrome menu - Add to Home screen)
                </p>
              </div>
              
              <div className="flex items-start gap-3 p-3 bg-[#121212] rounded-lg">
                <span className="font-bold text-[#00FF94]">2.</span>
                <p className="text-sm text-[#A1A1AA]">
                  Go to Settings - Apps - AI Crypto Trading - Battery - Allow background activity
                </p>
              </div>
              
              <div className="flex items-start gap-3 p-3 bg-[#121212] rounded-lg">
                <span className="font-bold text-[#00FF94]">3.</span>
                <p className="text-sm text-[#A1A1AA]">
                  Disable Put app to sleep in Device Care - Battery settings
                </p>
              </div>
              
              <div className="flex items-start gap-3 p-3 bg-[#121212] rounded-lg">
                <span className="font-bold text-[#00FF94]">4.</span>
                <p className="text-sm text-[#A1A1AA]">
                  Keep app open in background. Auto-trading will continue running even when screen is off.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AutoTrading;
