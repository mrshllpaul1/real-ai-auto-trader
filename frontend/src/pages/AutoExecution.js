import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bot, Play, Square, Brain, TrendingUp, TrendingDown, 
  Zap, Target, AlertTriangle, RefreshCw, Settings2,
  DollarSign, Shield, Activity, Lightbulb
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';
import { toast } from 'sonner';

const AutoExecution = () => {
  const [status, setStatus] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);
  const [aiPerformance, setAiPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Get initial mode from localStorage - sync with GrowthDashboard
  const getInitialMode = () => {
    const saved = localStorage.getItem('growth_trading_mode');
    return saved === 'real' ? 'live' : 'paper';
  };
  
  const [riskProfile, setRiskProfile] = useState({
    enabled: false,
    mode: getInitialMode(),
    min_score: 60,
    max_position_size_usd: 100,
    max_daily_trades: 5,
    max_open_positions: 3,
    stop_loss_pct: 10,
    take_profit_pct: 50
  });

  // Sync mode with localStorage
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'growth_trading_mode') {
        const newMode = e.newValue === 'real' ? 'live' : 'paper';
        setRiskProfile(prev => ({ ...prev, mode: newMode }));
      }
    };
    window.addEventListener('storage', handleStorageChange);
    
    // Also check on mount
    const saved = localStorage.getItem('growth_trading_mode');
    if (saved) {
      const newMode = saved === 'real' ? 'live' : 'paper';
      setRiskProfile(prev => ({ ...prev, mode: newMode }));
    }
    
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // When mode changes, update localStorage
  const handleModeChange = (newMode) => {
    setRiskProfile(prev => ({ ...prev, mode: newMode }));
    localStorage.setItem('growth_trading_mode', newMode === 'live' ? 'real' : 'paper');
  };

  const loadData = useCallback(async () => {
    try {
      const [statusRes, aiRes, perfRes, profileRes] = await Promise.all([
        api.get('/auto-exec/status').catch(() => ({ data: {} })),
        api.get('/auto-exec/ai/status').catch(() => ({ data: {} })),
        api.get('/auto-exec/ai/performance').catch(() => ({ data: {} })),
        api.get('/auto-exec/risk-profile').catch(() => ({ data: {} }))
      ]);
      
      setStatus(statusRes.data);
      setAiStatus(aiRes.data);
      setAiPerformance(perfRes.data);
      if (profileRes.data) {
        setRiskProfile(prev => ({ ...prev, ...profileRes.data }));
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const toggleAutoExecution = async () => {
    try {
      if (riskProfile.enabled) {
        await api.post('/auto-exec/disable');
        toast.success('Auto-execution disabled');
      } else {
        await api.post('/auto-exec/enable', null, { 
          params: { mode: riskProfile.mode }
        });
        toast.success(`Auto-execution enabled in ${riskProfile.mode.toUpperCase()} mode`);
      }
      await loadData();
    } catch (error) {
      toast.error('Failed to toggle auto-execution');
    }
  };

  const startExecution = async () => {
    try {
      toast.loading('Starting auto-execution engine...');
      await api.post('/auto-exec/start');
      toast.dismiss();
      toast.success('Auto-execution engine started!');
      await loadData();
    } catch (error) {
      toast.dismiss();
      toast.error('Failed to start');
    }
  };

  const stopExecution = async () => {
    try {
      await api.post('/auto-exec/stop');
      toast.success('Auto-execution stopped');
      await loadData();
    } catch (error) {
      toast.error('Failed to stop');
    }
  };

  const executeNow = async () => {
    try {
      toast.loading('Scanning and executing...');
      const res = await api.post('/auto-exec/execute-now');
      toast.dismiss();
      
      if (res.data.executed > 0) {
        toast.success(`Executed ${res.data.executed} trade(s)!`);
      } else {
        toast.info('No trades executed - no matching HIGH priority gems');
      }
      await loadData();
    } catch (error) {
      toast.dismiss();
      toast.error('Execution failed');
    }
  };

  const saveRiskProfile = async () => {
    try {
      await api.post('/auto-exec/risk-profile', riskProfile);
      toast.success('Risk profile saved!');
    } catch (error) {
      toast.error('Failed to save risk profile');
    }
  };

  const startAILearning = async () => {
    try {
      await api.post('/auto-exec/ai/start-learning');
      toast.success('AI continuous learning started!');
      await loadData();
    } catch (error) {
      toast.error('Failed to start AI learning');
    }
  };

  const optimizeStrategy = async () => {
    try {
      toast.loading('AI optimizing strategy...');
      const res = await api.post('/auto-exec/ai/optimize');
      toast.dismiss();
      toast.success(`Made ${res.data.optimizations_made?.length || 0} optimizations`);
      await loadData();
    } catch (error) {
      toast.dismiss();
      toast.error('Optimization failed');
    }
  };

  const isRunning = status?.running || false;
  const openPositions = status?.open_positions_details || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-[#00FF94]" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-12 space-y-6" data-testid="auto-execution">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <h1 className="text-4xl lg:text-5xl font-heading font-black tracking-tight mb-2" data-testid="auto-exec-title">
          <Bot className="inline mr-3 text-[#9D00FF]" size={48} />
          <span className="text-[#9D00FF]">Auto</span> Execution
        </h1>
        <p className="text-[#A1A1AA]">
          AI-powered automatic trade execution with self-improving intelligence
        </p>
      </motion.div>

      <Tabs defaultValue="execution" className="space-y-6">
        <TabsList className="bg-[#0A0A0A] border border-[#1F1F1F]">
          <TabsTrigger value="execution" data-testid="tab-execution">
            <Zap size={16} className="mr-2" />
            Auto Execution
          </TabsTrigger>
          <TabsTrigger value="ai" data-testid="tab-ai">
            <Brain size={16} className="mr-2" />
            AI Learning
          </TabsTrigger>
          <TabsTrigger value="positions" data-testid="tab-positions">
            <Activity size={16} className="mr-2" />
            Positions
          </TabsTrigger>
          <TabsTrigger value="settings" data-testid="tab-settings">
            <Settings2 size={16} className="mr-2" />
            Risk Profile
          </TabsTrigger>
        </TabsList>

        {/* EXECUTION TAB */}
        <TabsContent value="execution" className="space-y-6">
          {/* Status Card */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]" data-testid="execution-status">
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <div 
                    className={`w-4 h-4 rounded-full ${isRunning ? 'bg-[#00FF94] animate-pulse' : 'bg-[#FF0055]'}`}
                  />
                  <div>
                    <CardTitle className="text-2xl font-heading">Execution Engine</CardTitle>
                    <CardDescription>
                      {isRunning ? 'Actively monitoring and executing trades' : 'Engine stopped'}
                    </CardDescription>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <Button
                    onClick={executeNow}
                    className="bg-[#007AFF] hover:bg-[#0066DD] text-white rounded-full"
                    data-testid="execute-now-btn"
                  >
                    <RefreshCw size={16} className="mr-2" />
                    Execute Now
                  </Button>
                  
                  {isRunning ? (
                    <Button
                      onClick={stopExecution}
                      className="bg-[#FF0055] hover:bg-[#CC0044] text-white rounded-full"
                      data-testid="stop-engine-btn"
                    >
                      <Square size={16} className="mr-2" />
                      Stop Engine
                    </Button>
                  ) : (
                    <Button
                      onClick={startExecution}
                      disabled={!riskProfile.enabled}
                      className="bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full glow-profit"
                      data-testid="start-engine-btn"
                    >
                      <Play size={16} className="mr-2" />
                      Start Engine
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Status</div>
                  <Badge className={isRunning ? 'bg-[#00FF94]/20 text-[#00FF94]' : 'bg-[#FF0055]/20 text-[#FF0055]'}>
                    {isRunning ? 'RUNNING' : 'STOPPED'}
                  </Badge>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Mode</div>
                  <Badge className={riskProfile.mode === 'live' ? 'bg-[#FF0055]/20 text-[#FF0055]' : 'bg-[#007AFF]/20 text-[#007AFF]'}>
                    {riskProfile.mode?.toUpperCase()}
                  </Badge>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Daily Trades</div>
                  <div className="text-2xl font-data font-bold text-white">
                    {status?.daily_trades_used || 0}/{status?.daily_trades_limit || 5}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Open Positions</div>
                  <div className="text-2xl font-data font-bold text-[#007AFF]">
                    {status?.open_positions || 0}
                  </div>
                </div>
                <div className="p-3 bg-[#121212] rounded-lg">
                  <div className="text-xs text-[#A1A1AA] mb-1">Total Profit</div>
                  <div className={`text-2xl font-data font-bold ${(status?.total_profit_pct || 0) >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                    {(status?.total_profit_pct || 0) >= 0 ? '+' : ''}{(status?.total_profit_pct || 0).toFixed(2)}%
                  </div>
                </div>
              </div>

              {/* Enable/Disable Toggle */}
              <div className="flex items-center justify-between mt-6 p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                <div>
                  <Label className="text-lg font-bold text-white">Auto-Execution</Label>
                  <p className="text-sm text-[#A1A1AA]">
                    {riskProfile.enabled ? 'Will execute trades on HIGH priority gems' : 'Disabled - no trades will be executed'}
                  </p>
                </div>
                <Switch
                  checked={riskProfile.enabled}
                  onCheckedChange={toggleAutoExecution}
                  data-testid="auto-exec-switch"
                />
              </div>
            </CardContent>
          </Card>

          {/* Recent Trades */}
          {status?.recent_trades?.length > 0 && (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardHeader>
                <CardTitle className="text-xl font-heading">Recent Trades</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {status.recent_trades.slice(0, 5).map((trade, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-[#121212] rounded-lg">
                      <div className="flex items-center gap-3">
                        {trade.status === 'OPEN' ? (
                          <Activity className="text-[#007AFF]" size={20} />
                        ) : trade.profit_pct > 0 ? (
                          <TrendingUp className="text-[#00FF94]" size={20} />
                        ) : (
                          <TrendingDown className="text-[#FF0055]" size={20} />
                        )}
                        <div>
                          <span className="font-bold text-white">{trade.symbol}</span>
                          <span className="text-xs text-[#A1A1AA] ml-2">
                            ${trade.entry_price?.toFixed(4)}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={
                          trade.status === 'OPEN' ? 'bg-[#007AFF]/20 text-[#007AFF]' :
                          trade.profit_pct > 0 ? 'bg-[#00FF94]/20 text-[#00FF94]' :
                          'bg-[#FF0055]/20 text-[#FF0055]'
                        }>
                          {trade.status === 'OPEN' ? 'OPEN' : `${trade.profit_pct > 0 ? '+' : ''}${trade.profit_pct?.toFixed(2)}%`}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* AI LEARNING TAB */}
        <TabsContent value="ai" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#9D00FF]/30" data-testid="ai-learning">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Brain className="text-[#9D00FF]" size={32} />
                  <div>
                    <CardTitle className="text-2xl font-heading">Self-Improving AI</CardTitle>
                    <CardDescription>
                      Continuously learns from trades to optimize performance
                    </CardDescription>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={optimizeStrategy}
                    className="bg-[#9D00FF] hover:bg-[#8B00E6] text-white rounded-full"
                  >
                    <Target size={16} className="mr-2" />
                    Optimize Now
                  </Button>
                  <Button
                    onClick={startAILearning}
                    disabled={aiStatus?.is_learning}
                    className="bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full"
                  >
                    <Brain size={16} className="mr-2" />
                    {aiStatus?.is_learning ? 'Learning...' : 'Start Learning'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Signal Weights */}
              <div>
                <h3 className="font-bold text-white mb-3">Learned Signal Weights</h3>
                <p className="text-xs text-[#A1A1AA] mb-3">
                  Weights greater than 1.0 mean the signal performs better than average
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(aiStatus?.signal_weights || {}).map(([signal, weight]) => (
                    <div key={signal} className="p-3 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA] mb-1">{signal.replace('_', ' ')}</div>
                      <div className={`text-xl font-data font-bold ${weight > 1 ? 'text-[#00FF94]' : weight < 1 ? 'text-[#FF0055]' : 'text-white'}`}>
                        {weight?.toFixed(2)}x
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Performance Stats */}
              {aiPerformance && aiPerformance.total_trades > 0 && (
                <div>
                  <h3 className="font-bold text-white mb-3">Performance Analytics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA] mb-1">Total Trades</div>
                      <div className="text-3xl font-data font-bold text-white">
                        {aiPerformance.total_trades}
                      </div>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA] mb-1">Win Rate</div>
                      <div className={`text-3xl font-data font-bold ${aiPerformance.win_rate > 50 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {aiPerformance.win_rate?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA] mb-1">Total Profit</div>
                      <div className={`text-3xl font-data font-bold ${aiPerformance.total_profit > 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {aiPerformance.total_profit > 0 ? '+' : ''}{aiPerformance.total_profit?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="p-4 bg-[#121212] rounded-lg">
                      <div className="text-xs text-[#A1A1AA] mb-1">Avg Profit/Trade</div>
                      <div className={`text-3xl font-data font-bold ${aiPerformance.avg_profit_per_trade > 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                        {aiPerformance.avg_profit_per_trade > 0 ? '+' : ''}{aiPerformance.avg_profit_per_trade?.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* POSITIONS TAB */}
        <TabsContent value="positions" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-3">
                <Activity className="text-[#007AFF]" />
                Open Positions ({openPositions.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {openPositions.length === 0 ? (
                <div className="text-center py-8">
                  <Target size={48} className="mx-auto mb-4 text-[#007AFF] opacity-50" />
                  <p className="text-[#A1A1AA]">No open positions</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {openPositions.map((pos, i) => (
                    <div key={i} className="p-4 bg-[#121212] rounded-lg border border-[#1F1F1F]">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-xl font-bold text-white">{pos.symbol}</span>
                          <Badge className="bg-[#007AFF]/20 text-[#007AFF]">
                            {pos.mode?.toUpperCase()}
                          </Badge>
                        </div>
                        <Badge className="bg-[#00FF94]/20 text-[#00FF94]">
                          Score: {pos.adjusted_score}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <span className="text-[#A1A1AA]">Entry:</span>
                          <span className="ml-2 font-data text-white">${pos.entry_price?.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-[#A1A1AA]">Size:</span>
                          <span className="ml-2 font-data text-white">${pos.position_size_usd?.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-[#A1A1AA]">Stop Loss:</span>
                          <span className="ml-2 font-data text-[#FF0055]">${pos.stop_loss_price?.toFixed(4)}</span>
                        </div>
                        <div>
                          <span className="text-[#A1A1AA]">Take Profit:</span>
                          <span className="ml-2 font-data text-[#00FF94]">${pos.take_profit_price?.toFixed(4)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SETTINGS TAB */}
        <TabsContent value="settings" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-xl font-heading flex items-center gap-3">
                <Shield className="text-[#FFB800]" />
                Risk Profile Settings
              </CardTitle>
              <CardDescription>
                Configure your risk tolerance and trading parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Mode Selection */}
              <div className="flex items-center justify-between p-4 bg-[#121212] rounded-lg">
                <div>
                  <Label className="text-base font-bold text-white">Trading Mode</Label>
                  <p className="text-sm text-[#A1A1AA]">Paper = No real money | Live = Real trades</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleModeChange('paper')}
                    className={riskProfile.mode === 'paper' ? 'bg-[#007AFF]' : 'bg-[#1F1F1F]'}
                  >
                    Paper
                  </Button>
                  <Button
                    onClick={() => handleModeChange('live')}
                    className={riskProfile.mode === 'live' ? 'bg-[#FF0055]' : 'bg-[#1F1F1F]'}
                  >
                    Live
                  </Button>
                </div>
              </div>

              {/* Parameters */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label className="text-[#A1A1AA]">Minimum Score to Trade</Label>
                  <div className="flex items-center gap-4 mt-2">
                    <Slider
                      value={[riskProfile.min_score]}
                      onValueChange={([v]) => setRiskProfile(p => ({...p, min_score: v}))}
                      min={40}
                      max={90}
                      step={5}
                      className="flex-1"
                    />
                    <span className="font-data text-white w-12">{riskProfile.min_score}</span>
                  </div>
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Max Position Size (USD)</Label>
                  <Input
                    type="number"
                    value={riskProfile.max_position_size_usd}
                    onChange={(e) => setRiskProfile(p => ({...p, max_position_size_usd: parseFloat(e.target.value)}))}
                    className="bg-[#121212] border-[#1F1F1F] mt-2"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Max Daily Trades</Label>
                  <Input
                    type="number"
                    value={riskProfile.max_daily_trades}
                    onChange={(e) => setRiskProfile(p => ({...p, max_daily_trades: parseInt(e.target.value)}))}
                    className="bg-[#121212] border-[#1F1F1F] mt-2"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Max Open Positions</Label>
                  <Input
                    type="number"
                    value={riskProfile.max_open_positions}
                    onChange={(e) => setRiskProfile(p => ({...p, max_open_positions: parseInt(e.target.value)}))}
                    className="bg-[#121212] border-[#1F1F1F] mt-2"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Stop Loss (%)</Label>
                  <div className="flex items-center gap-4 mt-2">
                    <Slider
                      value={[riskProfile.stop_loss_pct]}
                      onValueChange={([v]) => setRiskProfile(p => ({...p, stop_loss_pct: v}))}
                      min={5}
                      max={30}
                      step={1}
                      className="flex-1"
                    />
                    <span className="font-data text-[#FF0055] w-12">{riskProfile.stop_loss_pct}%</span>
                  </div>
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Take Profit (%)</Label>
                  <div className="flex items-center gap-4 mt-2">
                    <Slider
                      value={[riskProfile.take_profit_pct]}
                      onValueChange={([v]) => setRiskProfile(p => ({...p, take_profit_pct: v}))}
                      min={10}
                      max={100}
                      step={5}
                      className="flex-1"
                    />
                    <span className="font-data text-[#00FF94] w-12">{riskProfile.take_profit_pct}%</span>
                  </div>
                </div>
              </div>

              <Button
                onClick={saveRiskProfile}
                className="w-full bg-[#00FF94] hover:bg-[#00CC76] text-black font-bold rounded-full"
              >
                <Shield size={16} className="mr-2" />
                Save Risk Profile
              </Button>

              {/* Warning */}
              {riskProfile.mode === 'live' && (
                <div className="bg-[#FF0055]/10 border border-[#FF0055]/30 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="text-[#FF0055] flex-shrink-0" size={20} />
                    <div className="text-sm text-[#FF0055]">
                      <p className="font-bold mb-1">LIVE MODE WARNING</p>
                      <p>Real money will be used for trades. Only trade what you can afford to lose.</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AutoExecution;
