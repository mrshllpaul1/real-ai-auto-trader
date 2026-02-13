import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { motion } from 'framer-motion';
import {
  Activity, Play, Pause, Settings2, TrendingUp, TrendingDown,
  DollarSign, BarChart3, RefreshCw, AlertTriangle, Layers,
  ArrowUpDown, Percent, Target, Clock, Zap, Brain
} from 'lucide-react';
import api from '../services/api';
import toast from '../utils/toast';
import TradingPairSelector from '../components/TradingPairSelector';
import { PageLoadingSkeleton } from '../components/LoadingSkeleton';
import { AIPredictionCard, useAIPrediction } from '../components/AIPrediction';

const MarketMaker = ({ embedded = false }) => {
  const [status, setStatus] = useState(null);
  const [orders, setOrders] = useState({ bids: [], asks: [] });
  const [history, setHistory] = useState([]);
  const [pnl, setPnl] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [presets, setPresets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('control');
  
  // Configuration state
  const [config, setConfig] = useState({
    symbol: 'BTC/USD',
    spread_percentage: 0.5,
    order_size_usd: 100,
    num_levels: 3,
    level_spacing_pct: 0.2,
    max_position_usd: 1000,
    rebalance_threshold: 0.3,
    min_profit_pct: 0.1,
    enabled: true
  });

  // AI Prediction for selected symbol
  const symbolClean = config.symbol.replace('/USD', '').replace('USD', '');
  const { prediction: aiPrediction, loading: aiLoading, refetch: refetchAi } = useAIPrediction(symbolClean);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusRes, ordersRes, pnlRes, presetsRes] = await Promise.all([
        api.get('/market-maker/status').catch(() => ({ data: {} })),
        api.get('/market-maker/orders').catch(() => ({ data: { orders: { bids: [], asks: [] } } })),
        api.get('/market-maker/pnl').catch(() => ({ data: {} })),
        api.get('/market-maker/presets').catch(() => ({ data: { presets: [] } }))
      ]);

      setStatus(statusRes.data);
      setOrders(ordersRes.data.orders || { bids: [], asks: [] });
      setPnl(pnlRes.data);
      setPresets(presetsRes.data.presets || []);
      
      if (statusRes.data.config) {
        setConfig(statusRes.data.config);
      }
    } catch (error) {
      console.error('Error loading market maker data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [loadData]);

  const handleStart = async () => {
    const loadingToast = toast.loading('Starting Market Maker...');
    try {
      await api.post('/market-maker/start', config);
      toast.dismiss(loadingToast);
      toast.success('Market Maker started!', {
        description: `Trading ${config.symbol} with ${config.spread_percentage}% spread`
      });
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to start Market Maker', {
        description: error.response?.data?.detail || 'Please try again'
      });
    }
  };

  const handleStop = async () => {
    const loadingToast = toast.loading('Stopping Market Maker...');
    try {
      await api.post('/market-maker/stop');
      toast.dismiss(loadingToast);
      toast.success('Market Maker stopped');
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to stop Market Maker');
    }
  };

  const handleUpdateConfig = async () => {
    const loadingToast = toast.loading('Updating configuration...');
    try {
      await api.put('/market-maker/config', config);
      toast.dismiss(loadingToast);
      toast.success('Configuration updated');
      loadData();
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to update configuration');
    }
  };

  const handleApplyPreset = (preset) => {
    setConfig({ ...config, ...preset.config, symbol: config.symbol });
    toast.info(`Applied "${preset.name}" preset`);
  };

  const handleRefreshOrders = async () => {
    try {
      // Simulate mid price update
      const midPrice = 45000 + Math.random() * 1000;
      await api.post(`/market-maker/update-orders?mid_price=${midPrice}`);
      toast.success('Orders refreshed');
      loadData();
    } catch (error) {
      toast.error('Failed to refresh orders');
    }
  };

  if (loading) {
    return <PageLoadingSkeleton />;
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="market-maker-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <Activity size={40} className="text-[#00B8FF]" />
            <span className="text-[#00B8FF]">Market</span> Maker
          </h1>
          <p className="text-[#A1A1AA]">
            Provide liquidity and earn from bid-ask spread
          </p>
        </div>
        <div className="flex gap-2">
          {status?.is_running ? (
            <Button onClick={handleStop} variant="destructive" className="bg-[#FF0055]" data-testid="stop-btn">
              <Pause size={16} className="mr-2" />
              Stop
            </Button>
          ) : (
            <Button onClick={handleStart} className="bg-[#00FF94] text-black" data-testid="start-btn">
              <Play size={16} className="mr-2" />
              Start
            </Button>
          )}
          <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
            <RefreshCw size={16} />
          </Button>
        </div>
      </motion.div>

      {/* Status Banner */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card className={`border-2 ${status?.is_running ? 'border-[#00FF94]/50 bg-[#00FF94]/5' : 'border-[#1F1F1F] bg-[#0A0A0A]'}`}>
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`w-4 h-4 rounded-full ${status?.is_running ? 'bg-[#00FF94] animate-pulse' : 'bg-[#666]'}`} />
                <div>
                  <span className="font-bold text-white text-lg">
                    {status?.is_running ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                  {status?.symbol && <span className="text-[#A1A1AA] ml-3">{status.symbol}</span>}
                </div>
              </div>
              {status?.is_running && (
                <div className="flex flex-wrap gap-6 text-sm">
                  <div>
                    <span className="text-[#A1A1AA]">Position:</span>
                    <span className={`ml-2 font-data ${status.position >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                      {(status?.position ?? 0).toFixed(6)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#A1A1AA]">Trades:</span>
                    <span className="ml-2 font-data text-white">{status.trades_executed || 0}</span>
                  </div>
                  <div>
                    <span className="text-[#A1A1AA]">Mid Price:</span>
                    <span className="ml-2 font-data text-white">${(status?.last_mid_price ?? 0).toLocaleString() || 'N/A'}</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* AI Prediction Card */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.15 }}
      >
        <AIPredictionCard 
          symbol={symbolClean}
          prediction={aiPrediction}
          loading={aiLoading}
          onRefresh={refetchAi}
        />
      </motion.div>

      {/* P&L Cards */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign size={20} className="text-[#00FF94]" />
              <span className="text-sm text-[#A1A1AA]">Realized P&L</span>
            </div>
            <div className={`text-2xl font-data font-bold ${(pnl?.realized_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              ${(pnl?.realized_pnl ?? 0).toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp size={20} className="text-[#007AFF]" />
              <span className="text-sm text-[#A1A1AA]">Unrealized P&L</span>
            </div>
            <div className={`text-2xl font-data font-bold ${(pnl?.unrealized_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              ${(pnl?.unrealized_pnl ?? 0).toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <Layers size={20} className="text-[#9D00FF]" />
              <span className="text-sm text-[#A1A1AA]">Position Value</span>
            </div>
            <div className="text-2xl font-data font-bold text-white">
              ${(pnl?.position_value_usd ?? 0).toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-2">
              <BarChart3 size={20} className="text-[#FFB800]" />
              <span className="text-sm text-[#A1A1AA]">Total P&L</span>
            </div>
            <div className={`text-2xl font-data font-bold ${(pnl?.total_pnl || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
              ${(pnl?.total_pnl ?? 0).toFixed(2) || '0.00'}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="control" className="data-[state=active]:bg-[#00B8FF] data-[state=active]:text-black">
            <Settings2 size={16} className="mr-2" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="orders" className="data-[state=active]:bg-[#00B8FF] data-[state=active]:text-black">
            <ArrowUpDown size={16} className="mr-2" />
            Order Book
          </TabsTrigger>
          <TabsTrigger value="presets" className="data-[state=active]:bg-[#00B8FF] data-[state=active]:text-black">
            <Zap size={16} className="mr-2" />
            Presets
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="control" className="space-y-4">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Market Maker Configuration</CardTitle>
              <CardDescription>Configure your market making parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <Label className="text-[#A1A1AA]">Trading Pair</Label>
                  <TradingPairSelector 
                    value={config.symbol} 
                    onValueChange={(v) => setConfig({ ...config, symbol: v })}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Spread: {config.spread_percentage}%</Label>
                  <Slider
                    value={[config.spread_percentage]}
                    onValueChange={([v]) => setConfig({ ...config, spread_percentage: v })}
                    min={0.1}
                    max={2}
                    step={0.1}
                    className="mt-3"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Order Size (USD)</Label>
                  <Input
                    type="number"
                    value={config.order_size_usd}
                    onChange={(e) => setConfig({ ...config, order_size_usd: parseFloat(e.target.value) || 0 })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Order Levels (per side)</Label>
                  <Input
                    type="number"
                    value={config.num_levels}
                    onChange={(e) => setConfig({ ...config, num_levels: parseInt(e.target.value) || 1 })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                    min={1}
                    max={10}
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Level Spacing: {config.level_spacing_pct}%</Label>
                  <Slider
                    value={[config.level_spacing_pct]}
                    onValueChange={([v]) => setConfig({ ...config, level_spacing_pct: v })}
                    min={0.05}
                    max={1}
                    step={0.05}
                    className="mt-3"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Max Position (USD)</Label>
                  <Input
                    type="number"
                    value={config.max_position_usd}
                    onChange={(e) => setConfig({ ...config, max_position_usd: parseFloat(e.target.value) || 0 })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>
              </div>

              <div className="flex gap-4">
                <Button onClick={handleUpdateConfig} className="bg-[#00B8FF] text-black" disabled={status?.is_running}>
                  Save Configuration
                </Button>
                {!status?.is_running && (
                  <Button onClick={handleStart} className="bg-[#00FF94] text-black">
                    <Play size={16} className="mr-2" />
                    Start with this Config
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Order Book Tab */}
        <TabsContent value="orders" className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-white">Active Orders</h3>
            <Button onClick={handleRefreshOrders} variant="outline" className="border-[#1F1F1F]" disabled={!status?.is_running}>
              <RefreshCw size={16} className="mr-2" />
              Refresh Orders
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Bids */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader className="pb-2">
                <CardTitle className="text-[#00FF94] flex items-center gap-2">
                  <TrendingUp size={20} />
                  Bids (Buy Orders)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {orders.bids?.length > 0 ? (
                  <div className="space-y-2">
                    {orders.bids.map((order, i) => (
                      <div key={i} className="flex justify-between p-2 bg-[#00FF94]/10 rounded border border-[#00FF94]/20">
                        <span className="text-[#00FF94] font-data">${(order?.price ?? 0).toLocaleString()}</span>
                        <span className="text-white font-data">${order.size_usd}</span>
                        <Badge variant="outline" className="border-[#00FF94] text-[#00FF94]">L{order.level}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[#A1A1AA] text-center py-4">No bid orders</p>
                )}
              </CardContent>
            </Card>

            {/* Asks */}
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader className="pb-2">
                <CardTitle className="text-[#FF0055] flex items-center gap-2">
                  <TrendingDown size={20} />
                  Asks (Sell Orders)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {orders.asks?.length > 0 ? (
                  <div className="space-y-2">
                    {orders.asks.map((order, i) => (
                      <div key={i} className="flex justify-between p-2 bg-[#FF0055]/10 rounded border border-[#FF0055]/20">
                        <span className="text-[#FF0055] font-data">${(order?.price ?? 0).toLocaleString()}</span>
                        <span className="text-white font-data">${order.size_usd}</span>
                        <Badge variant="outline" className="border-[#FF0055] text-[#FF0055]">L{order.level}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[#A1A1AA] text-center py-4">No ask orders</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Presets Tab */}
        <TabsContent value="presets" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {presets.map((preset, i) => (
              <motion.div
                key={preset.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <Card className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#00B8FF]/50 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-white text-lg">{preset.name}</h3>
                        <p className="text-sm text-[#A1A1AA]">{preset.description}</p>
                      </div>
                      <Button
                        onClick={() => handleApplyPreset(preset)}
                        variant="outline"
                        size="sm"
                        className="border-[#00B8FF] text-[#00B8FF]"
                      >
                        Apply
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-[#A1A1AA]">Spread:</span>
                        <span className="text-white">{preset.config.spread_percentage}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#A1A1AA]">Order Size:</span>
                        <span className="text-white">${preset.config.order_size_usd}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#A1A1AA]">Levels:</span>
                        <span className="text-white">{preset.config.num_levels}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#A1A1AA]">Max Position:</span>
                        <span className="text-white">${preset.config.max_position_usd}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Warning Card */}
      <Card className="bg-[#FFB800]/10 border-[#FFB800]/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="text-[#FFB800] flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-[#FFB800] mb-1">Market Making Risks</h4>
              <p className="text-sm text-[#A1A1AA]">
                Market making involves inventory risk. If the market moves sharply against your position, 
                you may incur losses. Start with small order sizes and monitor closely.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MarketMaker;
