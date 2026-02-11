import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Progress } from '@/components/ui/progress';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import {
  Play, History, TrendingUp, TrendingDown, DollarSign, Percent,
  Target, Calendar, RefreshCw, BarChart3, Zap, Clock, Award,
  AlertTriangle, Trash2, Copy, CheckCircle, XCircle
} from 'lucide-react';
import api from '../services/api';
import toast from '../utils/toast';
import TradingPairSelector from '../components/TradingPairSelector';

const BacktestEngine = ({ embedded = false }) => {
  const [strategies, setStrategies] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [history, setHistory] = useState([]);
  const [currentBacktest, setCurrentBacktest] = useState(null);
  const [runningBacktest, setRunningBacktest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('new');
  
  // Form state
  const [config, setConfig] = useState({
    name: 'My Backtest',
    strategy_type: 'momentum',
    symbols: ['BTC/USD'],
    start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    initial_capital: 10000,
    position_size_pct: 10,
    max_positions: 5,
    stop_loss_pct: 5,
    take_profit_pct: 15,
    commission_pct: 0.1,
    slippage_pct: 0.05,
    strategy_params: {}
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Add timeout wrapper to prevent infinite loading
      const fetchWithTimeout = async (url, timeout = 8000) => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        try {
          const response = await api.get(url, { signal: controller.signal });
          clearTimeout(timeoutId);
          return response;
        } catch (error) {
          clearTimeout(timeoutId);
          if (error.name === 'AbortError' || error.name === 'CanceledError') {
            console.warn(`Request to ${url} timed out`);
          }
          return { data: {} };
        }
      };
      
      const [strategiesRes, templatesRes, historyRes] = await Promise.all([
        fetchWithTimeout('/backtest-engine/strategies'),
        fetchWithTimeout('/backtest-engine/templates'),
        fetchWithTimeout('/backtest-engine/history')
      ]);

      setStrategies(strategiesRes.data.strategies || []);
      setTemplates(templatesRes.data.templates || []);
      setHistory(historyRes.data.history || []);
    } catch (error) {
      console.error('Error loading backtest data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll for running backtest status
  useEffect(() => {
    if (!runningBacktest) return;

    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/backtest-engine/status/${runningBacktest}`);
        if (res.data.status === 'completed') {
          clearInterval(interval);
          const resultRes = await api.get(`/backtest-engine/results/${runningBacktest}`);
          setCurrentBacktest(resultRes.data);
          setRunningBacktest(null);
          setActiveTab('results');
          toast.success('Backtest completed!');
          loadData();
        } else if (res.data.status === 'failed') {
          clearInterval(interval);
          setRunningBacktest(null);
          toast.error('Backtest failed');
        }
      } catch (error) {
        console.error('Error polling backtest:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [runningBacktest, loadData]);

  const handleRunBacktest = async () => {
    const loadingToast = toast.loading('Starting backtest...');
    try {
      const res = await api.post('/backtest-engine/run', config);
      toast.dismiss(loadingToast);
      toast.info('Backtest started', {
        description: 'Running in background...'
      });
      setRunningBacktest(res.data.backtest_id);
    } catch (error) {
      toast.dismiss(loadingToast);
      toast.error('Failed to start backtest');
    }
  };

  const handleApplyTemplate = (template) => {
    setConfig({
      ...config,
      ...template.config,
      start_date: config.start_date,
      end_date: config.end_date
    });
    toast.info(`Applied "${template.name}" template`);
  };

  const handleViewResult = async (backtestId) => {
    try {
      const res = await api.get(`/backtest-engine/results/${backtestId}`);
      setCurrentBacktest(res.data);
      setActiveTab('results');
    } catch (error) {
      toast.error('Failed to load backtest results');
    }
  };

  const handleDeleteBacktest = async (backtestId) => {
    if (!window.confirm('Delete this backtest?')) return;
    try {
      await api.delete(`/backtest-engine/${backtestId}`);
      toast.success('Backtest deleted');
      loadData();
    } catch (error) {
      toast.error('Failed to delete backtest');
    }
  };

  const selectedStrategy = strategies.find(s => s.id === config.strategy_type);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-[#007AFF] mx-auto mb-4" />
          <p className="text-[#A1A1AA]">Loading Backtest Engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 space-y-6" data-testid="backtest-engine-page">
      {/* Header */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl lg:text-4xl font-heading font-black tracking-tight mb-2 flex items-center gap-3">
            <BarChart3 size={40} className="text-[#007AFF]" />
            <span className="text-[#007AFF]">Backtest</span> Engine
          </h1>
          <p className="text-[#A1A1AA]">
            Test your trading strategies on historical data
          </p>
        </div>
        <Button onClick={loadData} variant="outline" className="border-[#1F1F1F]">
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </Button>
      </motion.div>

      {/* Running Backtest Banner */}
      {runningBacktest && (
        <Card className="bg-[#007AFF]/10 border-[#007AFF]/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-[#007AFF] border-t-transparent" />
              <div className="flex-1">
                <p className="font-bold text-white">Backtest Running...</p>
                <p className="text-sm text-[#A1A1AA]">ID: {runningBacktest}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-[#121212] border border-[#1F1F1F]">
          <TabsTrigger value="new" className="data-[state=active]:bg-[#007AFF] data-[state=active]:text-white">
            <Play size={16} className="mr-2" />
            New Backtest
          </TabsTrigger>
          <TabsTrigger value="results" className="data-[state=active]:bg-[#007AFF] data-[state=active]:text-white" disabled={!currentBacktest}>
            <TrendingUp size={16} className="mr-2" />
            Results
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-[#007AFF] data-[state=active]:text-white">
            <History size={16} className="mr-2" />
            History ({history.length})
          </TabsTrigger>
        </TabsList>

        {/* New Backtest Tab */}
        <TabsContent value="new" className="space-y-4">
          {/* Templates */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="text-[#FFB800]" size={20} />
                Quick Templates
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {templates.map((template, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    className="border-[#1F1F1F] hover:border-[#007AFF]"
                    onClick={() => handleApplyTemplate(template)}
                  >
                    <Copy size={14} className="mr-2" />
                    {template.name}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Configuration */}
          <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
            <CardHeader>
              <CardTitle>Backtest Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <Label className="text-[#A1A1AA]">Backtest Name</Label>
                  <Input
                    value={config.name}
                    onChange={(e) => setConfig({ ...config, name: e.target.value })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Strategy</Label>
                  <Select value={config.strategy_type} onValueChange={(v) => setConfig({ ...config, strategy_type: v })}>
                    <SelectTrigger className="bg-[#121212] border-[#1F1F1F] mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#121212] border-[#1F1F1F]">
                      {strategies.map((s) => (
                        <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Symbol</Label>
                  <TradingPairSelector 
                    value={config.symbols[0]} 
                    onValueChange={(v) => setConfig({ ...config, symbols: [v] })}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Start Date</Label>
                  <Input
                    type="date"
                    value={config.start_date}
                    onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">End Date</Label>
                  <Input
                    type="date"
                    value={config.end_date}
                    onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Initial Capital ($)</Label>
                  <Input
                    type="number"
                    value={config.initial_capital}
                    onChange={(e) => setConfig({ ...config, initial_capital: parseFloat(e.target.value) })}
                    className="bg-[#121212] border-[#1F1F1F] mt-1"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Position Size: {config.position_size_pct}%</Label>
                  <Slider
                    value={[config.position_size_pct]}
                    onValueChange={([v]) => setConfig({ ...config, position_size_pct: v })}
                    min={5}
                    max={50}
                    step={5}
                    className="mt-3"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Stop Loss: {config.stop_loss_pct}%</Label>
                  <Slider
                    value={[config.stop_loss_pct]}
                    onValueChange={([v]) => setConfig({ ...config, stop_loss_pct: v })}
                    min={1}
                    max={20}
                    step={1}
                    className="mt-3"
                  />
                </div>

                <div>
                  <Label className="text-[#A1A1AA]">Take Profit: {config.take_profit_pct}%</Label>
                  <Slider
                    value={[config.take_profit_pct]}
                    onValueChange={([v]) => setConfig({ ...config, take_profit_pct: v })}
                    min={5}
                    max={50}
                    step={5}
                    className="mt-3"
                  />
                </div>
              </div>

              {/* Strategy description */}
              {selectedStrategy && (
                <div className="p-4 bg-[#007AFF]/10 border border-[#007AFF]/30 rounded-lg">
                  <h4 className="font-bold text-[#007AFF] mb-1">{selectedStrategy.name}</h4>
                  <p className="text-sm text-[#A1A1AA]">{selectedStrategy.description}</p>
                </div>
              )}

              <Button 
                onClick={handleRunBacktest} 
                className="w-full bg-[#007AFF] hover:bg-[#007AFF]/80"
                disabled={!!runningBacktest}
              >
                <Play size={16} className="mr-2" />
                Run Backtest
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          {currentBacktest && (
            <>
              {/* Metrics Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <DollarSign size={16} className="text-[#00FF94]" />
                      <span className="text-sm text-[#A1A1AA]">Total Return</span>
                    </div>
                    <div className={`text-2xl font-data font-bold ${currentBacktest.metrics?.total_return_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                      {currentBacktest.metrics?.total_return_pct >= 0 ? '+' : ''}{currentBacktest.metrics?.total_return_pct}%
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Target size={16} className="text-[#007AFF]" />
                      <span className="text-sm text-[#A1A1AA]">Win Rate</span>
                    </div>
                    <div className="text-2xl font-data font-bold text-white">
                      {currentBacktest.metrics?.win_rate}%
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingDown size={16} className="text-[#FF0055]" />
                      <span className="text-sm text-[#A1A1AA]">Max Drawdown</span>
                    </div>
                    <div className="text-2xl font-data font-bold text-[#FF0055]">
                      -{currentBacktest.metrics?.max_drawdown_pct}%
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Award size={16} className="text-[#FFB800]" />
                      <span className="text-sm text-[#A1A1AA]">Sharpe Ratio</span>
                    </div>
                    <div className="text-2xl font-data font-bold text-white">
                      {currentBacktest.metrics?.sharpe_ratio}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Equity Curve */}
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader>
                  <CardTitle>Equity Curve</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={currentBacktest.equity_curve?.slice(-100)}>
                        <defs>
                          <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#007AFF" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#007AFF" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1F1F1F" />
                        <XAxis dataKey="date" tick={{ fill: '#666' }} tickFormatter={(v) => v?.slice(5, 10)} />
                        <YAxis tick={{ fill: '#666' }} tickFormatter={(v) => `$${v}`} />
                        <Tooltip 
                          contentStyle={{ background: '#121212', border: '1px solid #1F1F1F' }}
                          formatter={(value) => [`$${value}`, 'Equity']}
                        />
                        <Area type="monotone" dataKey="equity" stroke="#007AFF" fill="url(#equityGradient)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Trade List */}
              <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
                <CardHeader>
                  <CardTitle>Trade History ({currentBacktest.trades?.length || 0} trades)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-80 overflow-y-auto space-y-2">
                    {currentBacktest.trades?.slice(0, 20).map((trade, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-[#121212] rounded">
                        <div className="flex items-center gap-3">
                          {trade.pnl >= 0 ? (
                            <CheckCircle size={16} className="text-[#00FF94]" />
                          ) : (
                            <XCircle size={16} className="text-[#FF0055]" />
                          )}
                          <span className="text-white">{trade.symbol}</span>
                          <Badge variant="outline" className="text-xs border-[#1F1F1F]">{trade.type}</Badge>
                        </div>
                        <span className={`font-data ${trade.pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {history.length === 0 ? (
            <Card className="bg-[#0A0A0A] border-[#1F1F1F]">
              <CardContent className="py-12 text-center">
                <History size={48} className="mx-auto mb-4 text-[#007AFF] opacity-50" />
                <p className="text-[#A1A1AA]">No backtest history yet</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {history.map((bt) => (
                <Card key={bt.backtest_id} className="bg-[#0A0A0A] border-[#1F1F1F] hover:border-[#007AFF]/50 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div>
                          <h3 className="font-bold text-white">{bt.config?.name || 'Unnamed'}</h3>
                          <p className="text-sm text-[#A1A1AA]">
                            {bt.config?.strategy_type} • {bt.created_at?.slice(0, 10)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        {bt.metrics && (
                          <div className="text-right">
                            <p className={`font-data font-bold ${bt.metrics.total_return_pct >= 0 ? 'text-[#00FF94]' : 'text-[#FF0055]'}`}>
                              {bt.metrics.total_return_pct >= 0 ? '+' : ''}{bt.metrics.total_return_pct}%
                            </p>
                            <p className="text-xs text-[#666]">Win: {bt.metrics.win_rate}%</p>
                          </div>
                        )}
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleViewResult(bt.backtest_id)}
                            size="sm"
                            className="bg-[#007AFF]"
                          >
                            View
                          </Button>
                          <Button
                            onClick={() => handleDeleteBacktest(bt.backtest_id)}
                            size="sm"
                            variant="ghost"
                            className="text-[#FF0055]"
                          >
                            <Trash2 size={14} />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BacktestEngine;
